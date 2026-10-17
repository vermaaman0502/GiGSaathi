"""Kagaz Samjho (text version): flag risky clauses in a pasted notice/contract, and document
expiry status for the vault. Photo/OCR input is on the roadmap."""
import re
from datetime import date
from typing import Dict, List, Optional

RISK_PATTERNS = {
    "risk_interest": r"interest|byaj|processing fee|late fee|ब्याज|व्याज|সুদ|வட்டி|వడ్డీ|વ્યાજ|ಬಡ್ಡಿ|പലിശ|ਵਿਆਜ|ସୁଧ|\d+\s*%\s*(per|p\.)?\s*(month|mahine|monthly)",
    "risk_penalty": r"penalt|fine\b|forfeit|jurmana|जुर्माना|दंड|জরিমানা|அபராதம்|జరిమానా|દંડ|ದಂಡ|പിഴ|ਜੁਰਮਾਨਾ|ଜରିମାନା",
    "risk_terminate": r"terminat|without (prior )?notice|deactivat|blacklist|बिना नोटिस|নোটিস ছাড়া",
    "risk_deduct": r"deduct|recover(y|ed)? from|katauti|कटौती|कपात",
    "risk_nonrefund": r"non[- ]?refundable|no refund|not refundable|वापस नहीं",
    "risk_advance": r"advance|security deposit|deposit|joining fee|जमा राशि|अनामत",
}


def scan(text: str) -> List[Dict]:
    """Returns [{key, snippet}] for each risky pattern found (first match's sentence)."""
    found = []
    sentences = re.split(r"(?<=[.!?।\n])\s+", text)
    for key, pat in RISK_PATTERNS.items():
        rx = re.compile(pat, re.I)
        for s in sentences:
            if rx.search(s):
                found.append({"key": key, "snippet": s.strip()[:200]})
                break
    return found


DOC_LABEL_KEY = {"dl": "dt_dl", "rc": "dt_rc", "insurance": "dt_ins", "puc": "dt_puc"}


def expiry_status(expiry_iso: str, today: Optional[date] = None) -> Dict:
    today = today or date.today()
    days = (date.fromisoformat(expiry_iso) - today).days
    key = "vault_expired" if days < 0 else "vault_soon" if days <= 30 else "vault_ok"
    return {"key": key, "days": abs(days) if days < 0 else days, "days_left": days}
