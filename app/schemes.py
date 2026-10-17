"""HaqFinder: structured scheme records, deterministic eligibility evaluation, adaptive questionnaire,
and localized views (English / Hindi / Punjabi; other languages fall back to English text)."""
import json
from pathlib import Path
from typing import Dict, List, Optional

DATA = Path(__file__).resolve().parent.parent / "data" / "schemes.json"
STATES = ("potentially_relevant", "more_info_needed", "appears_ineligible", "requires_official_confirmation")

_cache: Optional[List[Dict]] = None


def all_schemes() -> List[Dict]:
    global _cache
    if _cache is None:
        _cache = json.loads(DATA.read_text(encoding="utf-8"))
    return _cache


def get(scheme_id: str) -> Optional[Dict]:
    return next((s for s in all_schemes() if s["id"] == scheme_id), None)


# ---- questionnaire ----
FIELD_ORDER = ["state", "age", "work_type", "monthly_income", "epfo_member", "nps_member", "income_tax_payer",
               "govt_pension", "has_bank", "street_vendor"]
Q = {
    "state": {"type": "text", "label": {"en": "Which state do you live in?", "hi": "आप किस राज्य में रहते हैं?", "pa": "ਤੁਸੀਂ ਕਿਹੜੇ ਰਾਜ ਵਿੱਚ ਰਹਿੰਦੇ ਹੋ?"}},
    "district": {"type": "text", "optional": True, "label": {"en": "Which district?", "hi": "कौन-सा ज़िला?", "pa": "ਕਿਹੜਾ ਜ਼ਿਲ੍ਹਾ?"}},
    "age": {"type": "number", "label": {"en": "How old are you?", "hi": "आपकी उम्र कितनी है?", "pa": "ਤੁਹਾਡੀ ਉਮਰ ਕਿੰਨੀ ਹੈ?"}},
    "work_type": {"type": "select", "options": ["delivery", "driver", "domestic", "construction", "daily_wage", "street_vendor", "other"],
                  "label": {"en": "What work do you do?", "hi": "आप क्या काम करते हैं?", "pa": "ਤੁਸੀਂ ਕਿਹੜਾ ਕੰਮ ਕਰਦੇ ਹੋ?"}},
    "monthly_income": {"type": "number", "label": {"en": "Approximate monthly income (Rs)?", "hi": "लगभग मासिक आय (₹)?", "pa": "ਲਗਭਗ ਮਹੀਨਾਵਾਰ ਆਮਦਨ (₹)?"}},
    "epfo_member": {"type": "bool", "label": {"en": "Are you a member of EPFO or ESIC (a PF/ESI account through an employer)?", "hi": "क्या आप EPFO या ESIC के सदस्य हैं (नियोक्ता के ज़रिए PF/ESI खाता)?", "pa": "ਕੀ ਤੁਸੀਂ EPFO ਜਾਂ ESIC ਦੇ ਮੈਂਬਰ ਹੋ (ਮਾਲਕ ਰਾਹੀਂ PF/ESI ਖਾਤਾ)?"}},
    "nps_member": {"type": "bool", "label": {"en": "Are you covered under the National Pension System (NPS)?", "hi": "क्या आप राष्ट्रीय पेंशन प्रणाली (NPS) में शामिल हैं?", "pa": "ਕੀ ਤੁਸੀਂ ਰਾਸ਼ਟਰੀ ਪੈਨਸ਼ਨ ਪ੍ਰਣਾਲੀ (NPS) ਵਿੱਚ ਸ਼ਾਮਲ ਹੋ?"}},
    "income_tax_payer": {"type": "bool", "label": {"en": "Do you pay income tax?", "hi": "क्या आप आयकर देते हैं?", "pa": "ਕੀ ਤੁਸੀਂ ਇਨਕਮ ਟੈਕਸ ਦਿੰਦੇ ਹੋ?"}},
    "govt_pension": {"type": "bool", "label": {"en": "Do you already receive another government pension?", "hi": "क्या आपको पहले से कोई और सरकारी पेंशन मिलती है?", "pa": "ਕੀ ਤੁਹਾਨੂੰ ਪਹਿਲਾਂ ਹੀ ਕੋਈ ਹੋਰ ਸਰਕਾਰੀ ਪੈਨਸ਼ਨ ਮਿਲਦੀ ਹੈ?"}},
    "has_bank": {"type": "bool", "label": {"en": "Do you have a bank account?", "hi": "क्या आपका बैंक खाता है?", "pa": "ਕੀ ਤੁਹਾਡਾ ਬੈਂਕ ਖਾਤਾ ਹੈ?"}},
    "street_vendor": {"type": "bool", "label": {"en": "Are you a street vendor?", "hi": "क्या आप रेहड़ी-पटरी वाले हैं?", "pa": "ਕੀ ਤੁਸੀਂ ਰੇਹੜੀ-ਫੜ੍ਹੀ ਵਾਲੇ ਹੋ?"}},
}

REASON = {
    "age_ok": {"en": "Your age ({age}) is within {min}-{max}.", "hi": "आपकी उम्र ({age}) {min}-{max} के भीतर है।", "pa": "ਤੁਹਾਡੀ ਉਮਰ ({age}) {min}-{max} ਦੇ ਅੰਦਰ ਹੈ।"},
    "age_bad": {"en": "Your age ({age}) is outside {min}-{max}.", "hi": "आपकी उम्र ({age}) {min}-{max} से बाहर है।", "pa": "ਤੁਹਾਡੀ ਉਮਰ ({age}) {min}-{max} ਤੋਂ ਬਾਹਰ ਹੈ।"},
    "income_ok": {"en": "Your income (Rs {income}) is within the Rs {max} limit.", "hi": "आपकी आय (₹{income}) ₹{max} की सीमा के भीतर है।", "pa": "ਤੁਹਾਡੀ ਆਮਦਨ (₹{income}) ₹{max} ਦੀ ਹੱਦ ਦੇ ਅੰਦਰ ਹੈ।"},
    "income_bad": {"en": "Your income (Rs {income}) is above the Rs {max} limit.", "hi": "आपकी आय (₹{income}) ₹{max} की सीमा से ऊपर है।", "pa": "ਤੁਹਾਡੀ ਆਮਦਨ (₹{income}) ₹{max} ਦੀ ਹੱਦ ਤੋਂ ਉੱਪਰ ਹੈ।"},
    "excl_bad": {"en": "Not eligible if: {what}.", "hi": "इस स्थिति में पात्र नहीं: {what}।", "pa": "ਇਸ ਹਾਲਤ ਵਿੱਚ ਯੋਗ ਨਹੀਂ: {what}।"},
    "excl_ok": {"en": "You said you are not: {what}.", "hi": "आपने बताया कि आप नहीं हैं: {what}।", "pa": "ਤੁਸੀਂ ਦੱਸਿਆ ਕਿ ਤੁਸੀਂ ਨਹੀਂ ਹੋ: {what}।"},
    "bank_ok": {"en": "You have a bank account.", "hi": "आपका बैंक खाता है।", "pa": "ਤੁਹਾਡਾ ਬੈਂਕ ਖਾਤਾ ਹੈ।"},
    "bank_bad": {"en": "A bank account is required.", "hi": "बैंक खाता ज़रूरी है।", "pa": "ਬੈਂਕ ਖਾਤਾ ਜ਼ਰੂਰੀ ਹੈ।"},
    "work_ok": {"en": "Your work type matches.", "hi": "आपके काम का प्रकार मेल खाता है।", "pa": "ਤੁਹਾਡੇ ਕੰਮ ਦੀ ਕਿਸਮ ਮੇਲ ਖਾਂਦੀ ਹੈ।"},
    "work_bad": {"en": "This is for a different type of work.", "hi": "यह दूसरे प्रकार के काम के लिए है।", "pa": "ਇਹ ਹੋਰ ਕਿਸਮ ਦੇ ਕੰਮ ਲਈ ਹੈ।"},
    "state_ok": {"en": "Your state has its own law/scheme.", "hi": "आपके राज्य का अपना कानून/योजना है।", "pa": "ਤੁਹਾਡੇ ਰਾਜ ਦਾ ਆਪਣਾ ਕਾਨੂੰਨ/ਯੋਜਨਾ ਹੈ।"},
    "state_bad": {"en": "We found no gig-worker law in your state - ask your labour department.", "hi": "आपके राज्य में गिग-कामगार कानून नहीं मिला - अपने श्रम विभाग से पूछें।", "pa": "ਤੁਹਾਡੇ ਰਾਜ ਵਿੱਚ ਗਿਗ-ਕਾਮਾ ਕਾਨੂੰਨ ਨਹੀਂ ਮਿਲਿਆ - ਆਪਣੇ ਕਿਰਤ ਵਿਭਾਗ ਤੋਂ ਪੁੱਛੋ।"},
    "vendor_ok": {"en": "You are a street vendor.", "hi": "आप रेहड़ी-पटरी वाले हैं।", "pa": "ਤੁਸੀਂ ਰੇਹੜੀ-ਫੜ੍ਹੀ ਵਾਲੇ ਹੋ।"},
    "vendor_bad": {"en": "Only for street vendors.", "hi": "केवल रेहड़ी-पटरी वालों के लिए।", "pa": "ਸਿਰਫ਼ ਰੇਹੜੀ-ਫੜ੍ਹੀ ਵਾਲਿਆਂ ਲਈ।"},
}
EXCL_LABEL = {
    "epfo_member": {"en": "an EPFO/ESIC member", "hi": "EPFO/ESIC के सदस्य", "pa": "EPFO/ESIC ਦੇ ਮੈਂਬਰ"},
    "nps_member": {"en": "covered by NPS", "hi": "NPS में शामिल", "pa": "NPS ਵਿੱਚ ਸ਼ਾਮਲ"},
    "income_tax_payer": {"en": "an income-tax payer", "hi": "आयकर दाता", "pa": "ਇਨਕਮ ਟੈਕਸ ਦੇਣ ਵਾਲੇ"},
    "govt_pension": {"en": "receiving another government pension", "hi": "दूसरी सरकारी पेंशन पा रहे", "pa": "ਹੋਰ ਸਰਕਾਰੀ ਪੈਨਸ਼ਨ ਲੈ ਰਹੇ"},
}
STATE_LABEL = {
    "potentially_relevant": {"en": "Potentially relevant", "hi": "संभवतः प्रासंगिक", "pa": "ਸੰਭਾਵੀ ਤੌਰ ਤੇ ਢੁਕਵੀਂ"},
    "more_info_needed": {"en": "More information needed", "hi": "और जानकारी चाहिए", "pa": "ਹੋਰ ਜਾਣਕਾਰੀ ਚਾਹੀਦੀ ਹੈ"},
    "appears_ineligible": {"en": "Appears ineligible based on your answers", "hi": "आपके उत्तरों के आधार पर पात्र नहीं लगता", "pa": "ਤੁਹਾਡੇ ਜਵਾਬਾਂ ਮੁਤਾਬਕ ਯੋਗ ਨਹੀਂ ਜਾਪਦੀ"},
    "requires_official_confirmation": {"en": "Eligibility requires official confirmation", "hi": "पात्रता की सरकारी पुष्टि ज़रूरी है", "pa": "ਯੋਗਤਾ ਦੀ ਸਰਕਾਰੀ ਪੁਸ਼ਟੀ ਜ਼ਰੂਰੀ ਹੈ"},
}


def _l(d: Dict[str, str], lang: str) -> str:
    return d.get(lang) or d["en"]


def evaluate(scheme: Dict, a: Dict, lang: str = "en") -> Dict:
    """Deterministic rule check. Missing answers are never guessed - they produce `missing`."""
    r = scheme.get("rules", {})
    pos, neg, missing = [], [], []

    def need(field):
        if a.get(field) is None or a.get(field) == "":
            missing.append(field)
            return True
        return False

    age = a.get("age")
    if "min_age" in r or "max_age" in r:
        if not need("age"):
            lo, hi = r.get("min_age", 0), r.get("max_age", 120)
            ok = lo <= age <= hi
            (pos if ok else neg).append(_l(REASON["age_ok" if ok else "age_bad"], lang).format(age=age, min=lo, max=hi if "max_age" in r else "+"))
    if "max_monthly_income" in r:
        if not need("monthly_income"):
            ok = a["monthly_income"] <= r["max_monthly_income"]
            (pos if ok else neg).append(_l(REASON["income_ok" if ok else "income_bad"], lang).format(income=int(a["monthly_income"]), max=r["max_monthly_income"]))
    for f in r.get("excluded_if", []):
        v = a.get(f)
        what = _l(EXCL_LABEL[f], lang)
        if v is None:
            missing.append(f)
        elif v:
            neg.append(_l(REASON["excl_bad"], lang).format(what=what))
        else:
            pos.append(_l(REASON["excl_ok"], lang).format(what=what))
    for f in r.get("requires", []):
        v = a.get(f)
        key = "bank" if f == "has_bank" else "vendor"
        if v is None:
            missing.append(f)
        else:
            (pos if v else neg).append(_l(REASON[key + ("_ok" if v else "_bad")], lang))
    if r.get("work_types"):
        if not need("work_type"):
            ok = a["work_type"] in r["work_types"]
            (pos if ok else neg).append(_l(REASON["work_ok" if ok else "work_bad"], lang))
    if r.get("states"):
        if not need("state"):
            ok = str(a["state"]).strip().lower() in r["states"]
            (pos if ok else neg).append(_l(REASON["state_ok" if ok else "state_bad"], lang))
    missing = [m for i, m in enumerate(missing) if m not in missing[:i]]

    if neg:
        state = "appears_ineligible"
    elif missing:
        state = "more_info_needed"
    elif scheme.get("confirm_officially"):
        state = "requires_official_confirmation"
    else:
        state = "potentially_relevant"
    return {"state": state, "state_label": _l(STATE_LABEL[state], lang), "why_qualify": pos, "why_not": neg, "missing": missing}


def view(scheme: Dict, lang: str = "en") -> Dict:
    """Localized card payload (title/summary/how_to_apply from i18n when available)."""
    loc = (scheme.get("i18n") or {}).get(lang, {})
    return {
        "id": scheme["id"], "kind": scheme.get("kind", "scheme"),
        "title": loc.get("title") or scheme["title"], "authority": scheme.get("authority", ""),
        "summary": loc.get("summary") or scheme["summary"], "how_to_apply": loc.get("how_to_apply") or scheme["how_to_apply"],
        "benefits": scheme.get("benefits", []), "exclusions": scheme.get("exclusions", []), "documents": scheme.get("documents", []),
        "steps": scheme.get("steps", []), "apply_url": scheme.get("apply_url") or scheme.get("source"), "channels": scheme.get("channels", []),
        "sources": scheme.get("sources", []), "last_verified": scheme.get("last_verified"),
        "verification": "verified" if scheme.get("last_verified") else "unverified_seed",
        "text_language": lang if loc else "en",
    }


def match(answers: Dict, lang: str = "en") -> List[Dict]:
    out = []
    for s in all_schemes():
        if s.get("kind") != "scheme":
            continue
        ev = evaluate(s, answers, lang)
        out.append({**view(s, lang), **ev})
    order = {k: i for i, k in enumerate(["potentially_relevant", "requires_official_confirmation", "more_info_needed", "appears_ineligible"])}
    out.sort(key=lambda c: order[c["state"]])
    return out


def next_questions(answers: Dict, lang: str = "en") -> List[Dict]:
    """Only ask what is still needed by schemes that are not already ruled out."""
    need = set()
    for s in all_schemes():
        if s.get("kind") != "scheme":
            continue
        ev = evaluate(s, answers)
        if ev["state"] != "appears_ineligible":
            need.update(ev["missing"])
    ordered = [f for f in FIELD_ORDER if f in need]
    return [{"id": f, "type": Q[f]["type"], "options": Q[f].get("options"), "label": _l(Q[f]["label"], lang)} for f in ordered]
