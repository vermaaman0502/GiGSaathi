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


_SCRIPTS = [  # unicode block -> language (Devanagari defaults to Hindi unless Marathi markers appear)
    (re.compile(r"[\u0980-\u09FF]"), "bn"),
    (re.compile(r"[\u0A00-\u0A7F]"), "pa"),
    (re.compile(r"[\u0A80-\u0AFF]"), "gu"),
    (re.compile(r"[\u0B00-\u0B7F]"), "or"),
    (re.compile(r"[\u0B80-\u0BFF]"), "ta"),
    (re.compile(r"[\u0C00-\u0C7F]"), "te"),
    (re.compile(r"[\u0C80-\u0CFF]"), "kn"),
    (re.compile(r"[\u0D00-\u0D7F]"), "ml"),
    (re.compile(r"[\u0600-\u06FF]"), "ur"),   # Arabic script: Urdu (no template locale yet - uses the LLM if configured)
    (re.compile(r"[\u0900-\u097F]"), "hi"),
]
_MARATHI = ("आहे", "आहेत", "मला", "तुम्ही", "काय", "आणि", "कसे", "पाहिजे", "माझ", "करा", "नाही का", "होते")
_HINGLISH = {"kamaya", "kamaye", "kamai", "kharcha", "kharch", "hisab", "hisaab", "mahine", "aaj", "kitna", "baki", "nahi",
             "mujhe", "batao", "bataiye", "chahiye", "paisa", "madad", "yojana", "gaadi", "kiraya", "ghanta", "mera", "meri",
             "hai", "kya", "kaise", "karo", "kar", "hum", "aap", "bhai", "sahi", "ke", "ka", "ki", "ko"}
# Names for the LLM when a language has no template locale.
EXTRA_NAMES = {"ur": "Urdu", "as": "Assamese", "ne": "Nepali"}


def language_name(code: str) -> str:
    return languages().get(code) or EXTRA_NAMES.get(code) or "English"


def detect(text: str, chosen: str = "auto", prefer: str = "") -> str:
    """Language the worker WROTE in. 'auto' (default): decided from the message itself - the reply
    must come back in that same language. An explicit `chosen` code overrides. `prefer` (the UI
    language) is used only when the message has no letters at all (e.g. just numbers)."""
    if chosen and chosen != "auto":
        return normalize(chosen)
    for rx, code in _SCRIPTS:
        if rx.search(text):
            if code == "hi" and any(m in text for m in _MARATHI):
                return "mr"
            return code
    words = re.findall(r"[a-z]+", text.lower())
    if not words:
        return normalize(prefer) if prefer else DEFAULT
    strong = set(words) & (_HINGLISH - {"hai", "kya", "ke", "ka", "ki", "ko", "kar", "hum", "aap", "sahi", "bhai"})
    weak = set(words) & {"hai", "kya", "kaise", "ke", "ka", "ki", "ko", "kar", "hum", "aap"}
    return "hinglish" if strong or len(weak) >= 2 else DEFAULT


def ui(lang: str) -> Dict[str, str]:
    """All UI strings (everything except reply templates) merged over English."""
    base = {k: v for k, v in _load(DEFAULT).items() if k != "_name"}
    base.update({k: v for k, v in _load(normalize(lang)).items() if k != "_name"})
    return base


# Speech-recognition / synthesis locale tags for the browser.
SPEECH = {"en": "en-IN", "hi": "hi-IN", "hinglish": "hi-IN", "bn": "bn-IN", "ta": "ta-IN", "te": "te-IN", "mr": "mr-IN",
          "gu": "gu-IN", "kn": "kn-IN", "ml": "ml-IN", "pa": "pa-IN", "or": "or-IN"}
