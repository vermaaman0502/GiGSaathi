"""Message router: guardrails -> intent -> tools/RAG -> (optional LLM) -> reply in the worker's language.
Intent detection is keyword-based (English, Hindi, Hinglish + common words in the other languages) so it
works offline; the LLM only phrases answers from verified FACTS."""
import re
from typing import Dict, List, Optional

from . import guardrails, i18n, llm, rag, schemes, store
from .tools import earnings, money

NUM = re.compile(r"\d+(?:\.\d+)?")

SOS_W = ["sos", "emergency", "khatre", "खतरे", "জরুরি", "அவசரம்", "అత్యవసరం", "आणीबाणी", "કટોકટી", "ತುರ್ತು", "അടിയന്തരം", "ਐਮਰਜੈਂਸੀ", "ଜରୁରୀ"]
EXPENSE_W = ["spent", "kharcha", "kharch", "kharid", "खर्च", "expense", "খরচ", "செலவு", "ఖర్చు", "ખર્ચ", "ಖರ್ಚು", "ചെലവ്", "ਖਰਚ", "ଖର୍ଚ୍ଚ"]
INCOME_W = ["earned", "kamaya", "kamai", "kamaye", "कमाया", "कमाए", "कमाई", "कमावले", "income today", "আয়", "சம்பாதித்", "సంపాదించ", "કમાયા", "ગળ", "ಗಳಿಸ", "സമ്പാദിച്ച", "ਕਮਾਏ", "ଆୟ"]
SUMMARY_W = ["summary", "hisab", "hisaab", "हिसाब", "हिशोब", "হিসাব", "கணக்கு", "లెక్క", "હિસાબ", "ಲೆಕ್ಕ", "കണക്ക്", "ਹਿਸਾਬ", "ହିସାବ"]
LOAN_W = ["loan", "emi", "interest", "byaj", "ब्याज", "लोन", "व्याज", "সুদ", "கடன்", "రుణం", "લોન", "ಸಾಲ", "വായ്പ", "ਕਰਜ਼ਾ", "ଋଣ"]
MONTH_W = ["months", "month", "mahine", "महीने", "महिने", "মাস", "மாத", "నెల", "મહિના", "ತಿಂಗಳ", "മാസ", "ਮਹੀਨ", "ମାସ"]
KM_W = ["km", "किलोमीटर", "ਕਿਲੋਮੀਟਰ", "किमी", "কিমি", "கிமீ", "కి.మీ", "કિમી", "ಕಿಮೀ", "കി.മീ", "ਕਿਮੀ", "କିମି"]
GRIEV_W = ["complaint", "grievance", "deactivat", "blocked", "shikayat", "शिकायत", "तक्रार", "অভিযোগ", "புகார்", "ఫిర్యాదు", "ફરિયાદ", "ದೂರು", "പരാതി", "ਸ਼ਿਕਾਇਤ", "ଅଭିଯୋଗ", "id band"]
DIARY_W = ["owes", "baki", "bakaya", "बकाया", "due", "बाकी"]
SAFE_W = ["safe to spend", "daily limit", "kitna kharch", "कितना खर्च"]


def _has(text: str, words: List[str]) -> bool:
    return any(w in text for w in words)


def _after(text: str, words: List[str]) -> Optional[float]:
    for w in words:
        m = re.search(re.escape(w) + r"\D{0,12}(\d+(?:\.\d+)?)", text)
        if m:
            return float(m.group(1))
    return None


def _before(text: str, words: List[str]) -> Optional[float]:
    for w in words:
        m = re.search(r"(\d+(?:\.\d+)?)\s*" + re.escape(w), text)
        if m:
            return float(m.group(1))
    return None


def detect_intent(low: str) -> str:
    if _has(low, SOS_W):
        return "sos"
    if _has(low, ["worth", "should i accept", "trip", "ride", "order lena", "सवारी", "ट्रिप", "ਟ੍ਰਿਪ", "ਸਵਾਰੀ"]) and _before(low, KM_W) is not None:
        return "trip"
    if _has(low, LOAN_W) and _has(low, MONTH_W):
        return "loan"
    if _has(low, GRIEV_W):
        return "grievance"
    if _has(low, EXPENSE_W):
        return "expense"
    if _has(low, INCOME_W) and NUM.search(low):
        return "income"
    if _has(low, SUMMARY_W) and not NUM.search(low):
        return "summary"
    if _has(low, SAFE_W):
        return "safe_to_spend"
    if _has(low, DIARY_W) and NUM.search(low):
        return "diary"
    return "knowledge"


def handle(user: str, raw_text: str, lang: str = "auto", prefer: str = "") -> Dict:
    """Returns {reply, intent, lang, sources, escalate}."""
    secret = guardrails.shared_secret(raw_text)
    text = guardrails.mask_pii(raw_text)
    low = text.lower()
    L = i18n.detect(text, lang, prefer)          # language the worker wrote in -> reply in the same one
    LT = i18n.normalize(L)                         # template locale (falls back to English if no template exists)
    t = lambda k, **kw: i18n.t(LT, k, **kw)  # noqa: E731
    prefix = (t("secret") + "\n\n") if secret else ""

    def out(reply, intent, sources=None, escalate=False):
        return {"reply": prefix + reply, "intent": intent, "lang": L, "sources": sources or [], "escalate": escalate}

    if guardrails.is_crisis(low):
        return out(t("crisis"), "crisis", escalate=True)

    intent = detect_intent(low)
    if intent == "sos":
        return out(t("sos"), intent, escalate=True)

    facts, sources, template = "", [], ""

    if intent == "trip":
        fare = _after(low, ["fare", "pay", "kamai", "kiraya", "किराया", "ਕਿਰਾਇਆ", "rs", "₹"]) or 0.0
        km = _before(low, KM_W) or 0.0
        mins = _before(low, ["min", "minute", "मिनट"]) or km * 3
        r = earnings.trip_worth(fare=fare, distance_km=km, time_min=mins, return_km=km * 0.5)
        template = t("trip", fare=i18n.fmt(fare), km=i18n.fmt(km), net=i18n.fmt(r["net_profit"]),
                     hourly=i18n.fmt(r["net_per_hour"]), verdict=t("v_" + r["verdict"]))
        facts = f"Trip calc: {r}"

    elif intent == "loan":
        months = _before(low, MONTH_W) or 12
        emi = _after(low, ["emi"]) or 0.0
        principal = _after(low, ["loan", "लोन", "borrow", "of rs", "rs"]) or 0.0
        try:
            r = money.loan_check(principal, emi, int(months))
            template = t("loan", recv=i18n.fmt(r["money_received"]), total=i18n.fmt(r["total_repayment"]),
                         pct=r["yearly_interest_pct"], risk=t("r_" + r["risk"]))
            facts = f"Loan check: {r}"
        except ValueError:
            template = t("ask_loan")

    elif intent == "grievance":
        template = t("grievance_help")

    elif intent == "expense":
        amt = _after(low, EXPENSE_W + ["rs", "₹"]) or (float(NUM.search(low).group()) if NUM.search(low) else 0.0)
        cat = money.categorise(low)
        store.add(user, "expense", amt, cat, text[:100])
        template = t("noted_expense", amt=i18n.fmt(amt), cat=t("cat_" + cat))

    elif intent == "income":
        amt = float(NUM.search(low).group()) if NUM.search(low) else 0.0
        store.add(user, "income", amt, "work", text[:100])
        template = t("noted_income", amt=i18n.fmt(amt))

    elif intent == "diary":
        amt = float(NUM.search(low).group()) if NUM.search(low) else 0.0
        store.add(user, "diary", amt, "unpaid_due", text[:200])
        template = t("diary_saved", amt=i18n.fmt(amt))

    elif intent == "summary":
        s = store.daily_summary(user)
        template = t("summary", earned=i18n.fmt(s["earned"]), spent=i18n.fmt(s["spent"]), saved=i18n.fmt(s["saved"]))

    elif intent == "safe_to_spend":
        template = t("ask_safe")

    else:  # knowledge: RAG
        hits = rag.get_retriever().search(text, k=2)
        if not hits:
            template = t("unsure")
        else:
            views = [schemes.view(h, LT) for h in hits]
            sources = [{"title": v["title"], "url": v["apply_url"], "last_verified": v["last_verified"]} for v in views]
            facts = "\n".join(f"- {v['title']}: {v['summary']} Documents: {', '.join(v['documents']) or 'n/a'}. Apply: {v['how_to_apply']} (Source: {v['apply_url']})" for v in views)
            top = views[0]
            hdr = "" if top["text_language"] == LT else t("knowledge_hdr") + "\n"      # header only when text is not in the user's language
            ver = "" if top["last_verified"] else {"hi": "\n(पुष्टि नहीं - सरकारी पोर्टल पर जाँचें)", "pa": "\n(ਪੁਸ਼ਟੀ ਨਹੀਂ - ਸਰਕਾਰੀ ਪੋਰਟਲ ਤੇ ਜਾਂਚੋ)"}.get(LT, "\n(unverified - confirm on the official portal)")
            template = f"{hdr}{top['title']}: {top['summary']}\n→ {top['how_to_apply']}\n{top['apply_url']}{ver}"

    reply = llm.compose(text, facts, reply_language=i18n.language_name(L)) if facts else None
    return out(reply or template, intent, sources)
