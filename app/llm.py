"""Optional Claude call. Without ANTHROPIC_API_KEY (or on any error) callers fall back to
deterministic template replies, so the service still works offline and in tests."""
import os
from typing import Optional

import httpx

SYSTEM = """You are GigSaathi, a friendly assistant for gig and informal workers in India.
Rules:
- Reply in the SAME language/script the worker used (Hindi, Hinglish, English, etc.). Use very simple short sentences.
- Use ONLY the FACTS provided for numbers, scheme details and laws. If the facts do not cover it, say you are not sure and suggest the official helpline or a CSC. Never invent schemes, amounts, dates or laws.
- Mention the source name when you use a scheme fact.
- Never ask for OTP, PIN, password or full Aadhaar.
- For legal, medical or danger situations, point to 112, 108, 181, NALSA 15100 and a human helper.
- Keep replies under 120 words."""


def enabled() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def compose(user_text: str, facts: str, timeout: float = 20.0) -> Optional[str]:
    if not enabled():
        return None
    try:
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
                "max_tokens": 400,
                "system": SYSTEM,
                "messages": [{"role": "user", "content": f"FACTS:\n{facts}\n\nWORKER MESSAGE:\n{user_text}"}],
            },
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()
    except Exception:
        return None
