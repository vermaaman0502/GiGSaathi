"""Earnings domain logic. All money arithmetic is deterministic - the LLM never computes figures."""
import csv
import io
from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional

from .. import store
from ..messages import m
from ..tools import money

TOL = 1.0   # rupees: ignore rounding noise when flagging discrepancies


def platform_total(s: Dict) -> float:
    """What the platform's own figures add up to: gross + incentive - commission - deductions."""
    return s["gross"] + s["incentive"] - s["commission"] - s["deductions"]


def take_home(s: Dict) -> float:
    """After the worker's own costs (fuel + other)."""
    return platform_total(s) - s["fuel"] - s["other_expenses"]


def discrepancy(s: Dict) -> Dict:
    """Possible payment discrepancy. Never labelled as fraud."""
    expected = platform_total(s)
    out = {"expected_payout": round(expected, 2), "received": s.get("received"), "promised": s.get("promised"),
           "shortfall_vs_calculated": None, "shortfall_vs_promised": None, "status": "unknown"}
    if s.get("received") is None:
        return out
    sc = expected - s["received"]
    out["shortfall_vs_calculated"] = round(sc, 2)
    if s.get("promised") is not None:
        out["shortfall_vs_promised"] = round(s["promised"] - s["received"], 2)
    short = max(sc, out["shortfall_vs_promised"] or 0)
    out["status"] = "possible_discrepancy" if short > TOL else "matches"
    return out


def add_shift(user: str, d: Dict, is_demo: bool = False) -> int:
    return store.x(
        "INSERT INTO shifts(user,day,platform,hours,start_hour,gross,commission,deductions,incentive,fuel,other_expenses,promised,received,source,is_demo,note)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (user, d.get("day") or date.today().isoformat(), (d.get("platform") or "other").strip().lower(), d.get("hours", 0), d.get("start_hour"),
         d.get("gross", 0), d.get("commission", 0), d.get("deductions", 0), d.get("incentive", 0), d.get("fuel", 0), d.get("other_expenses", 0),
         d.get("promised"), d.get("received"), d.get("source", "manual"), int(is_demo), d.get("note", "")))


def shifts(user: str, days: Optional[int] = None) -> List[Dict]:
    sql, args = "SELECT * FROM shifts WHERE user=?", [user]
    if days:
        sql += " AND day>=?"
        args.append((date.today() - timedelta(days=days - 1)).isoformat())
    rows = store.q(sql + " ORDER BY day DESC, id DESC", args)
    for r in rows:
        r["take_home"] = round(take_home(r), 2)
        r["discrepancy"] = discrepancy(r)
    return rows


def data_source(user: str) -> str:
    if user.startswith("demo-"):
        return "demo"
    return "user" if store.q("SELECT 1 FROM shifts WHERE user=? LIMIT 1", (user,)) else "empty"


def _agg(rows: List[Dict]) -> Dict:
    gross = sum(r["gross"] + r["incentive"] for r in rows)
    exp = sum(r["commission"] + r["deductions"] + r["fuel"] + r["other_expenses"] for r in rows)
    hours = sum(r["hours"] for r in rows)
    net = gross - exp
    return {"gross": round(gross, 2), "expenses": round(exp, 2), "net": round(net, 2), "hours": round(hours, 2),
            "net_per_hour": round(net / hours, 2) if hours > 0 else None}


def dashboard(user: str, lang: str = "en", today: Optional[date] = None) -> Dict:
    today = today or date.today()
    rows = shifts(user, 14)
    t_rows = [r for r in rows if r["day"] == today.isoformat()]
    t = _agg(t_rows)
    series = []
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        a = _agg([r for r in rows if r["day"] == d])
        series.append({"day": d, "gross": a["gross"], "expenses": a["expenses"], "net": a["net"]})
    week = _agg([r for r in rows if r["day"] >= (today - timedelta(days=6)).isoformat()])
    summary = (m(lang, "summary_today", gross=round(t["gross"]), exp=round(t["expenses"]), net=round(t["net"]), hours=t["hours"], ph=round(t["net_per_hour"] or 0))
               if t_rows else m(lang, "summary_empty"))
    # pending items
    pend = []
    for r in store.q("SELECT scheme_id,status,reminder FROM tracker WHERE user=? AND status NOT IN ('received','rejected')", (user,)):
        pend.append({"type": "scheme", "id": r["scheme_id"], "status": r["status"], "due": r["reminder"]})
    for r in store.vault_list(user):
        days_left = (date.fromisoformat(r["expiry"]) - today).days
        if days_left <= 30:
            pend.append({"type": "document_expiry", "id": r["doc_type"], "due": r["expiry"], "days_left": days_left})
    for g in store.q("SELECT id,company,status,submitted_on FROM grievances WHERE user=? AND status IN ('draft','ready','submitted')", (user,)):
        item = {"type": "grievance", "id": g["id"], "company": g["company"], "status": g["status"]}
        if g["status"] == "submitted" and g["submitted_on"]:
            item["follow_up_on"] = (date.fromisoformat(g["submitted_on"]) + timedelta(days=7)).isoformat()
        pend.append(item)
    return {"data_source": data_source(user), "today": t, "week": week, "series": series, "ai_summary": summary,
            "summary_basis": "computed from saved shifts" if t_rows else "no data", "pending": pend}


def compare_platforms(user: str, days: int = 30) -> Dict:
    by = defaultdict(list)
    for r in shifts(user, days):
        by[r["platform"]].append(r)
    rows = []
    for p, rs in by.items():
        a = _agg(rs)
        rows.append({"platform": p, "shifts": len(rs), **a})
    rows.sort(key=lambda r: (r["net_per_hour"] is None, -(r["net_per_hour"] or 0)))
    return {"platforms": rows, "enough_data": len(rows) >= 2,
            "note": "Computed only from shifts you entered. GigSaathi has no live connection to any platform."}


def history_stats(user: str) -> Optional[Dict]:
    rs = [r for r in shifts(user, 60) if r["hours"] > 0]
    if not rs:
        return None
    a = _agg(rs)
    return {"avg_net_per_hour": a["net_per_hour"], "shifts": len(rs)}


def band_stats(user: str, band: int = 3) -> Dict:
    """Net per hour by start-hour band, from the worker's own shifts. Range shown only with enough data."""
    rs = [r for r in shifts(user, 90) if r["hours"] > 0 and r["start_hour"] is not None]
    bands = defaultdict(list)
    for r in rs:
        bands[(r["start_hour"] // band) * band].append(r["take_home"] / r["hours"])
    out = []
    for start, vals in sorted(bands.items()):
        out.append({"start": start, "end": start + band, "n": len(vals), "avg": round(sum(vals) / len(vals), 2),
                    "min": round(min(vals), 2), "max": round(max(vals), 2), "show_range": len(vals) >= 3})
    return {"total_shifts": len(rs), "enough_data": len(rs) >= 5, "bands": out}


def leaks(user: str) -> List[Dict]:
    ex = [{"category": r["category"] or "other", "amount": r["amount"]} for r in store.entries(user, "expense")]
    out = []
    for lk in money.find_leaks(ex):
        out.append({**lk, "why": f"{lk['times']} small expenses of the same kind added up to Rs {lk['total']:.0f}.",
                    "validate": "Look at your last 2 weeks of these purchases and check which were needed."})
    return out


# ---- wage diary (daily-wage workers) ----
def diary_add(user: str, d: Dict, is_demo: bool = False) -> int:
    return store.x("INSERT INTO wage_diary(user,day,employer,work,hours,promised,received,is_demo) VALUES (?,?,?,?,?,?,?,?)",
                   (user, d.get("day") or date.today().isoformat(), d.get("employer", ""), d.get("work", ""), d.get("hours", 0),
                    d.get("promised", 0), d.get("received", 0), int(is_demo)))


def diary_list(user: str) -> Dict:
    rows = store.q("SELECT * FROM wage_diary WHERE user=? ORDER BY day DESC, id DESC", (user,))
    due = round(sum(r["promised"] - r["received"] for r in rows), 2)
    return {"entries": rows, "promised_total": round(sum(r["promised"] for r in rows), 2),
            "received_total": round(sum(r["received"] for r in rows), 2), "unpaid_total": due}


def export_csv(user: str) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["type", "date", "platform_or_employer", "hours", "gross_or_promised", "commission", "deductions", "incentive", "fuel", "other_expenses", "received", "possible_shortfall", "source"])
    for r in reversed(shifts(user)):
        w.writerow(["shift", r["day"], r["platform"], r["hours"], r["gross"], r["commission"], r["deductions"], r["incentive"], r["fuel"],
                    r["other_expenses"], r["received"] if r["received"] is not None else "", r["discrepancy"]["shortfall_vs_calculated"] or "", r["source"]])
    for r in reversed(store.q("SELECT * FROM wage_diary WHERE user=? ORDER BY day", (user,))):
        w.writerow(["wage_diary", r["day"], r["employer"], r["hours"], r["promised"], "", "", "", "", "", r["received"], max(r["promised"] - r["received"], 0), "manual"])
    return buf.getvalue()
