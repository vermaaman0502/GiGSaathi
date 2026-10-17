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


_HI_SUBJECT = {
    "deactivation": "आईडी बंद किए जाने के विरुद्ध अपील",
    "wage_due": "बकाया मज़दूरी के भुगतान की सूचना",
    "deduction": "अनजानी कटौती की शिकायत",
    "general": "शिकायत",
}
_HI_BODY = {
    "deactivation": "मेरी पार्टनर आईडी {incident_date} को बंद कर दी गई। मेरा अनुरोध है कि इसका लिखित कारण बताया जाए, निर्णय की समीक्षा हो और मेरी आईडी फिर से चालू की जाए। मैंने {company} के साथ काम किया है। कृपया नीचे दिए सबूतों पर विचार करें।",
    "wage_due": "मैंने आपके यहाँ काम किया और {incident_date} तक के काम के ₹{amount:.0f} बकाया हैं। अनुरोध है कि इस पत्र के 7 दिन के भीतर भुगतान करें, अन्यथा मैं श्रम विभाग से संपर्क करूँगा/करूँगी।",
    "deduction": "{incident_date} के मेरे भुगतान में ₹{amount:.0f} की कटौती दिख रही है जो मुझे समझ नहीं आई। कृपया पूरा ब्योरा दें और बिना उचित कारण काटी गई रकम लौटाएँ।",
    "general": "मैं {incident_date} को हुई निम्न समस्या के बारे में लिख रहा/रही हूँ: {details}",
}


def draft(
    kind: str,
    name: str,
    company: str,
    details: str = "",
    amount: float = 0.0,
    incident_date: Optional[str] = None,
    evidence: Optional[List[str]] = None,
    lang: str = "en",
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
    out = {"kind": kind, "letter": letter, "ladder": LADDER, "follow_up_days": [7, 15, 30]}
    if lang == "hi":
        hbody = _HI_BODY[kind].format(company=company, amount=amount, incident_date=incident_date, details=details or "(कृपया सबूत देखें)")
        if details and kind != "general":
            hbody += f"\n\nविवरण: {details}"
        hev = "\n".join(f"  {i}. {e}" for i, e in enumerate(evidence, 1)) or "  (कोई नहीं)"
        out["letter_local"] = (
            f"सेवा में,\nशिकायत अधिकारी,\n{company}\n\nदिनांक: {date.today().isoformat()}\n"
            f"विषय: {_HI_SUBJECT[kind]}\n\nमहोदय/महोदया,\n\n{hbody}\n\nसंलग्न सबूत:\n{hev}\n\n"
            f"कृपया 15 दिन के भीतर उत्तर दें। धन्यवाद।\n\nभवदीय,\n{name}"
        )
    return out
