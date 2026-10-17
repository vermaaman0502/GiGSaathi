"""Server-generated sentences for the v2 modules, in English, Hindi and Punjabi (the launch languages).
Other languages fall back to English. Structured codes/numbers are always returned alongside, so a
client can render its own text."""
from typing import Dict

M: Dict[str, Dict[str, str]] = {
    "summary_today": {
        "en": "Today you earned Rs {gross}, spent Rs {exp} and kept Rs {net} in {hours} hours (Rs {ph} per hour). Based on the shifts you saved.",
        "hi": "आज आपने ₹{gross} कमाए, ₹{exp} खर्च किए और {hours} घंटे में ₹{net} बचे (₹{ph} प्रति घंटा)। यह आपके सहेजे शिफ्ट पर आधारित है।",
        "pa": "ਅੱਜ ਤੁਸੀਂ ₹{gross} ਕਮਾਏ, ₹{exp} ਖਰਚ ਕੀਤੇ ਅਤੇ {hours} ਘੰਟਿਆਂ ਵਿੱਚ ₹{net} ਬਚੇ (₹{ph} ਪ੍ਰਤੀ ਘੰਟਾ)। ਇਹ ਤੁਹਾਡੀਆਂ ਸੰਭਾਲੀਆਂ ਸ਼ਿਫਟਾਂ ਤੇ ਆਧਾਰਿਤ ਹੈ।"},
    "summary_empty": {
        "en": "No shift saved for today yet. Add one in Earnings to see your net income.",
        "hi": "आज का कोई शिफ्ट अभी सहेजा नहीं है। शुद्ध आय देखने के लिए कमाई में एक जोड़ें।",
        "pa": "ਅੱਜ ਦੀ ਕੋਈ ਸ਼ਿਫਟ ਅਜੇ ਸੰਭਾਲੀ ਨਹੀਂ। ਸ਼ੁੱਧ ਆਮਦਨ ਦੇਖਣ ਲਈ ਕਮਾਈ ਵਿੱਚ ਇੱਕ ਜੋੜੋ।"},
    "p2a_short": {
        "en": "The payout you received is Rs {amt} less than the platform's own figures add up to. This is a possible discrepancy, not proof of wrongdoing - ask the platform to explain it.",
        "hi": "आपको मिला भुगतान प्लेटफ़ॉर्म के अपने आँकड़ों के जोड़ से ₹{amt} कम है। यह संभावित अंतर है, गड़बड़ी का सबूत नहीं - प्लेटफ़ॉर्म से इसकी वजह पूछें।",
        "pa": "ਤੁਹਾਨੂੰ ਮਿਲਿਆ ਭੁਗਤਾਨ ਪਲੇਟਫਾਰਮ ਦੇ ਆਪਣੇ ਅੰਕੜਿਆਂ ਦੇ ਜੋੜ ਨਾਲੋਂ ₹{amt} ਘੱਟ ਹੈ। ਇਹ ਸੰਭਾਵੀ ਫ਼ਰਕ ਹੈ, ਗਲਤ ਕੰਮ ਦਾ ਸਬੂਤ ਨਹੀਂ - ਪਲੇਟਫਾਰਮ ਤੋਂ ਇਸਦਾ ਕਾਰਨ ਪੁੱਛੋ।"},
    "p2a_promised": {
        "en": "You received Rs {amt} less than the promised Rs {promised}.",
        "hi": "आपको वादे के ₹{promised} से ₹{amt} कम मिले।",
        "pa": "ਤੁਹਾਨੂੰ ਵਾਅਦੇ ਦੇ ₹{promised} ਨਾਲੋਂ ₹{amt} ਘੱਟ ਮਿਲੇ।"},
    "p2a_none": {
        "en": "The numbers add up. No discrepancy found in this record.",
        "hi": "आँकड़े मेल खाते हैं। इस रिकॉर्ड में कोई अंतर नहीं मिला।",
        "pa": "ਅੰਕੜੇ ਮੇਲ ਖਾਂਦੇ ਹਨ। ਇਸ ਰਿਕਾਰਡ ਵਿੱਚ ਕੋਈ ਫ਼ਰਕ ਨਹੀਂ ਮਿਲਿਆ।"},
    "p2a_unknown": {
        "en": "Enter the amount you actually received to check for a discrepancy.",
        "hi": "अंतर जाँचने के लिए वह रकम भरें जो आपको असल में मिली।",
        "pa": "ਫ਼ਰਕ ਜਾਂਚਣ ਲਈ ਉਹ ਰਕਮ ਭਰੋ ਜੋ ਤੁਹਾਨੂੰ ਅਸਲ ਵਿੱਚ ਮਿਲੀ।"},
    "p2a_next": {
        "en": "Next step: raise it with platform support (step 1 of the ladder) with these records attached. Keep the ticket number.",
        "hi": "अगला कदम: इन रिकॉर्ड के साथ प्लेटफ़ॉर्म सपोर्ट (सीढ़ी का पहला कदम) को बताएँ। टिकट नंबर संभालकर रखें।",
        "pa": "ਅਗਲਾ ਕਦਮ: ਇਨ੍ਹਾਂ ਰਿਕਾਰਡਾਂ ਸਮੇਤ ਪਲੇਟਫਾਰਮ ਸਪੋਰਟ (ਪੌੜੀ ਦਾ ਪਹਿਲਾ ਕਦਮ) ਨੂੰ ਦੱਸੋ। ਟਿਕਟ ਨੰਬਰ ਸੰਭਾਲ ਕੇ ਰੱਖੋ।"},
    "opp_hours_title": {"en": "Work around {band} more often", "hi": "{band} के आसपास ज़्यादा काम करें", "pa": "{band} ਦੇ ਆਸ-ਪਾਸ ਵੱਧ ਕੰਮ ਕਰੋ"},
    "opp_hours_why": {
        "en": "Across {n} of your shifts, your take-home averaged Rs {a} per hour when you started in {band}, versus Rs {b} per hour at other times. Past results do not guarantee future earnings.",
        "hi": "आपके {n} शिफ्ट में {band} में शुरू करने पर औसत बचत ₹{a} प्रति घंटा रही, बाकी समय ₹{b} प्रति घंटा। पुराने नतीजे आगे की कमाई की गारंटी नहीं हैं।",
        "pa": "ਤੁਹਾਡੀਆਂ {n} ਸ਼ਿਫਟਾਂ ਵਿੱਚ {band} ਵਿੱਚ ਸ਼ੁਰੂ ਕਰਨ ਤੇ ਔਸਤ ਬਚਤ ₹{a} ਪ੍ਰਤੀ ਘੰਟਾ ਰਹੀ, ਬਾਕੀ ਸਮੇਂ ₹{b} ਪ੍ਰਤੀ ਘੰਟਾ। ਪੁਰਾਣੇ ਨਤੀਜੇ ਅੱਗੇ ਦੀ ਕਮਾਈ ਦੀ ਗਾਰੰਟੀ ਨਹੀਂ ਹਨ।"},
    "opp_hours_next": {"en": "Try one shift in this window this week and compare.", "hi": "इस हफ़्ते इस समय में एक शिफ्ट करके तुलना करें।", "pa": "ਇਸ ਹਫ਼ਤੇ ਇਸ ਸਮੇਂ ਵਿੱਚ ਇੱਕ ਸ਼ਿਫਟ ਕਰਕੇ ਤੁਲਨਾ ਕਰੋ।"},
    "opp_data_title": {"en": "Log a few more shifts to unlock shift suggestions", "hi": "शिफ्ट सुझाव पाने के लिए कुछ और शिफ्ट दर्ज करें", "pa": "ਸ਼ਿਫਟ ਸੁਝਾਅ ਲਈ ਕੁਝ ਹੋਰ ਸ਼ਿਫਟਾਂ ਦਰਜ ਕਰੋ"},
    "opp_data_why": {"en": "Suggestions need at least 5 shifts with a start time. You have {n}.", "hi": "सुझावों के लिए शुरू होने के समय सहित कम से कम 5 शिफ्ट चाहिए। आपके पास {n} हैं।", "pa": "ਸੁਝਾਵਾਂ ਲਈ ਸ਼ੁਰੂ ਹੋਣ ਦੇ ਸਮੇਂ ਸਮੇਤ ਘੱਟੋ-ਘੱਟ 5 ਸ਼ਿਫਟਾਂ ਚਾਹੀਦੀਆਂ ਹਨ। ਤੁਹਾਡੇ ਕੋਲ {n} ਹਨ।"},
    "opp_data_next": {"en": "Add today's shift with its start time.", "hi": "आज का शिफ्ट शुरू होने के समय के साथ जोड़ें।", "pa": "ਅੱਜ ਦੀ ਸ਼ਿਫਟ ਸ਼ੁਰੂ ਹੋਣ ਦੇ ਸਮੇਂ ਸਮੇਤ ਜੋੜੋ।"},
    "opp_leak_title": {"en": "Review your recurring {cat} spending", "hi": "बार-बार होने वाले {cat} खर्च की समीक्षा करें", "pa": "ਵਾਰ-ਵਾਰ ਹੋਣ ਵਾਲੇ {cat} ਖਰਚ ਦੀ ਸਮੀਖਿਆ ਕਰੋ"},
    "opp_leak_why": {
        "en": "You logged {n} small {cat} expenses totalling Rs {total}. Check whether some can be skipped or bought cheaper. This is a prompt to review, not a saving until you confirm one.",
        "hi": "आपने {n} छोटे {cat} खर्च दर्ज किए, कुल ₹{total}। देखें कि कुछ टाले या सस्ते में लिए जा सकते हैं। यह समीक्षा का सुझाव है, जब तक आप पक्का न करें यह बचत नहीं है।",
        "pa": "ਤੁਸੀਂ {n} ਛੋਟੇ {cat} ਖਰਚ ਦਰਜ ਕੀਤੇ, ਕੁੱਲ ₹{total}। ਦੇਖੋ ਕਿ ਕੁਝ ਟਾਲੇ ਜਾਂ ਸਸਤੇ ਵਿੱਚ ਲਏ ਜਾ ਸਕਦੇ ਹਨ। ਇਹ ਸਮੀਖਿਆ ਦਾ ਸੁਝਾਅ ਹੈ, ਜਦ ਤੱਕ ਤੁਸੀਂ ਪੱਕਾ ਨਾ ਕਰੋ ਇਹ ਬਚਤ ਨਹੀਂ ਹੈ।"},
    "opp_leak_next": {"en": "Open Expense Leak Finder.", "hi": "खर्च लीक खोजक खोलें।", "pa": "ਖਰਚ ਲੀਕ ਖੋਜੀ ਖੋਲ੍ਹੋ।"},
    "opp_trip_title": {"en": "Check each trip against your own average", "hi": "हर ट्रिप को अपने औसत से मिलाएँ", "pa": "ਹਰ ਟ੍ਰਿਪ ਨੂੰ ਆਪਣੇ ਔਸਤ ਨਾਲ ਮਿਲਾਓ"},
    "opp_trip_why": {
        "en": "Your logged take-home averages Rs {ph} per hour. Use the Trip Profit calculator before accepting low-fare trips.",
        "hi": "आपकी दर्ज बचत औसतन ₹{ph} प्रति घंटा है। कम किराए की ट्रिप लेने से पहले ट्रिप प्रॉफिट कैलकुलेटर इस्तेमाल करें।",
        "pa": "ਤੁਹਾਡੀ ਦਰਜ ਬਚਤ ਔਸਤਨ ₹{ph} ਪ੍ਰਤੀ ਘੰਟਾ ਹੈ। ਘੱਟ ਕਿਰਾਏ ਵਾਲੀ ਟ੍ਰਿਪ ਲੈਣ ਤੋਂ ਪਹਿਲਾਂ ਟ੍ਰਿਪ ਪ੍ਰੋਫਿਟ ਕੈਲਕੁਲੇਟਰ ਵਰਤੋ।"},
    "opp_trip_next": {"en": "Open Trip Profit.", "hi": "ट्रिप प्रॉफिट खोलें।", "pa": "ਟ੍ਰਿਪ ਪ੍ਰੋਫਿਟ ਖੋਲ੍ਹੋ।"},
    "opp_disc_title": {"en": "Review a possible missing payment of Rs {amt}", "hi": "₹{amt} के संभावित बकाया भुगतान की जाँच करें", "pa": "₹{amt} ਦੇ ਸੰਭਾਵੀ ਬਕਾਇਆ ਭੁਗਤਾਨ ਦੀ ਜਾਂਚ ਕਰੋ"},
    "opp_disc_why": {
        "en": "On {day} your {platform} payout was Rs {amt} less than the figures add up to. This is an estimate until the platform confirms it.",
        "hi": "{day} को आपका {platform} भुगतान आँकड़ों के जोड़ से ₹{amt} कम था। जब तक प्लेटफ़ॉर्म पुष्टि न करे, यह अनुमान है।",
        "pa": "{day} ਨੂੰ ਤੁਹਾਡਾ {platform} ਭੁਗਤਾਨ ਅੰਕੜਿਆਂ ਦੇ ਜੋੜ ਨਾਲੋਂ ₹{amt} ਘੱਟ ਸੀ। ਜਦ ਤੱਕ ਪਲੇਟਫਾਰਮ ਪੁਸ਼ਟੀ ਨਾ ਕਰੇ, ਇਹ ਅੰਦਾਜ਼ਾ ਹੈ।"},
    "opp_disc_next": {"en": "Open Proof-to-Action.", "hi": "प्रूफ-टू-एक्शन खोलें।", "pa": "ਪ੍ਰੂਫ-ਟੂ-ਐਕਸ਼ਨ ਖੋਲ੍ਹੋ।"},
    "opp_scheme_title": {"en": "Check whether you can register on e-Shram", "hi": "देखें कि क्या आप e-Shram पर पंजीकरण कर सकते हैं", "pa": "ਦੇਖੋ ਕੀ ਤੁਸੀਂ e-Shram ਤੇ ਰਜਿਸਟਰ ਕਰ ਸਕਦੇ ਹੋ"},
    "opp_scheme_why": {
        "en": "You have not saved any welfare scheme yet. e-Shram registration is free and open to many gig and informal workers, and other schemes link to it. Eligibility needs official confirmation.",
        "hi": "आपने अभी कोई कल्याण योजना सहेजी नहीं है। e-Shram पंजीकरण मुफ़्त है और कई गिग व अनौपचारिक कामगारों के लिए खुला है; अन्य योजनाएँ इससे जुड़ी हैं। पात्रता की सरकारी पुष्टि ज़रूरी है।",
        "pa": "ਤੁਸੀਂ ਅਜੇ ਕੋਈ ਭਲਾਈ ਯੋਜਨਾ ਸੰਭਾਲੀ ਨਹੀਂ। e-Shram ਰਜਿਸਟ੍ਰੇਸ਼ਨ ਮੁਫ਼ਤ ਹੈ ਅਤੇ ਕਈ ਗਿਗ ਤੇ ਗੈਰ-ਰਸਮੀ ਕਾਮਿਆਂ ਲਈ ਖੁੱਲ੍ਹੀ ਹੈ; ਹੋਰ ਯੋਜਨਾਵਾਂ ਇਸ ਨਾਲ ਜੁੜੀਆਂ ਹਨ। ਯੋਗਤਾ ਦੀ ਸਰਕਾਰੀ ਪੁਸ਼ਟੀ ਜ਼ਰੂਰੀ ਹੈ।"},
    "opp_scheme_next": {"en": "Open HaqFinder.", "hi": "हक़फ़ाइंडर खोलें।", "pa": "ਹੱਕਫਾਈਂਡਰ ਖੋਲ੍ਹੋ।"},
    "opp_griev_title": {"en": "Follow up on your complaint to {company}", "hi": "{company} को की गई अपनी शिकायत पर फ़ॉलो-अप करें", "pa": "{company} ਨੂੰ ਕੀਤੀ ਆਪਣੀ ਸ਼ਿਕਾਇਤ ਤੇ ਫ਼ਾਲੋ-ਅੱਪ ਕਰੋ"},
    "opp_griev_why": {
        "en": "You recorded it as submitted on {day}. If there is no reply, the next step is the platform's grievance officer.",
        "hi": "आपने इसे {day} को जमा किया दर्ज किया था। जवाब न मिले तो अगला कदम प्लेटफ़ॉर्म का शिकायत अधिकारी है।",
        "pa": "ਤੁਸੀਂ ਇਸਨੂੰ {day} ਨੂੰ ਜਮ੍ਹਾਂ ਦਰਜ ਕੀਤਾ ਸੀ। ਜਵਾਬ ਨਾ ਮਿਲੇ ਤਾਂ ਅਗਲਾ ਕਦਮ ਪਲੇਟਫਾਰਮ ਦਾ ਸ਼ਿਕਾਇਤ ਅਧਿਕਾਰੀ ਹੈ।"},
    "opp_griev_next": {"en": "Open your complaints.", "hi": "अपनी शिकायतें खोलें।", "pa": "ਆਪਣੀਆਂ ਸ਼ਿਕਾਇਤਾਂ ਖੋਲ੍ਹੋ।"},
    "disclaimer_doc": {
        "en": "AI-generated reading of a document can be wrong or incomplete. Have important documents checked by a trusted person, CSC or legal aid (NALSA 15100).",
        "hi": "दस्तावेज़ की AI-आधारित व्याख्या गलत या अधूरी हो सकती है। ज़रूरी दस्तावेज़ किसी भरोसेमंद व्यक्ति, CSC या कानूनी सहायता (NALSA 15100) से जँचवाएँ।",
        "pa": "ਦਸਤਾਵੇਜ਼ ਦੀ AI-ਆਧਾਰਿਤ ਵਿਆਖਿਆ ਗਲਤ ਜਾਂ ਅਧੂਰੀ ਹੋ ਸਕਦੀ ਹੈ। ਜ਼ਰੂਰੀ ਦਸਤਾਵੇਜ਼ ਕਿਸੇ ਭਰੋਸੇਮੰਦ ਵਿਅਕਤੀ, CSC ਜਾਂ ਕਾਨੂੰਨੀ ਸਹਾਇਤਾ (NALSA 15100) ਤੋਂ ਜਾਂਚਵਾਓ।"},
    "weather_unavailable": {"en": "Weather service is unavailable right now. No alert can be shown - check IMD or a weather app.", "hi": "मौसम सेवा अभी उपलब्ध नहीं है। कोई चेतावनी नहीं दिखाई जा सकती - IMD या मौसम ऐप देखें।", "pa": "ਮੌਸਮ ਸੇਵਾ ਹੁਣੇ ਉਪਲਬਧ ਨਹੀਂ। ਕੋਈ ਚੇਤਾਵਨੀ ਨਹੀਂ ਦਿਖਾਈ ਜਾ ਸਕਦੀ - IMD ਜਾਂ ਮੌਸਮ ਐਪ ਦੇਖੋ।"},
    "weather_heat": {"en": "Heat alert: forecast high of {t} C. Avoid 12:00-16:00, drink water every hour and rest in shade.", "hi": "गर्मी की चेतावनी: अधिकतम तापमान {t} °C का पूर्वानुमान। दोपहर 12-4 बजे से बचें, हर घंटे पानी पिएँ और छाँव में आराम करें।", "pa": "ਗਰਮੀ ਚੇਤਾਵਨੀ: ਵੱਧ ਤੋਂ ਵੱਧ ਤਾਪਮਾਨ {t} °C ਦਾ ਅਨੁਮਾਨ। ਦੁਪਹਿਰ 12-4 ਵਜੇ ਤੋਂ ਬਚੋ, ਹਰ ਘੰਟੇ ਪਾਣੀ ਪੀਓ ਅਤੇ ਛਾਂ ਵਿੱਚ ਆਰਾਮ ਕਰੋ।"},
    "weather_rain": {"en": "Rain likely ({p}% chance). Ride slowly and protect your phone and documents.", "hi": "बारिश की संभावना ({p}%)। धीरे चलाएँ और फ़ोन व कागज़ बचाएँ।", "pa": "ਬਾਰਿਸ਼ ਦੀ ਸੰਭਾਵਨਾ ({p}%)। ਹੌਲੀ ਚਲਾਓ ਅਤੇ ਫ਼ੋਨ ਤੇ ਕਾਗਜ਼ ਬਚਾਓ।"},
    "weather_ok": {"en": "No heat or rain alert in today's forecast.", "hi": "आज के पूर्वानुमान में गर्मी या बारिश की कोई चेतावनी नहीं।", "pa": "ਅੱਜ ਦੇ ਅਨੁਮਾਨ ਵਿੱਚ ਗਰਮੀ ਜਾਂ ਬਾਰਿਸ਼ ਦੀ ਕੋਈ ਚੇਤਾਵਨੀ ਨਹੀਂ।"},
}


def m(lang: str, key: str, **kw) -> str:
    d = M[key]
    s = d.get(lang) or d["en"]
    try:
        return s.format(**kw)
    except (KeyError, IndexError):
        return s
