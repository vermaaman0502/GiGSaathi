"""Practice Mode: scripted role-play of hard conversations with coaching. Scenario text is
available in English, Hindi and Hinglish; other languages fall back to English."""
from typing import Dict, Optional

SCENARIOS = {
    "contractor_wages": {
        "title": {"en": "Contractor delays your wages", "hi": "ठेकेदार मज़दूरी रोक रहा है", "hinglish": "Thekedar mazdoori rok raha hai"},
        "steps": [
            {"npc": {"en": "Contractor: Next week I will pay. Stop asking every day.",
                     "hi": "ठेकेदार: अगले हफ़्ते दूँगा। रोज़ मत माँगो।",
                     "hinglish": "Thekedar: Agle hafte dunga. Roz mat maango."},
             "tip": {"en": "Stay calm. State the exact amount and the dates you worked. Ask for a date in writing.",
                     "hi": "शांत रहें। सही रकम और काम की तारीखें बताएँ। लिखित तारीख माँगें।",
                     "hinglish": "Shant rahein. Sahi rakam aur kaam ki tareekhein batayein. Likhit tareekh maangein."}},
            {"npc": {"en": "Contractor: I do not have a record of that. Prove it.",
                     "hi": "ठेकेदार: मेरे पास इसका रिकॉर्ड नहीं है। सबूत दो।",
                     "hinglish": "Thekedar: Mere paas iska record nahi hai. Saboot do."},
             "tip": {"en": "Mention your wage diary, messages and co-workers. Say you will go to the Labour Department if not paid by the date.",
                     "hi": "अपनी मज़दूरी डायरी, मैसेज और साथियों का ज़िक्र करें। कहें कि तारीख तक न मिला तो श्रम विभाग जाएँगे।",
                     "hinglish": "Apni mazdoori diary, messages aur saathiyon ka zikr karein. Kahein ki tareekh tak na mila to shram vibhag jayenge."}},
        ],
    },
    "police_stop": {
        "title": {"en": "Police stop your vehicle", "hi": "पुलिस ने गाड़ी रोकी", "hinglish": "Police ne gaadi roki"},
        "steps": [
            {"npc": {"en": "Officer: Show your papers. Why are you driving here?",
                     "hi": "पुलिस: कागज़ दिखाओ। यहाँ क्यों चला रहे हो?",
                     "hinglish": "Police: Kagaz dikhao. Yahan kyun chala rahe ho?"},
             "tip": {"en": "Be polite, keep DL, RC and insurance ready, and say you are a delivery/ride partner on duty.",
                     "hi": "विनम्र रहें, DL, RC और बीमा तैयार रखें और बताएँ कि आप ड्यूटी पर डिलीवरी/राइड पार्टनर हैं।",
                     "hinglish": "Vinamra rahein, DL, RC aur bima tayyar rakhein aur batayein ki aap duty par delivery/ride partner hain."}},
            {"npc": {"en": "Officer: Pay the fine here in cash.",
                     "hi": "पुलिस: जुर्माना यहीं नकद दो।",
                     "hinglish": "Police: Jurmana yahin nakad do."},
             "tip": {"en": "Ask for an official challan or receipt. Do not pay without a receipt. Note the officer's name/number.",
                     "hi": "आधिकारिक चालान या रसीद माँगें। रसीद के बिना पैसे न दें। अधिकारी का नाम/नंबर नोट करें।",
                     "hinglish": "Official challan ya receipt maangein. Receipt ke bina paise na dein. Officer ka naam/number note karein."}},
        ],
    },
    "customer_complaint": {
        "title": {"en": "Customer complains and refuses to pay", "hi": "ग्राहक शिकायत कर भुगतान से मना कर रहा है", "hinglish": "Customer complaint karke payment se mana kar raha hai"},
        "steps": [
            {"npc": {"en": "Customer: You are late. I will not pay the tip and I will report you.",
                     "hi": "ग्राहक: आप देर से आए। टिप नहीं दूँगा और शिकायत करूँगा।",
                     "hinglish": "Customer: Aap late aaye. Tip nahi dunga aur complaint karunga."},
             "tip": {"en": "Apologise briefly, explain the real reason (traffic/restaurant delay) without arguing, and offer to help now.",
                     "hi": "संक्षेप में माफ़ी माँगें, असली कारण (ट्रैफ़िक/रेस्तराँ में देरी) बिना बहस बताएँ और अभी मदद की पेशकश करें।",
                     "hinglish": "Sankshep mein maafi maangein, asli karan (traffic/restaurant mein deri) bina bahas batayein aur abhi madad ki peshkash karein."}},
        ],
    },
}

POLITE = ["please", "sorry", "kindly", "request", "thank", "कृपया", "माफ़", "धन्यवाद", "kripya", "maafi", "shukriya"]
FACTS = ["date", "amount", "rs", "₹", "diary", "receipt", "challan", "tareekh", "रसीद", "तारीख", "डायरी", "proof", "saboot", "सबूत"]
ESCALATE = ["labour", "labor", "complaint", "shram", "श्रम", "grievance", "officer"]


def pick(d: Dict[str, str], lang: str) -> str:
    return d.get(lang) or d.get("en", "")


def start(scenario: str, lang: str) -> Optional[Dict]:
    sc = SCENARIOS.get(scenario)
    if not sc:
        return None
    return {"scenario": scenario, "step": 0, "title": pick(sc["title"], lang), "npc": pick(sc["steps"][0]["npc"], lang), "done": False}


def reply(scenario: str, step: int, answer: str, lang: str) -> Optional[Dict]:
    sc = SCENARIOS.get(scenario)
    if not sc or step >= len(sc["steps"]):
        return None
    low = answer.lower()
    score = sum([any(w in low for w in POLITE), any(w in low for w in FACTS) or any(c.isdigit() for c in low), any(w in low for w in ESCALATE)])
    feedback = {"score": score, "max": 3, "tip": pick(sc["steps"][step]["tip"], lang),
                "checks": {"polite": any(w in low for w in POLITE), "facts": any(w in low for w in FACTS) or any(c.isdigit() for c in low),
                           "next_step": any(w in low for w in ESCALATE)}}
    nxt = step + 1
    done = nxt >= len(sc["steps"])
    return {"scenario": scenario, "step": nxt, "npc": None if done else pick(sc["steps"][nxt]["npc"], lang), "done": done, "feedback": feedback}
