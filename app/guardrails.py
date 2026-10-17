"""Privacy masking, forbidden-ask checks and crisis escalation. Runs before any LLM call."""
import re
from typing import Dict, Optional

AADHAAR_RE = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")
OTP_RE = re.compile(r"(otp|pin|cvv|password)\D{0,12}\d{3,8}", re.I)
PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
CARD_RE = re.compile(r"\b(?:\d[ -]?){13,16}\b")

HELPLINES = (
    "Emergency: 112 | Ambulance: 108 | Women helpline: 181 | "
    "Free legal aid (NALSA): 15100 | Cyber fraud: 1930"
)

CRISIS_WORDS = [
    "suicide", "kill myself", "marna chahta", "marna chahti", "jaan se maar", "bachao", "bachaao",
    "accident", "attack", "harass", "molest", "chhed", "threat", "dhamki", "beaten", "maar pit",
    "जान से", "बचाओ", "दुर्घटना", "हमला", "छेड़", "धमकी", "आत्महत्या",
]


def mask_pii(text: str) -> str:
    """Mask identifiers so they never reach the LLM or the logs."""
    text = OTP_RE.sub("[SECRET REMOVED]", text)
    text = AADHAAR_RE.sub("XXXX-XXXX-XXXX", text)
    text = PAN_RE.sub("[PAN MASKED]", text)
    text = CARD_RE.sub("[NUMBER MASKED]", text)
    return text


def shared_secret(text: str) -> bool:
    return bool(OTP_RE.search(text))


def crisis_reply(text: str) -> Optional[Dict]:
    low = text.lower()
    if any(w in low for w in CRISIS_WORDS):
        return {
            "reply": (
                "I am worried about your safety. Please contact a human right now.\n"
                f"{HELPLINES}\n"
                "If you are in danger, move to a safe, public place and share your live location "
                "with someone you trust. You are not alone."
            ),
            "escalate": True,
        }
    return None


SECRET_WARNING = (
    "Please never share your OTP, PIN, password or full Aadhaar number with anyone - "
    "not even with me. I have removed it from your message."
)
