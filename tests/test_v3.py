import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app import schemes, store, weather
from app.main import app
from app.services import demo, earn, ledger
from app.tools import earnings as et

client = TestClient(app)


@pytest.fixture(autouse=True)
def db(tmp_path):
    store.reset_for_tests(str(tmp_path / "t.db"))


def new_user():
    return "u-" + uuid.uuid4().hex          # 34 chars


# ---------- financial calculations ----------
def test_trip_profit_numbers_and_breakeven():
    r = et.trip_worth(fare=120, distance_km=8, time_min=25, return_km=4, tolls=10, commission_pct=20, history_net_per_hour=130)
    assert r["net_profit"] == 32 and r["cost"] == 64 and r["cost_per_km"] == 5.33 and r["breakeven_fare"] == 80
    assert r["vs_history"]["better_than_average"] is False and r["assumptions"]
    # at the break-even fare, net profit is exactly zero
    z = et.trip_worth(fare=80, distance_km=8, time_min=25, return_km=4, tolls=10, commission_pct=20)
    assert z["net_profit"] == 0


def test_discrepancy_is_deterministic_and_not_called_fraud():
    s = {"gross": 1100, "incentive": 200, "commission": 220, "deductions": 40, "fuel": 0, "other_expenses": 0, "promised": 1040, "received": 880}
    d = earn.discrepancy(s)
    assert d["expected_payout"] == 1040 and d["shortfall_vs_calculated"] == 160 and d["shortfall_vs_promised"] == 160
    assert d["status"] == "possible_discrepancy"
    assert earn.discrepancy({**s, "received": 1040})["status"] == "matches"
    assert earn.discrepancy({**s, "received": None})["status"] == "unknown"
    assert earn.discrepancy({**s, "received": 1039.5})["status"] == "matches"          # rounding tolerance


def test_dashboard_numbers_from_saved_shifts():
    u = new_user()
    client.post("/api/shifts", json={"user": u, "hours": 8, "gross": 1000, "commission": 200, "fuel": 150, "other_expenses": 50})
    d = client.get(f"/api/dashboard/{u}").json()
    assert d["data_source"] == "user" and d["today"]["gross"] == 1000 and d["today"]["expenses"] == 400
    assert d["today"]["net"] == 600 and d["today"]["net_per_hour"] == 75 and len(d["series"]) == 7
    assert "600" in d["ai_summary"] and d["summary_basis"] == "computed from saved shifts"
    hi = client.get(f"/api/dashboard/{u}?lang=hi").json()["ai_summary"]
    assert "₹600" in hi
    empty = client.get(f"/api/dashboard/{new_user()}").json()
    assert empty["data_source"] == "empty" and empty["summary_basis"] == "no data"


# ---------- HaqFinder ----------
A = {"age": 28, "monthly_income": 12000, "epfo_member": False, "nps_member": False, "income_tax_payer": False,
     "govt_pension": False, "has_bank": True, "state": "punjab", "work_type": "delivery", "street_vendor": False}


def state_of(sid, answers, lang="en"):
    return next(c for c in schemes.match(answers, lang) if c["id"] == sid)


def test_scheme_states():
    assert state_of("pmsym", A)["state"] == "potentially_relevant"
    assert state_of("pmsym", {**A, "monthly_income": 20000})["state"] == "appears_ineligible"
    assert state_of("pmsym", {**A, "age": 45})["state"] == "appears_ineligible"
    assert state_of("pmsym", {**A, "nps_member": True})["state"] == "appears_ineligible"
    assert state_of("pmsym", {**A, "govt_pension": True})["state"] == "appears_ineligible"
    assert state_of("pmsym", {**A, "epfo_member": None})["state"] == "more_info_needed"
    assert state_of("eshram", {**A, "income_tax_payer": True})["state"] == "appears_ineligible"
    assert state_of("pmjay", A)["state"] == "requires_official_confirmation"         # never auto-confirmed
    assert state_of("state_gig_laws", {**A, "state": "karnataka"})["state"] == "requires_official_confirmation"
    assert state_of("state_gig_laws", A)["state"] == "appears_ineligible"            # Punjab: no state gig law found
    assert state_of("svanidhi", {**A, "street_vendor": True})["state"] == "requires_official_confirmation"
    assert state_of("bocw", {**A, "work_type": "construction", "age": 35})["state"] == "requires_official_confirmation"


def test_scheme_cards_have_required_fields_and_honest_verification():
    for c in schemes.match(A, "en"):
        for f in ("title", "authority", "benefits", "exclusions", "documents", "steps", "apply_url", "sources", "state", "state_label", "why_qualify", "missing"):
            assert f in c, (c["id"], f)
        assert c["sources"] and all(s["url"].startswith("http") for s in c["sources"])
    cards = {c["id"]: c for c in schemes.match(A, "en")}
    assert cards["eshram"]["last_verified"] == "2026-10-17" and cards["eshram"]["verification"] == "verified"
    assert cards["apy"]["last_verified"] is None and cards["apy"]["verification"] == "unverified_seed"   # not claimed as verified


def test_adaptive_questionnaire_asks_only_what_is_needed():
    all_q = [q["id"] for q in schemes.next_questions({})]
    assert all_q[:3] == ["state", "age", "work_type"]
    after = [q["id"] for q in schemes.next_questions({"age": 50})]
    assert "monthly_income" not in after            # PM-SYM already ruled out by age; nobody else needs income
    assert schemes.next_questions(A) == []


def test_scheme_text_in_hindi_and_punjabi():
    hi = schemes.view(schemes.get("pmsym"), "hi")
    pa = schemes.view(schemes.get("pmsym"), "pa")
    assert hi["text_language"] == "hi" and "पेंशन" in hi["title"]
    assert pa["text_language"] == "pa" and "ਪੈਨਸ਼ਨ" in pa["title"]
    assert schemes.view(schemes.get("pmsym"), "ta")["text_language"] == "en"


def test_haq_api_and_tracker_user_recorded_only():
    u = new_user()
    r = client.post("/api/haq/match", json={"answers": {"age": 30}, "lang": "hi"}).json()
    assert r["cards"] and r["next_questions"]
    t = client.post("/api/haq/track", json={"user": u, "scheme_id": "eshram", "reminder": (date.today() + timedelta(days=2)).isoformat()}).json()["tracker"]["eshram"]
    assert t["status"] == "saved" and "does not submit" in t["note"] and "Aadhaar" in t["checklist"]
    client.post("/api/haq/track", json={"user": u, "scheme_id": "eshram", "status": "applied", "checklist": {"Aadhaar": True}})
    t = client.get(f"/api/haq/track/{u}").json()["tracker"]["eshram"]
    assert t["status"] == "applied" and t["checklist"]["Aadhaar"] is True
    assert client.post("/api/haq/track", json={"user": u, "scheme_id": "eshram", "status": "teleported"}).status_code == 422
    assert client.post("/api/haq/track", json={"user": u, "scheme_id": "nope"}).status_code == 404
    imp = client.get(f"/api/impact/{u}").json()
    assert imp["counts"]["scheme_discovered"] == 1 and imp["counts"]["application_started"] == 1
    assert imp["money"] == {"verified": 0, "user_reported": 0, "estimated": 0}       # discovering/applying is never money


# ---------- Proof-to-Action ----------
def test_proof_to_action_full_journey():
    u = new_user()
    body = {"user": u, "day": date.today().isoformat(), "platform": "SwiftEats", "hours": 7, "gross": 1100, "commission": 220, "deductions": 40, "incentive": 200,
            "promised": 1040, "received": 880, "lang": "en", "create_grievance": True, "name": "Ravi", "company": "SwiftEats"}
    r = client.post("/api/proof-to-action", json=body).json()
    assert r["calculation"]["shortfall_vs_calculated"] == 160 and r["explanation"]["code"] == "possible_discrepancy"
    assert "not proof" in r["explanation"]["message"] and "not proof" in r["explanation"]["disclaimer"]
    assert r["grievance"]["status"] == "draft" and "160" in r["grievance"]["letter"] and r["evidence"] and r["next_step"]["ladder_step"] == "platform_support"
    gid = r["grievance"]["id"]
    # draft is separate from submission; statuses are user-recorded
    g = client.patch(f"/api/grievances/{gid}", json={"user": u, "status": "ready"}).json()
    assert g["status"] == "ready" and g["follow_ups"] == []
    g = client.patch(f"/api/grievances/{gid}", json={"user": u, "status": "submitted"}).json()
    assert g["submitted_on"] == date.today().isoformat() and len(g["follow_ups"]) == 3 and "does not submit" in g["note"]
    assert client.patch(f"/api/grievances/{gid}", json={"user": u, "status": "won"}).status_code == 422
    client.patch(f"/api/grievances/{gid}", json={"user": u, "status": "resolved"})
    imp = client.get(f"/api/impact/{u}").json()
    assert imp["counts"]["complaint_submitted"] == 1 and imp["counts"]["complaint_resolved"] == 1
    assert imp["money"]["estimated"] == 160 and imp["money"]["user_reported"] == 0      # estimate is NOT money received


def test_proof_no_discrepancy_and_unknown_and_validation():
    u = new_user()
    ok = client.post("/api/proof-to-action", json={"user": u, "gross": 500, "commission": 100, "received": 400, "save": False}).json()
    assert ok["explanation"]["code"] == "no_discrepancy" and ok["grievance"] is None
    unk = client.post("/api/proof-to-action", json={"user": u, "gross": 500, "save": False}).json()
    assert unk["explanation"]["code"] == "insufficient_data"
    assert client.post("/api/proof-to-action", json={"user": u, "gross": -5}).status_code == 422
    need = client.post("/api/proof-to-action", json={"user": u, "gross": 500, "received": 100, "create_grievance": True})
    assert need.status_code == 422                                    # complaint needs name + company
    hi = client.post("/api/proof-to-action", json={"user": u, "gross": 500, "received": 100, "lang": "hi", "save": False}).json()
    assert "संभावित" in hi["explanation"]["message"]


# ---------- Impact ledger honesty ----------
def test_impact_ledger_separates_basis_and_blocks_verified():
    u = new_user()
    assert client.post("/api/impact", json={"user": u, "kind": "extra_payment", "amount": 300, "basis": "verified"}).status_code == 422
    client.post("/api/impact", json={"user": u, "kind": "extra_payment", "amount": 300, "basis": "user_reported"})
    client.post("/api/impact", json={"user": u, "kind": "expense_avoided", "amount": 100, "basis": "estimated"})
    client.post("/api/impact", json={"user": u, "kind": "scheme_discovered", "amount": 5000, "basis": "user_reported"})   # amount must be ignored
    s = client.get(f"/api/impact/{u}").json()
    assert s["money"] == {"verified": 0, "user_reported": 300, "estimated": 100}
    assert s["counts"]["scheme_discovered"] == 1
    assert client.post("/api/impact", json={"user": u, "kind": "lottery", "amount": 1, "basis": "estimated"}).status_code == 422


# ---------- demo mode ----------
def test_demo_seed_is_reserved_and_labelled():
    assert client.post(f"/api/demo/seed/{new_user()}").status_code == 422          # real ids can't be seeded
    d = "demo-" + uuid.uuid4().hex[:8]
    assert client.post(f"/api/demo/seed/{d}").json()["demo"] is True
    dash = client.get(f"/api/dashboard/{d}").json()
    assert dash["data_source"] == "demo" and dash["week"]["gross"] > 0
    assert client.get(f"/api/impact/{d}").json()["data_source"] == "demo"
    assert all(s["source"] == "demo" for s in client.get(f"/api/shifts/{d}").json()["shifts"])
    p = client.get("/api/demo/payout-sample").json()
    assert p["demo"] and client.post("/api/extract/payout-text", json={"text": p["text"]}).json()["fields"]["received"] == 880
    seeded_again = client.post(f"/api/demo/seed/{d}")
    assert seeded_again.status_code == 200
    assert len(client.get(f"/api/shifts/{d}").json()["shifts"]) == 15               # re-seeding does not duplicate
    assert store.q("SELECT COUNT(*) AS n FROM shifts WHERE is_demo=0")[0]["n"] == 0


# ---------- extraction & documents ----------
def test_payout_text_parser_and_incentive_parser():
    txt = "Weekly payout\nDate: 12 Oct 2026\nTotal earnings: Rs 2,450\nPlatform fee 490\nPeak bonus 300\nPenalty late 50\nGST 20\nOnline hours 31\nNet payout 2,190"
    f = client.post("/api/extract/payout-text", json={"text": txt}).json()
    assert f["needs_review"] and f["fields"]["gross"] == 2450 and f["fields"]["commission"] == 490 and f["fields"]["incentive"] == 300
    assert f["fields"]["received"] == 2190 and f["fields"]["hours"] == 31 and len(f["fields"]["deductions"]) == 2
    assert client.post("/api/extract/payout-text", json={"text": "hello world"}).json()["confidence"] == "low"
    inc = client.post("/api/incentive/parse", json={"text": "Complete 25 trips by Sunday 11 PM and earn Rs 500 bonus"}).json()
    assert inc["target_trips"] == 25 and inc["reward"] == 500 and "sunday" in inc["deadline_text"] and inc["needs_review"]
    pr = client.post("/api/incentive/progress", json={"trips_done": 10, "target_trips": 25, "reward": 500, "hours_left": 5, "lang": "en"}).json()
    assert pr["rem"] == 15 and pr["per_hr"] == 3.0


def test_document_analyze_extracts_and_flags():
    text = ("LOAN AGREEMENT. The borrower shall repay Rs 12,000 in 12 EMIs of Rs 1,500. A processing fee of Rs 500 applies. "
            "Interest is 4% per month. A penalty of Rs 200 is charged for late payment. Pay within 10 days of 01/11/2026. The lender may terminate without notice.")
    r = client.post("/api/document/analyze", json={"text": text, "lang": "en"}).json()
    assert r["doc_type"] == "loan_agreement" and 12000 in r["amounts"] and 1500 in r["amounts"] and r["dates"]
    assert r["deadlines"] and r["fees"] and r["obligations"] and r["checklist"]
    assert {x["key"] for x in r["risks"]} >= {"risk_interest", "risk_penalty", "risk_terminate"}
    assert r["ai_summary"] is None and r["ai_summary_available"] is False          # no key: not faked
    assert "professional" in r["disclaimer"] or "NALSA" in r["disclaimer"]
    assert client.post("/api/extract/payout-image", json={"image_b64": "AAAA"}).json()["available"] is False


# ---------- opportunities ----------
def test_opportunities_need_data_then_use_it():
    u = new_user()
    items = {i["category"]: i for i in client.get(f"/api/opportunities/{u}").json()["items"]}
    assert set(items) == {"earn_more", "save_money"} | {"rights_benefits"} or set(items) == {"earn_more", "rights_benefits"}
    assert items["earn_more"]["confidence"] == "none" and items["earn_more"]["impact"] is None      # no invented prediction
    for i in range(10):                                         # evening shifts much better than morning
        evening = i % 2 == 0
        client.post("/api/shifts", json={"user": u, "day": (date.today() - timedelta(days=i)).isoformat(), "hours": 5, "start_hour": 19 if evening else 9,
                                         "gross": 900 if evening else 400, "commission": 100})
    items = {i["category"]: i for i in client.get(f"/api/opportunities/{u}").json()["items"]}
    e = items["earn_more"]
    assert "18:00-21:00" in e["title"] and e["confidence"] == "medium" and e["impact"]["basis"] == "estimated" and e["evidence"] and e["next"]["href"]
    assert "guarantee" in e["why"]
    d = "demo-" + uuid.uuid4().hex[:8]
    client.post(f"/api/demo/seed/{d}")
    cats = {i["category"]: i for i in client.get(f"/api/opportunities/{d}").json()["items"]}
    assert cats["rights_benefits"]["impact"]["basis"] == "estimated" and "not money received" in cats["rights_benefits"]["impact"]["note"]
    assert cats["save_money"]["impact"]["basis"] == "estimated"


def test_shift_insights_ranges_only_with_enough_data():
    u = new_user()
    s = client.get(f"/api/shift-insights/{u}").json()
    assert s["enough_data"] is False and s["generic"] and "Not enough data" in s["note"]
    for i in range(6):
        client.post("/api/shifts", json={"user": u, "day": (date.today() - timedelta(days=i)).isoformat(), "hours": 4, "start_hour": 18, "gross": 600 + i * 10})
    s = client.get(f"/api/shift-insights/{u}").json()
    assert s["enough_data"] and s["bands"][0]["show_range"] and s["bands"][0]["min"] <= s["bands"][0]["avg"] <= s["bands"][0]["max"] and s["generic"] is None


def test_platform_comparison_and_wage_diary_export():
    u = new_user()
    for plat, g in [("a", 800), ("b", 500)]:
        client.post("/api/shifts", json={"user": u, "platform": plat, "hours": 5, "gross": g, "commission": 100})
    c = client.get(f"/api/compare/platforms/{u}").json()
    assert c["enough_data"] and c["platforms"][0]["platform"] == "a" and "no live connection" in c["note"]
    client.post("/api/wage-diary", json={"user": u, "employer": "X", "work": "mason", "hours": 8, "promised": 700, "received": 500})
    assert client.get(f"/api/wage-diary/{u}").json()["unpaid_total"] == 200
    csv_text = client.get(f"/api/export/{u}.csv").text
    assert "wage_diary" in csv_text and "shift" in csv_text and csv_text.count("\n") >= 4


# ---------- weather: honest when unavailable ----------
def test_weather_never_fabricates(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("offline")
    monkeypatch.setattr(weather.httpx, "get", boom)
    w = client.get("/api/weather?lat=30.9&lon=75.8&lang=en").json()
    assert w["available"] is False and "unavailable" in w["message"] and "temp_max_c" not in w

    class R:
        def raise_for_status(self): pass
        def json(self): return {"daily": {"temperature_2m_max": [43.2], "precipitation_probability_max": [10]}}
    monkeypatch.setattr(weather.httpx, "get", lambda *a, **k: R())
    w = client.get("/api/weather?lat=30.9&lon=75.8&lang=hi").json()
    assert w["available"] and w["heat_alert"] and "43.2" in w["message"]


# ---------- privacy ----------
def test_user_id_validation_export_and_deletion():
    assert client.get("/api/dashboard/short").status_code == 422
    assert client.get("/api/dashboard/has spaces and ../").status_code in (404, 422)
    u = new_user()
    client.post("/api/shifts", json={"user": u, "hours": 4, "gross": 300})
    client.post("/api/wage-diary", json={"user": u, "promised": 100})
    other = new_user()
    client.post("/api/shifts", json={"user": other, "hours": 4, "gross": 111})
    exp = client.get(f"/api/user/{u}/export").json()
    assert len(exp["shifts"]) == 1 and len(exp["wage_diary"]) == 1
    deleted = client.delete(f"/api/user/{u}").json()["deleted_rows"]
    assert deleted["shifts"] == 1 and deleted["wage_diary"] == 1
    assert client.get(f"/api/shifts/{u}").json()["shifts"] == []
    assert len(client.get(f"/api/shifts/{other}").json()["shifts"]) == 1                # others untouched
    assert client.get("/health").json()["status"] == "ok"
