"""Locale loading, language detection and translated message lookup.
Each language lives in app/locales/<code>.json so native speakers can review/fix strings.
Missing keys fall back to English."""
import json
import re
from pathlib import Path
from typing import Dict

LOCALE_DIR = Path(__file__).resolve().parent / "locales"
DEFAULT = "en"

_cache: Dict[str, Dict[str, str]] = {}


def _load(code: str) -> Dict[str, str]:
    if code not in _cache:
        p = LOCALE_DIR / f"{code}.json"
        _cache[code] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return _cache[code]


def languages() -> Dict[str, str]:
    """code -> native name, English first."""
    out = {}
    for p in sorted(LOCALE_DIR.glob("*.json")):
        out[p.stem] = _load(p.stem).get("_name", p.stem)
    return {DEFAULT: out.pop(DEFAULT), **out}


def normalize(lang: str) -> str:
    lang = (lang or DEFAULT).lower()
    return lang if (LOCALE_DIR / f"{lang}.json").exists() else DEFAULT


def t(lang: str, key: str, **kw) -> str:
    s = _load(normalize(lang)).get(key) or _load(DEFAULT).get(key, key)
    try:
        return s.format(**kw)
    except (KeyError, IndexError):
        return s


def fmt(n: float) -> str:
    """Whole rupees without trailing .0, keeps decimals when needed."""
    return f"{n:,.0f}" if abs(n - round(n)) < 0.005 else f"{n:,.2f}"


_SCRIPTS = [  # unicode block -> language (Devanagari defaults to Hindi; Marathi if user picked it)
    (re.compile(r"[ঀ-৿]"), "bn"),
    (re.compile(r"[਀-੿]"), "pa"),
    (re.compile(r"[઀-૿]"), "gu"),
    (re.compile(r"[଀-୿]"), "or"),
    (re.compile(r"[஀-௿]"), "ta"),
    (re.compile(r"[ఀ-౿]"), "te"),
    (re.compile(r"[ಀ-೿]"), "kn"),
    (re.compile(r"[ഀ-ൿ]"), "ml"),
    (re.compile(r"[ऀ-ॿ]"), "hi"),
]
_HINGLISH = {"kamaya", "kamaye", "kamai", "kharcha", "kharch", "hisab", "hisaab", "mahine", "aaj", "kitna", "baki", "nahi",
             "mujhe", "batao", "bataiye", "chahiye", "paisa", "madad", "yojana", "gaadi", "kiraya", "ghanta", "mera", "meri"}


def detect(text: str, chosen: str = "auto") -> str:
    """Reply language: explicit choice wins; 'auto' guesses from script/words."""
    if chosen and chosen != "auto":
        return normalize(chosen)
    for rx, code in _SCRIPTS:
        if rx.search(text):
            return code
    words = set(re.findall(r"[a-z]+", text.lower()))
    return "hinglish" if words & _HINGLISH else DEFAULT


def ui(lang: str) -> Dict[str, str]:
    """All UI strings (everything except reply templates) merged over English."""
    base = {k: v for k, v in _load(DEFAULT).items() if k != "_name"}
    base.update({k: v for k, v in _load(normalize(lang)).items() if k != "_name"})
    return base


# Speech-recognition / synthesis locale tags for the browser.
SPEECH = {"en": "en-IN", "hi": "hi-IN", "hinglish": "hi-IN", "bn": "bn-IN", "ta": "ta-IN", "te": "te-IN", "mr": "mr-IN",
          "gu": "gu-IN", "kn": "kn-IN", "ml": "ml-IN", "pa": "pa-IN", "or": "or-IN"}
