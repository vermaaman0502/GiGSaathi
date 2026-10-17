import json
import re
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import i18n, orchestrator, store
from app.main import app
from app.tools import docs, planner, practice

client = TestClient(app)
LOCALES = Path(__file__).resolve().parent.parent / "app" / "locales"
PH = re.compile(r"\{(\w+)\}")


@pytest.fixture(autouse=True)
def db(tmp_path):
    store.reset_for_tests(str(tmp_path / "t.db"))


def test_twelve_languages_complete_and_consistent():
    en = json.loads((LOCALES / "en.json").read_text(encoding="utf-8"))
    codes = sorted(p.stem for p in LOCALES.glob("*.json"))
    assert len(codes) == 12
    for c in codes:
        d = json.loads((LOCALES / f"{c}.json").read_text(encoding="utf-8"))
        assert set(d) == set(en), f"{c}: key mismatch {set(en) ^ set(d)}"
        for k in en:
            assert sorted(PH.findall(d[k])) == sorted(PH.findall(en[k])), f"{c}.{k} placeholders differ"
            assert d[k].strip(), f"{c}.{k} empty"


def test_emergency_numbers_present_in_every_language():
    for c in i18n.languages():
        for key in ("sos", "crisis"):
            msg = i18n.t(c, key)
            assert "112" in msg and "108" in msg and "15100" in msg, f"{c}.{key}"


def test_detect_language():
    assert i18n.detect("मुझे पेंशन चाहिए") == "hi"
    assert i18n.detect("எனக்கு உதவி வேண்டும்") == "ta"
    assert i18n.detect("আমার সাহায্য দরকার") == "bn"
    assert i18n.detect("aaj ka hisab batao") == "hinglish"
    assert i18n.detect("which schemes can I get") == "en"
    assert i18n.detect("hello", "te") == "te"          # explicit choice wins
    assert i18n.detect("hello", "xx") == "en"          # unknown falls back


@pytest.mark.parametrize("lang", sorted(i18n.languages()))
def test_chat_replies_in_selected_language(lang):
    r = orchestrator.handle("u", "trip fare 120 distance 8 km", lang)
    assert r["lang"] == lang and r["intent"] == "trip"
    assert i18n.t(lang, "v_accept") in r["reply"] or i18n.t(lang, "v_marginal") in r["reply"] or i18n.t(lang, "v_skip") in r["reply"]


def test_crisis_in_native_scripts():
    for text, lang in [("मेरा दुर्घटना हो गया", "hi"), ("আমাকে বাঁচাও", "bn"), ("காப்பாற்று", "ta"), ("ਬਚਾਓ", "pa"), ("ବଞ୍ଚାଅ", "or")]:
        r = orchestrator.handle("u", text, "auto")
        assert r["escalate"] and r["lang"] == lang and "112" in r["reply"]


def test_native_script_keywords_route_to_intents():
    assert orchestrator.handle("u", "ખર્ચ 50 ચા", "gu")["intent"] == "expense"
    assert orchestrator.handle("u", "செலவு 40 டீ", "ta")["intent"] == "expense"


def test_api_languages_and_ui_strings():
    langs = client.get("/api/languages").json()["languages"]
    assert [l["code"] for l in langs][0] == "en" and len(langs) == 12
    ui = client.get("/api/i18n/ta").json()
    assert ui["t_chat"] == "உரையாடல்" and "_name" not in ui
    assert client.get("/api/i18n/zz").json()["t_chat"] == "Chat"   # fallback to English


def test_api_messages_are_translated():
    body = {"gross": 1000, "hours_worked": 8, "commission": 200, "fuel": 150, "deductions": [{"label": "misc", "amount": 50}]}
    en = client.post("/api/earnings/xray", json={**body, "lang": "en"}).json()
    hi = client.post("/api/earnings/xray", json={**body, "lang": "hi"}).json()
    assert "You keep" in en["message"] and "आपके पास" in hi["message"]
    assert en["flags"] and "misc" in hi["flags"][0]
    assert client.post("/api/loan-check", json={"principal": 10000, "emi": 1000, "months": 12, "lang": "mr"}).json()["message"].startswith("तुम्हाला")


def test_shift_planner_rain_and_heat():
    p = planner.shift_plan("food", "clear")
    assert len(p["windows"]) == 2 and 19 <= p["windows"][0]["start"] <= 20 or p["windows"][0]["start"] == 12
    hot = planner.shift_plan("food", "hot")
    assert "tip_heat" in hot["tips"] and all(not (12 <= w["start"] < 16) for w in hot["windows"][:1])
    r = client.post("/api/shift-planner", json={"work_type": "ride", "weather": "rain", "festival": True, "lang": "hi"}).json()
    assert r["message"] and len(r["tips"]) == 3


def test_fatigue_and_incentive():
    assert planner.fatigue_level(12, 4, 42) == "fatigue_high"
    assert planner.fatigue_level(5, 8) == "fatigue_low"
    assert client.post("/api/fatigue", json={"hours_worked": 12, "hours_slept": 4, "temp_c": 41, "lang": "hi"}).json()["level"] == "high"
    done = client.post("/api/incentive", json={"trips_done": 20, "trips_target": 20, "bonus": 300, "hours_left": 2}).json()
    assert "300" in done["message"] and done["rem"] == 0
    far = client.post("/api/incentive", json={"trips_done": 1, "trips_target": 20, "bonus": 300, "hours_left": 2}).json()
    assert far["per_hr"] == 9.5


def test_document_scan_flags_risky_clauses():
    text = "The company may terminate your ID without notice. A penalty of Rs 500 applies. Interest is 5% per month."
    found = {f["key"] for f in docs.scan(text)}
    assert {"risk_terminate", "risk_penalty", "risk_interest"} <= found
    r = client.post("/api/document/scan", json={"text": text, "lang": "hi"}).json()
    assert len(r["risks"]) >= 3 and r["message"] == i18n.t("hi", "doc_hdr")
    assert client.post("/api/document/scan", json={"text": "Thank you for working with us."}).json()["risks"] == []


def test_vault_expiry_statuses():
    today = date.today()
    for dt, delta in [("dl", -5), ("rc", 10), ("puc", 200)]:
        client.post("/api/vault", json={"user": "v1", "doc_type": dt, "expiry": (today + timedelta(days=delta)).isoformat()})
    items = {i["doc_type"]: i for i in client.get("/api/vault/v1?lang=hi").json()["items"]}
    assert items["dl"]["status"] == "vault_expired" and items["rc"]["status"] == "vault_soon" and items["puc"]["status"] == "vault_ok"
    assert client.post("/api/vault", json={"user": "v1", "doc_type": "bogus", "expiry": "2030-01-01"}).status_code == 422
    assert client.post("/api/vault", json={"user": "v1", "doc_type": "dl", "expiry": "not-a-date"}).status_code == 422
    assert client.get("/api/vault/other-user").json()["items"] == []     # isolation between users


def test_collective_voice_k_anonymity():
    body = {"company": "FastBite", "issue": "unpaid incentives", "city": "Pune", "lang": "en"}
    g = client.post("/api/collective/report", json=body).json()["groups"][0]
    assert g["count"] == 1 and g["petition"] is None
    client.post("/api/collective/report", json=body)
    g = client.post("/api/collective/report", json={**body, "lang": "hi"}).json()["groups"][0]
    assert g["count"] == 3 and "Fastbite" in g["petition"] and "कामगार" in g["petition"]
    cols = [r[1] for r in store._db().execute("PRAGMA table_info(reports)")]
    assert "user" not in cols                                           # anonymity enforced in schema


def test_practice_mode_flow():
    sc = client.get("/api/practice/scenarios?lang=hi").json()["scenarios"]
    assert len(sc) == 3
    s = client.post("/api/practice/start", json={"scenario": "contractor_wages", "lang": "hinglish"}).json()
    assert s["npc"].startswith("Thekedar")
    step = client.post("/api/practice/step", json={"scenario": "contractor_wages", "step": 0, "answer": "Please pay my Rs 3000, I will keep a date in my diary", "lang": "en"}).json()
    assert step["feedback"]["score"] >= 2 and not step["done"]
    last = client.post("/api/practice/step", json={"scenario": "contractor_wages", "step": 1, "answer": "I will complain to the labour department", "lang": "en"}).json()
    assert last["done"]
    assert client.post("/api/practice/start", json={"scenario": "nope", "lang": "en"}).status_code == 404
    assert practice.start("police_stop", "ta")["npc"].startswith("Officer")   # English fallback


def test_side_income_diary_and_leaks_endpoints():
    assert len(client.get("/api/side-income?work_type=driver").json()["ideas"]) == 3
    orchestrator.handle("d1", "contractor owes 500 baki", "en")
    assert client.get("/api/diary/d1").json()["total_due"] == 500
    for _ in range(5):
        orchestrator.handle("d1", "chai 20 kharcha", "en")
    assert client.get("/api/money/leaks/d1").json()["leaks"][0]["category"] == "food"


def test_whatsapp_replies_in_detected_script():
    r = client.post("/whatsapp", data={"Body": "मुझे पेंशन स्कीम बताओ", "From": "whatsapp:+910000000001"})
    assert r.status_code == 200 and "<Message>" in r.text and "पेंशन" in r.text and "Source" not in r.text


def test_grievance_letter_hindi_and_note():
    body = {"kind": "wage_due", "name": "Ravi", "company": "ABC", "amount": 3000, "evidence": ["diary"]}
    hi = client.post("/api/grievance", json={**body, "lang": "hi"}).json()
    assert "बकाया" in hi["letter_local"] and "3000" in hi["letter_local"] and "diary" in hi["letter_local"]
    assert "Respectfully" in hi["letter"] and hi["message"] == i18n.t("hi", "letter_note")
    ta = client.post("/api/grievance", json={**body, "lang": "ta"}).json()
    assert "letter_local" not in ta and ta["message"] == i18n.t("ta", "letter_note")


def test_reply_language_follows_message_language_not_ui_language():
    # UI is Tamil, but the worker typed Hindi -> Hindi reply; typed English -> English reply
    r = orchestrator.handle("u", "मुझे पेंशन स्कीम बताओ", "auto", "ta")
    assert r["lang"] == "hi"
    r = orchestrator.handle("u", "trip fare 120 distance 8 km", "auto", "ta")
    assert r["lang"] == "en" and "Verdict" in r["reply"]
    r = orchestrator.handle("u", "ஓய்வூதியம் பற்றி சொல்லுங்கள்", "auto", "hi")
    assert r["lang"] == "ta"
    assert orchestrator.handle("u", "250", "auto", "pa")["lang"] == "pa"       # no letters -> UI language


def test_hindi_question_gets_hindi_only_reply():
    r = orchestrator.handle("u", "₹120 किराया 8 km ट्रिप", "auto")
    assert r["lang"] == "hi"
    assert not re.search(r"[A-Za-z]{4,}", re.sub(r"https?://\S+|PM-\w+|SHG|MUDRA|EMI|CSC|NALSA|e-Shram", "", r["reply"]))


def test_marathi_vs_hindi_and_unsupported_script():
    assert i18n.detect("मला पेन्शन योजना हवी आहे") == "mr"
    assert i18n.detect("مجھے پنشن چاہیے") == "ur"
    assert orchestrator.handle("u", "مجھے پنشن چاہیے")["lang"] == "ur"       # detected; templates fall back to English


def test_chip_phrases_in_hindi_and_punjabi_route_correctly():
    r = orchestrator.handle("u", "ट्रिप किराया 120 दूरी 8 km")
    assert r["intent"] == "trip" and r["lang"] == "hi" and "120" in r["reply"]
    r = orchestrator.handle("u", "ਟ੍ਰਿਪ ਕਿਰਾਇਆ 120 ਦੂਰੀ 8 km")
    assert r["intent"] == "trip" and r["lang"] == "pa"
    assert orchestrator.handle("u", "आज 850 रुपये कमाया")["intent"] == "income"
    assert orchestrator.handle("u", "ਅੱਜ 850 ਕਮਾਏ")["intent"] == "income"
    r = orchestrator.handle("u", "लोन 10000 emi 1200 for 12 महीने")
    assert r["intent"] == "loan" and r["lang"] == "hi"
    r = orchestrator.handle("u", "ਕਰਜ਼ਾ 10000 emi 1200 for 12 ਮਹੀਨੇ")
    assert r["intent"] == "loan" and r["lang"] == "pa"
