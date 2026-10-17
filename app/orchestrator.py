"""Message router: guardrails -> intent -> tools/RAG -> (optional LLM) -> reply.
Intent detection is keyword-based (English, Hindi, Hinglish) so it works offline; the LLM only
phrases the answer from verified FACTS."""
import re
from typing import Dict, List, Optional

from . import guardrails, llm, rag, store
from .tools import earnings, money

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
NUM = re.compile(r"\d+(?:\.\d+)?")


def detect_lang(text: str) -> str:
    return "hi" if DEVANAGARI.search(text) else "en"


def _has(text: str, words: List[str]) -> bool:
    return any(w in text for w in words)


def _after(text: str, words: List[str]) -> Optional[float]:
    """First number that follows any of the given words."""
    for w in words:
        m = re.search(re.escape(w) + r"\D{0,12}(\d+(?:\.\d+)?)", text)
        if m:
            return float(m.group(1))
    return None


def _before(text: str, words: List[str]) -> Optional[float]:
    """Number written right before a unit word, e.g. '8 km'."""
    for w in words:
        m = re.search(r"(\d+(?:\.\d+)?)\s*" + re.escape(w), text)
        if m:
            return float(m.group(1))
    return None


def detect_intent(low: str) -> str:
    if _has(low, ["sos", "emergency", "khatre", "खतरे"]):
        return "sos"
    if _has(low, ["worth", "should i accept", "trip", "ride", "order lena", "सवारी"]) and _before(low, ["km", "किमी"]) is not None:
        return "trip"
    if _has(low, ["loan", "emi", "interest", "byaj", "ब्याज", "लोन"]) and _has(low, ["months", "month", "mahine", "महीने"]):
        return "loan"
    if _has(low, ["complaint", "grievance", "deactivat", "blocked", "shikayat", "शिकायत", "id band", "ID बंद"]):
        return "grievance"
    if _has(low, ["spent", "kharcha", "kharch", "kharid", "खर्च", "expense"]):
        return "expense"
    if _has(low, ["earned", "kamaya", "kamai", "kamaye", "कमाया", "कमाई", "income today"]) and NUM.search(low):
        return "income"
    if _has(low, ["summary", "hisab", "hisaab", "today", "aaj ka", "हिसाब", "आज"]) and _has(low, ["summary", "hisab", "hisaab", "हिसाब", "kitna", "कितना"]):
        return "summary"
    if _has(low, ["safe to spend", "daily limit", "kitna kharch", "कितना खर्च"]):
        return "safe_to_spend"
    if _has(low, ["owes", "baki", "bakaya", "बकाया", "due"]) and NUM.search(low):
        return "diary"
    return "knowledge"


def _fmt(hi: bool, en: str, hin: str) -> str:
    return hin if hi else en


def handle(user: str, raw_text: str) -> Dict:
    """Returns {reply, intent, sources, escalate}."""
    secret = guardrails.shared_secret(raw_text)
    text = guardrails.mask_pii(raw_text)
    low = text.lower()
    hi = detect_lang(text) == "hi"
    prefix = (guardrails.SECRET_WARNING + "\n\n") if secret else ""

    crisis = guardrails.crisis_reply(low)
    if crisis:
        return {"reply": prefix + crisis["reply"], "intent": "crisis", "sources": [], "escalate": True}

    intent = detect_intent(low)
    facts, sources, template = "", [], ""

    if intent == "sos":
        template = _fmt(hi, f"SOS: call 112 now. Share your live location with a trusted person. {guardrails.HELPLINES}",
                        f"SOS: abhi 112 par call karein. Apni live location kisi apne ko bhejein. {guardrails.HELPLINES}")
        return {"reply": prefix + template, "intent": intent, "sources": [], "escalate": True}

    if intent == "trip":
        fare = _after(low, ["fare", "pay", "kamai", "rs", "₹"]) or 0.0
        km = _before(low, ["km", "किमी"]) or 0.0
        mins = _before(low, ["min", "minute", "मिनट"]) or km * 3
        t = earnings.trip_worth(fare=fare, distance_km=km, time_min=mins, return_km=km * 0.5)
        verdict = {"accept": "ACCEPT", "marginal": "MARGINAL", "skip": "SKIP"}[t["verdict"]]
        template = _fmt(
            hi,
            f"Trip: fare Rs {fare:.0f}, {km:.0f} km. After fuel and wear you keep about Rs {t['net_profit']:.0f} "
            f"(Rs {t['net_per_hour']:.0f}/hour). Verdict: {verdict}. (Assumes 40 km/l bike, petrol Rs 100, 50% empty return.)",
            f"Trip: kiraya Rs {fare:.0f}, {km:.0f} km. Petrol aur ghisai ke baad bachega lagbhag Rs {t['net_profit']:.0f} "
            f"(Rs {t['net_per_hour']:.0f}/ghanta). Salah: {verdict}.",
        )
        facts = f"Trip calc: {t}"

    elif intent == "loan":
        months = _before(low, ["months", "month", "mahine", "महीने"]) or 12
        emi = _after(low, ["emi"]) or 0.0
        principal = _after(low, ["loan", "लोन", "borrow", "of rs", "rs"]) or 0.0
        try:
            r = money.loan_check(principal, emi, int(months))
            template = _fmt(
                hi,
                f"You receive Rs {r['money_received']:.0f} and repay Rs {r['total_repayment']:.0f}. Real yearly interest is about "
                f"{r['yearly_interest_pct']}%. Risk: {r['risk'].upper()}. Safer options: bank/SHG loan, PM MUDRA.",
                f"Aapko Rs {r['money_received']:.0f} milenge aur Rs {r['total_repayment']:.0f} chukane honge. Asli saalana byaj lagbhag "
                f"{r['yearly_interest_pct']}%. Khatra: {r['risk'].upper()}. Behtar: bank/SHG loan, PM MUDRA.",
            )
            facts = f"Loan check: {r}"
        except ValueError:
            template = _fmt(hi, "Tell me the loan amount, monthly EMI and number of months, e.g. 'loan 10000 emi 1200 for 12 months'.",
                            "Loan rashi, mahine ki EMI aur mahine bataiye, jaise 'loan 10000 emi 1200 12 months'.")

    elif intent == "grievance":
        template = _fmt(
            hi,
            "I can draft a polite complaint. Use the Grievance Ladder: 1) platform support, 2) grievance officer, 3) labour department, "
            "4) consumer forum, 5) free legal aid (NALSA 15100). Send me your name, company, date and amount and I will write the letter.",
            "Main shikayat ka patra bana sakta hoon. Pehle platform support, phir grievance officer, phir labour department, phir consumer forum, "
            "phir muft kanooni madad (NALSA 15100). Apna naam, company, tareekh aur rashi bhejein.",
        )

    elif intent == "expense":
        amt = _after(low, ["spent", "kharcha", "kharch", "खर्च", "rs", "₹"]) or (float(NUM.search(low).group()) if NUM.search(low) else 0.0)
        cat = money.categorise(low)
        store.add(user, "expense", amt, cat, text[:100])
        template = _fmt(hi, f"Noted: Rs {amt:.0f} spent on {cat}.", f"Likh liya: Rs {amt:.0f} {cat} par kharch.")

    elif intent == "income":
        amt = float(NUM.search(low).group()) if NUM.search(low) else 0.0
        store.add(user, "income", amt, "work", text[:100])
        template = _fmt(hi, f"Noted: Rs {amt:.0f} earned today.", f"Likh liya: aaj Rs {amt:.0f} kamaye.")

    elif intent == "diary":
        amt = float(NUM.search(low).group()) if NUM.search(low) else 0.0
        store.add(user, "diary", amt, "unpaid_due", text[:200])
        template = _fmt(hi, f"Saved in your wage diary: Rs {amt:.0f} due. This dated note can help as evidence.",
                        f"Mazdoori diary mein likh liya: Rs {amt:.0f} baaki. Ye tareekh ke saath saboot ban sakta hai.")

    elif intent == "summary":
        s = store.daily_summary(user)
        template = _fmt(hi, f"Today: earned Rs {s['earned']:.0f}, spent Rs {s['spent']:.0f}, saved Rs {s['saved']:.0f}.",
                        f"Aaj: kamaya Rs {s['earned']:.0f}, kharch Rs {s['spent']:.0f}, bacha Rs {s['saved']:.0f}.")

    elif intent == "safe_to_spend":
        template = _fmt(hi, "Tell me your monthly income, rent, EMI and bills and I will give a daily safe-to-spend number.",
                        "Mahine ki kamai, kiraya, EMI aur bills bataiye, main roz ka safe-to-spend number dunga.")

    else:  # knowledge: RAG
        hits = rag.get_retriever().search(text, k=2)
        if not hits:
            template = _fmt(
                hi,
                "I am not sure about this and do not want to guess. Please ask at your nearest CSC, call 14434 (e-Shram) or "
                "NALSA 15100 for legal questions.",
                "Mujhe iske baare mein pakka nahi pata, andaza nahi lagaunga. Kripya apne nazdiki CSC par poochhein, e-Shram 14434 ya "
                "kanooni madad ke liye NALSA 15100 par call karein.",
            )
        else:
            sources = [{"title": h["title"], "url": h["source"]} for h in hits]
            facts = "\n".join(f"- {h['title']}: {h['summary']} Documents: {', '.join(h['documents']) or 'n/a'}. Apply: {h['how_to_apply']} (Source: {h['source']})" for h in hits)
            top = hits[0]
            template = f"{top['title']}: {top['summary']}\nHow to apply: {top['how_to_apply']}\nSource: {top['source']} (please confirm details on the official portal)"

    reply = llm.compose(text, facts) if facts else None
    return {"reply": prefix + (reply or template), "intent": intent, "sources": sources, "escalate": False}
