"""Proof-to-Action: payout record -> validate -> deterministic discrepancy -> plain explanation ->
evidence bundle -> optional grievance draft -> next step -> outcome tracking."""
from typing import Dict, Optional

from ..messages import m
from . import earn, ledger


def run(user: str, record: Dict, lang: str = "en", create_grievance: bool = False, name: str = "", company: str = "",
        is_demo: bool = False, save: bool = True) -> Dict:
    # 1-2. accept + validate (numeric, non-negative, hours present)
    rec = {k: record.get(k) for k in ["day", "platform", "hours", "start_hour", "gross", "commission", "deductions", "incentive", "fuel", "other_expenses", "promised", "received", "source", "note"]}
    for k in ["hours", "gross", "commission", "deductions", "incentive", "fuel", "other_expenses"]:
        rec[k] = float(rec[k] or 0)
        if rec[k] < 0:
            raise ValueError(f"{k} cannot be negative")
    for k in ["promised", "received"]:
        rec[k] = None if rec[k] in (None, "") else float(rec[k])
    rec["platform"] = (rec["platform"] or "other").strip().lower()
    rec["source"] = rec["source"] or "manual"

    # 3. deterministic calculation
    disc = earn.discrepancy(rec)
    short = max(disc["shortfall_vs_calculated"] or 0, disc["shortfall_vs_promised"] or 0)

    # 4. plain-language explanation (typed code + sentence)
    if disc["status"] == "unknown":
        code, msg = "insufficient_data", m(lang, "p2a_unknown")
    elif disc["status"] == "possible_discrepancy":
        code = "possible_discrepancy"
        msg = m(lang, "p2a_short", amt=round(short))
        if disc["shortfall_vs_promised"] and disc["shortfall_vs_promised"] > earn.TOL:
            msg += " " + m(lang, "p2a_promised", amt=round(disc["shortfall_vs_promised"]), promised=round(rec["promised"]))
    else:
        code, msg = "no_discrepancy", m(lang, "p2a_none")

    result = {"validated_record": rec, "calculation": {"platform_total": round(earn.platform_total(rec), 2), "take_home": round(earn.take_home(rec), 2), **disc},
              "explanation": {"code": code, "shortfall": round(short, 2) if code == "possible_discrepancy" else 0, "message": msg,
                              "disclaimer": "This is a possible discrepancy based on the numbers you entered or confirmed. It is not proof of wrongdoing."},
              "shift_id": None, "evidence": [], "grievance": None, "next_step": None, "tracking": None}

    # 5. organise evidence
    if save:
        result["shift_id"] = earn.add_shift(user, rec, is_demo)
        ev_title = f"Payout {rec['day'] or ''} {rec['platform']}".strip()
        ledger.evidence_add(user, "payout", ev_title, {"record": rec, "calculation": result["calculation"]}, is_demo)
    result["evidence"] = [
        {"label": "Payout record", "detail": f"{rec['platform']} {rec['day'] or ''}: gross Rs {rec['gross']:.0f}, incentive Rs {rec['incentive']:.0f}, commission Rs {rec['commission']:.0f}, deductions Rs {rec['deductions']:.0f}"},
        {"label": "Amount received", "detail": "not entered" if rec["received"] is None else f"Rs {rec['received']:.0f}"},
        {"label": "Calculation", "detail": f"Figures add up to Rs {disc['expected_payout']:.0f}"},
    ]

    # 6-7. optional grievance draft + next step (drafting is separate from submitting)
    if code == "possible_discrepancy":
        result["next_step"] = {"message": m(lang, "p2a_next"), "ladder_step": "platform_support"}
        if create_grievance:
            if not (name and company):
                raise ValueError("name and company are required to draft a complaint")
            ev = [e["detail"] for e in result["evidence"]]
            g = ledger.grievance_create(user, "deduction", name, company, {"amount": round(short), "incident_date": rec["day"],
                                        "details": f"The payout received is Rs {round(short)} lower than the platform's own figures add up to."}, lang, ev, is_demo)
            result["grievance"] = {"id": g["id"], "status": g["status"], "letter": g["letter"], "letter_local": g["letter_local"], "escalation": g["escalation"]}
        if save:
            ledger.impact_add(user, "extra_payment", round(short), "estimated", f"possible shortfall {rec['day'] or ''} {rec['platform']}", is_demo)
    # 8. outcome tracking is recorded later via PATCH /api/grievances/{id} and POST /api/impact
    result["tracking"] = {"how": "Record the outcome in Impact Ledger (user-reported) once the platform replies."}
    return result
