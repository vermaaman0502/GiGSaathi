"""Grievance drafter + escalation ladder. Template-based so it works without an LLM;
the LLM (if configured) only polishes tone/translation."""
from datetime import date
from typing import Dict, List, Optional

LADDER = [
    {"step": 1, "to": "Platform support / in-app ticket", "note": "Keep the ticket number and screenshots."},
    {"step": 2, "to": "Platform Grievance Officer", "note": "Platforms must publish the officer's contact (IT Rules 2021 / Consumer Protection E-Commerce Rules)."},
    {"step": 3, "to": "State Labour Department / Labour Commissioner", "note": "For unpaid wages or unfair termination. Visit the nearest labour office or CSC."},
    {"step": 4, "to": "Consumer forum (e-Daakhil)", "note": "Where the dispute is about a service/payment as a consumer."},
    {"step": 5, "to": "Free legal aid - NALSA helpline 15100 / District Legal Services Authority", "note": "Free for eligible workers."},
]

KINDS = {"deactivation", "wage_due", "deduction", "general"}

_SUBJECT = {
    "deactivation": "Appeal against ID deactivation",
    "wage_due": "Notice for payment of unpaid wages",
    "deduction": "Complaint about unexplained deductions",
    "general": "Complaint",
}

_BODY = {
    "deactivation": "My partner ID was deactivated on {incident_date}. I request a written reason and a review of this decision, and reactivation of my ID. I have worked with {company} and request that my record and the evidence below be considered.",
    "wage_due": "I worked for you and Rs {amount:.0f} remains unpaid for work done up to {incident_date}. I request payment within 7 days of this letter. Otherwise I will approach the Labour Department.",
    "deduction": "My payout dated {incident_date} shows deductions of Rs {amount:.0f} that I do not understand. I request an itemised breakdown and a refund of any amount deducted without a valid reason.",
    "general": "I am writing about the following issue that occurred on {incident_date}: {details}",
}


def draft(
    kind: str,
    name: str,
    company: str,
    details: str = "",
    amount: float = 0.0,
    incident_date: Optional[str] = None,
    evidence: Optional[List[str]] = None,
) -> Dict:
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {sorted(KINDS)}")
    incident_date = incident_date or date.today().isoformat()
    evidence = evidence or []
    body = _BODY[kind].format(company=company, amount=amount, incident_date=incident_date, details=details or "(please see evidence)")
    if details and kind != "general":
        body += f"\n\nDetails: {details}"
    ev = "\n".join(f"  {i}. {e}" for i, e in enumerate(evidence, 1)) or "  (none attached)"
    letter = (
        f"To,\nThe Grievance Officer,\n{company}\n\n"
        f"Date: {date.today().isoformat()}\n"
        f"Subject: {_SUBJECT[kind]}\n\n"
        f"Respectfully,\n\n{body}\n\n"
        f"Evidence attached:\n{ev}\n\n"
        f"I request a reply within 15 days. Thank you for your attention.\n\n"
        f"Sincerely,\n{name}"
    )
    return {"kind": kind, "letter": letter, "ladder": LADDER, "follow_up_days": [7, 15, 30]}
