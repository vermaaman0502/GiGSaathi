import pytest
from fastapi.testclient import TestClient

from app import guardrails, orchestrator, rag, store
from app.main import app
from app.tools import earnings, grievance, money

client = TestClient(app)


@pytest.fixture(autouse=True)
def db(tmp_path):
    store.reset_for_tests(str(tmp_path / "t.db"))


def test_real_hourly_includes_waiting():
    r = earnings.real_hourly_earnings(gross=1000, hours_worked=8, waiting_hours=2, commission=200, fuel=150, emi_per_day=50)
    assert r["net"] == 600 and r["total_hours"] == 10 and r["real_hourly"] == 60


def test_flags_unknown_deduction():
    f = earnings.flag_deductions([{"label": "misc charge", "amount": 80}, {"label": "commission", "amount": 100}], gross=1000)
    assert len(f) == 1 and "misc charge" in f[0]


def test_trip_worth_verdicts():
    assert earnings.trip_worth(fare=30, distance_km=10, time_min=30, return_km=10)["verdict"] == "skip"
    assert earnings.trip_worth(fare=200, distance_km=5, time_min=20)["verdict"] == "accept"


def test_safe_to_spend():
    r = money.safe_to_spend(30000, rent=6000, emi=3000, bills=1000, savings_pct=10)
    assert r["daily_limit"] == 566.67 and not r["shortfall"]
    assert money.safe_to_spend(5000, rent=6000)["shortfall"]


def test_loan_apr_known_value():
    # 12 monthly payments of 1000 for 10000 received -> ~ 2.92%/month ~= 35% p.a. (simple annualised)
    r = money.loan_check(10000, 1000, 12)
    assert 34 < r["yearly_interest_pct"] < 36.5 and r["total_repayment"] == 12000
    assert money.loan_check(10000, 1000, 12, upfront_fee=2000)["risk"] == "high"
    with pytest.raises(ValueError):
        money.loan_check(10000, 500, 12)


def test_leaks_and_category():
    ex = [{"category": "food", "amount": 20}] * 5 + [{"category": "fuel", "amount": 400}]
    assert money.find_leaks(ex)[0]["category"] == "food"
    assert money.categorise("petrol 200") == "fuel" and money.categorise("zzz") == "other"


def test_grievance_letter_has_evidence_and_ladder():
    d = grievance.draft("wage_due", "Ravi", "ABC Contractors", amount=3000, evidence=["wage diary 1-10 Oct"])
    assert "3000" in d["letter"] and "wage diary" in d["letter"] and len(d["ladder"]) == 5
    with pytest.raises(ValueError):
        grievance.draft("bogus", "x", "y")


def test_pii_masking_and_secrets():
    m = guardrails.mask_pii("my aadhaar 1234 5678 9012 and otp is 482913")
    assert "1234" not in m and "482913" not in m
    r = orchestrator.handle("u", "my otp 123456 how to register eshram")
    assert "never share" in r["reply"].lower()


def test_crisis_escalates():
    r = orchestrator.handle("u", "mera accident ho gaya bachao")
    assert r["escalate"] and "112" in r["reply"]


def test_rag_finds_eshram_and_refuses_unknown():
    assert rag.get_retriever().search("how do I register on e-shram")[0]["id"] == "eshram"
    r = orchestrator.handle("u", "who won the cricket world cup")
    assert "not sure" in r["reply"].lower() and r["sources"] == []


def test_scheme_match_excludes_epfo():
    ids = [m["scheme"]["id"] for m in rag.match_schemes(30, 12000, epfo_member=True)]
    assert "eshram" not in ids and "pmsym" not in ids and "pmsby" in ids


def test_chat_diary_flow():
    orchestrator.handle("w1", "aaj 850 kamaye")
    orchestrator.handle("w1", "chai 20 kharcha")
    r = orchestrator.handle("w1", "aaj ka hisab kitna")
    assert "850" in r["reply"] and "830" in r["reply"]
    assert "diary" in orchestrator.handle("w1", "contractor owes 500 baki")["reply"].lower()


def test_chat_trip_and_loan():
    assert orchestrator.handle("u", "trip fare 120 distance 8 km")["intent"] == "trip"
    r = orchestrator.handle("u", "loan 10000 emi 1000 for 12 months")
    assert r["intent"] == "loan" and "%" in r["reply"]


def test_api_endpoints():
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/").status_code == 200
    x = client.post("/api/earnings/xray", json={"gross": 1000, "hours_worked": 8, "commission": 200, "deductions": [{"label": "xyz", "amount": 50}]}).json()
    assert x["flags"]
    assert client.post("/api/loan-check", json={"principal": 10000, "emi": 500, "months": 12}).status_code == 422
    assert client.post("/api/grievance", json={"kind": "bad", "name": "a", "company": "b"}).status_code == 422
    assert client.post("/api/schemes/match", json={"age": 28, "monthly_income": 14000}).json()["matches"]


def test_whatsapp_webhook_twiml():
    r = client.post("/whatsapp", data={"Body": "Which schemes for pension?", "From": "whatsapp:+910000000000"})
    assert r.status_code == 200 and "<Message>" in r.text and "+91" not in r.text
