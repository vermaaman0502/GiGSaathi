"""Worker Impact Ledger, welfare tracker, grievance records and evidence. Outcomes are always
labelled by basis: 'estimated' (our calculation), 'user_reported' (the worker confirmed it), and
'verified' (independent confirmation - reserved for future integrations; cannot be created via the API)."""
import json
from datetime import date, timedelta
from typing import Dict, List, Optional

from .. import schemes, store
from ..tools import grievance as griev

IMPACT_KINDS = {
    "extra_payment": "money", "benefit_received": "money", "expense_avoided": "money",
    "scheme_discovered": "count", "application_started": "count", "complaint_submitted": "count",
    "complaint_resolved": "count", "document_completed": "count",
}
USER_BASES = {"estimated", "user_reported"}          # 'verified' is deliberately not accepted from clients
TRACKER_STATUS = ["saved", "documents_ready", "applied", "received", "rejected"]   # 'applied'/'received' are user-recorded
GRIEVANCE_STATUS = ["draft", "ready", "submitted", "resolved"]


# ---------------- impact ----------------
def impact_add(user: str, kind: str, amount: float, basis: str, note: str = "", is_demo: bool = False) -> int:
    if kind not in IMPACT_KINDS:
        raise ValueError(f"kind must be one of {sorted(IMPACT_KINDS)}")
    if basis not in USER_BASES:
        raise ValueError("basis must be 'estimated' or 'user_reported'. 'verified' can only come from an integration.")
    if IMPACT_KINDS[kind] == "count":
        amount = 0.0                                  # discovering a scheme / starting an application is never money
    if amount < 0:
        raise ValueError("amount cannot be negative")
    return store.x("INSERT INTO impact(user,day,kind,amount,basis,note,is_demo) VALUES (?,?,?,?,?,?,?)",
                   (user, date.today().isoformat(), kind, amount, basis, note[:200], int(is_demo)))


def impact_summary(user: str) -> Dict:
    rows = store.q("SELECT * FROM impact WHERE user=? ORDER BY id DESC", (user,))
    money_user = sum(r["amount"] for r in rows if IMPACT_KINDS[r["kind"]] == "money" and r["basis"] == "user_reported")
    money_est = sum(r["amount"] for r in rows if IMPACT_KINDS[r["kind"]] == "money" and r["basis"] == "estimated")
    money_ver = sum(r["amount"] for r in rows if IMPACT_KINDS[r["kind"]] == "money" and r["basis"] == "verified")
    counts = {k: sum(1 for r in rows if r["kind"] == k) for k, t in IMPACT_KINDS.items() if t == "count"}
    by_kind = {k: round(sum(r["amount"] for r in rows if r["kind"] == k and r["basis"] == "user_reported"), 2) for k, t in IMPACT_KINDS.items() if t == "money"}
    return {
        "money": {"verified": round(money_ver, 2), "user_reported": round(money_user, 2), "estimated": round(money_est, 2)},
        "money_by_kind_user_reported": by_kind, "counts": counts, "entries": rows,
        "notes": ["Estimated amounts are our calculations and are NOT money received.",
                  "User-reported amounts are what you told us you received or avoided.",
                  "Verified amounts need independent confirmation, which no integration provides yet - so this stays at 0."],
    }


# ---------------- welfare tracker ----------------
def tracker_save(user: str, scheme_id: str, status: Optional[str] = None, reminder: Optional[str] = None,
                 checklist: Optional[Dict] = None, is_demo: bool = False) -> Dict:
    sc = schemes.get(scheme_id)
    if not sc:
        raise KeyError("unknown scheme")
    if status and status not in TRACKER_STATUS:
        raise ValueError(f"status must be one of {TRACKER_STATUS}")
    if reminder:
        date.fromisoformat(reminder)
    cur = store.q("SELECT * FROM tracker WHERE user=? AND scheme_id=?", (user, scheme_id))
    base_check = {d: False for d in sc.get("documents", [])}
    if cur:
        row = cur[0]
        ck = {**json.loads(row["checklist"]), **(checklist or {})}
        store.x("UPDATE tracker SET status=?, reminder=?, checklist=?, updated=? WHERE user=? AND scheme_id=?",
                (status or row["status"], reminder if reminder is not None else row["reminder"], json.dumps(ck), date.today().isoformat(), user, scheme_id))
    else:
        store.x("INSERT INTO tracker(user,scheme_id,status,reminder,checklist,updated,is_demo) VALUES (?,?,?,?,?,?,?)",
                (user, scheme_id, status or "saved", reminder, json.dumps({**base_check, **(checklist or {})}), date.today().isoformat(), int(is_demo)))
        impact_add(user, "scheme_discovered", 0, "user_reported", sc["title"], is_demo)
    if status == "applied":
        impact_add(user, "application_started", 0, "user_reported", sc["title"], is_demo)
    if status == "received":
        pass  # amount is added via the ledger by the worker; we never infer money from a status change
    return tracker_get(user)[scheme_id] if scheme_id in tracker_get(user) else {}


def tracker_get(user: str) -> Dict[str, Dict]:
    out = {}
    for r in store.q("SELECT * FROM tracker WHERE user=? ORDER BY updated DESC", (user,)):
        r["checklist"] = json.loads(r["checklist"])
        r["title"] = (schemes.get(r["scheme_id"]) or {}).get("title", r["scheme_id"])
        r["note"] = "Status is recorded by you. GigSaathi does not submit applications on your behalf."
        out[r["scheme_id"]] = r
    return out


# ---------------- grievances ----------------
ESCALATION = {
    "unpaid_wages": ["contractor_or_employer", "labour_dept", "legal_aid"],
    "deduction": ["platform_support", "grievance_officer", "labour_dept", "consumer_forum"],
    "incentive": ["platform_support", "grievance_officer", "consumer_forum"],
    "deactivation": ["platform_support", "grievance_officer", "labour_dept", "legal_aid"],
    "contractor": ["contractor_or_employer", "labour_dept", "legal_aid"],
}
STEPS = {
    "platform_support": {"to": "Platform support / in-app ticket", "note": "Keep the ticket number and screenshots.", "where": "In the app"},
    "grievance_officer": {"to": "Platform Grievance Officer", "note": "Platforms must publish the officer's contact details (IT Rules / E-Commerce Rules).", "where": "Platform website footer / app help"},
    "contractor_or_employer": {"to": "Contractor / employer (written notice)", "note": "Send a dated written demand; keep a copy.", "where": "Hand delivery or WhatsApp with proof"},
    "labour_dept": {"to": "State Labour Department / Labour Commissioner", "note": "For unpaid or delayed wages and unfair termination.", "where": "District labour office / state labour portal / CSC"},
    "consumer_forum": {"to": "Consumer forum (e-Daakhil)", "note": "Where the dispute is about a service or payment.", "where": "edaakhil.nic.in"},
    "legal_aid": {"to": "Free legal aid - NALSA 15100 / DLSA", "note": "Free for eligible workers.", "where": "Call 15100 or the district DLSA office"},
}
KIND_MAP = {"unpaid_wages": "wage_due", "deduction": "deduction", "incentive": "deduction", "deactivation": "deactivation", "contractor": "wage_due"}


def grievance_create(user: str, issue: str, name: str, company: str, facts: Dict, lang: str = "en", evidence: Optional[List[str]] = None,
                     is_demo: bool = False) -> Dict:
    if issue not in ESCALATION:
        raise ValueError(f"issue must be one of {sorted(ESCALATION)}")
    d = griev.draft(KIND_MAP[issue], name, company, facts.get("details", ""), float(facts.get("amount", 0) or 0), facts.get("incident_date"), evidence or [], lang)
    now = date.today().isoformat()
    tl = [{"day": now, "event": "draft_created"}]
    gid = store.x("INSERT INTO grievances(user,kind,company,facts,letter,letter_local,status,timeline,evidence,created,updated,is_demo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (user, issue, company, json.dumps(facts), d["letter"], d.get("letter_local", ""), "draft", json.dumps(tl), json.dumps(evidence or []), now, now, int(is_demo)))
    return grievance_get(user, gid)


def _row(r: Dict) -> Dict:
    r["facts"] = json.loads(r["facts"])
    r["timeline"] = json.loads(r["timeline"])
    r["evidence"] = json.loads(r["evidence"])
    r["escalation"] = [{**STEPS[k], "id": k} for k in ESCALATION[r["kind"]]]
    r["follow_ups"] = ([(date.fromisoformat(r["submitted_on"]) + timedelta(days=d)).isoformat() for d in (7, 15, 30)] if r["submitted_on"] else [])
    r["note"] = "Status is recorded by you. GigSaathi drafts letters; it does not submit them or guarantee any outcome."
    return r


def grievance_get(user: str, gid: int) -> Optional[Dict]:
    rows = store.q("SELECT * FROM grievances WHERE user=? AND id=?", (user, gid))
    return _row(rows[0]) if rows else None


def grievance_list(user: str) -> List[Dict]:
    return [_row(r) for r in store.q("SELECT * FROM grievances WHERE user=? ORDER BY id DESC", (user,))]


def grievance_update(user: str, gid: int, status: Optional[str] = None, letter: Optional[str] = None,
                     event: Optional[str] = None, evidence: Optional[List[str]] = None) -> Optional[Dict]:
    g = grievance_get(user, gid)
    if not g:
        return None
    if status and status not in GRIEVANCE_STATUS:
        raise ValueError(f"status must be one of {GRIEVANCE_STATUS}")
    today = date.today().isoformat()
    tl = g["timeline"]
    submitted_on = g["submitted_on"]
    if status and status != g["status"]:
        tl.append({"day": today, "event": f"status:{status}"})
        if status == "submitted":
            submitted_on = today
            impact_add(user, "complaint_submitted", 0, "user_reported", g["company"], bool(g["is_demo"]))
        if status == "resolved":
            impact_add(user, "complaint_resolved", 0, "user_reported", g["company"], bool(g["is_demo"]))
    if event:
        tl.append({"day": today, "event": event[:300]})
    store.x("UPDATE grievances SET status=?, letter=?, timeline=?, evidence=?, updated=?, submitted_on=? WHERE user=? AND id=?",
            (status or g["status"], letter if letter is not None else g["letter"], json.dumps(tl), json.dumps(evidence if evidence is not None else g["evidence"]),
             today, submitted_on, user, gid))
    return grievance_get(user, gid)


# ---------------- evidence ----------------
def evidence_add(user: str, kind: str, title: str, data: Dict, is_demo: bool = False) -> int:
    return store.x("INSERT INTO evidence(user,day,kind,title,data,is_demo) VALUES (?,?,?,?,?,?)",
                   (user, date.today().isoformat(), kind, title[:120], json.dumps(data), int(is_demo)))


def evidence_list(user: str) -> List[Dict]:
    rows = store.q("SELECT * FROM evidence WHERE user=? ORDER BY id DESC", (user,))
    for r in rows:
        r["data"] = json.loads(r["data"])
    return rows
