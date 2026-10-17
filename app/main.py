import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional
from xml.sax.saxutils import escape

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from . import i18n, orchestrator, rag, store
from .tools import community, docs, earnings, grievance, money, planner, practice

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

app = FastAPI(title="GigSaathi", version="0.2.0",
              description="Multilingual GenAI assistant for gig and informal workers: earnings, money, safety, rights, documents, grievances.")


def _hhmm(h: int) -> str:
    return f"{h % 24:02d}:00"


# ---------- request models ----------
class Base(BaseModel):
    lang: str = "en"


class ChatIn(Base):
    user: str = Field(..., description="Opaque user id (e.g. hashed phone)")
    text: str = Field(..., max_length=2000)
    lang: str = "auto"


class XRayIn(Base):
    gross: float = Field(..., ge=0)
    hours_worked: float = Field(..., gt=0)
    waiting_hours: float = Field(0, ge=0)
    commission: float = Field(0, ge=0)
    fuel: float = Field(0, ge=0)
    emi_per_day: float = Field(0, ge=0)
    other_costs: float = Field(0, ge=0)
    deductions: List[Dict] = []


class TripIn(Base):
    fare: float = Field(..., ge=0)
    distance_km: float = Field(..., ge=0)
    time_min: float = Field(..., gt=0)
    return_km: float = Field(0, ge=0)
    mileage_kmpl: float = Field(40, gt=0)
    fuel_price: float = Field(100, gt=0)
    commission_pct: float = Field(0, ge=0, le=100)


class SafeIn(Base):
    expected_monthly_income: float = Field(..., ge=0)
    rent: float = Field(0, ge=0)
    emi: float = Field(0, ge=0)
    bills: float = Field(0, ge=0)
    savings_pct: float = Field(10, ge=0, le=100)
    spent_today: float = Field(0, ge=0)


class LoanIn(Base):
    principal: float = Field(..., gt=0)
    emi: float = Field(..., gt=0)
    months: int = Field(..., gt=0)
    upfront_fee: float = Field(0, ge=0)


class GrievanceIn(Base):
    kind: str
    name: str
    company: str
    details: str = ""
    amount: float = 0
    incident_date: Optional[str] = None
    evidence: List[str] = []


class SchemeIn(Base):
    age: int = Field(..., ge=14, le=100)
    monthly_income: float = Field(..., ge=0)
    epfo_member: bool = False
    has_bank: bool = True
    income_tax_payer: bool = False
    street_vendor: bool = False


class ShiftIn(Base):
    work_type: str = "food"
    weather: str = "clear"
    festival: bool = False


class FatigueIn(Base):
    hours_worked: float = Field(..., ge=0)
    hours_slept: float = Field(..., ge=0)
    temp_c: float = 30


class IncentiveIn(Base):
    trips_done: int = Field(..., ge=0)
    trips_target: int = Field(..., gt=0)
    bonus: float = Field(0, ge=0)
    hours_left: float = Field(..., ge=0)


class AppsIn(Base):
    apps: List[Dict]


class DocScanIn(Base):
    text: str = Field(..., max_length=20000)


class VaultIn(Base):
    user: str
    doc_type: str
    expiry: str


class ReportIn(Base):
    company: str = Field(..., max_length=80)
    issue: str = Field(..., max_length=120)
    city: str = Field(..., max_length=60)


class PracticeStartIn(Base):
    scenario: str


class PracticeStepIn(Base):
    scenario: str
    step: int
    answer: str = Field(..., max_length=1000)


# ---------- pages & meta ----------
@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}


@app.get("/api/languages")
def languages():
    return {"languages": [{"code": c, "name": n, "speech": i18n.SPEECH.get(c, "en-IN")} for c, n in i18n.languages().items()]}


@app.get("/api/i18n/{lang}")
def ui_strings(lang: str):
    return i18n.ui(lang)


# ---------- chat & channels ----------
@app.post("/chat")
def chat(b: ChatIn):
    return orchestrator.handle(b.user, b.text, b.lang)


@app.post("/whatsapp", include_in_schema=False)
def whatsapp(Body: str = Form(""), From: str = Form("unknown")):
    """Twilio WhatsApp webhook (form-encoded). Replies in TwiML, language auto-detected."""
    uid = hashlib.sha256(From.encode()).hexdigest()[:16]  # store a hash, not the phone number
    out = orchestrator.handle(uid, Body, "auto")
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escape(out["reply"])}</Message></Response>'
    return Response(content=xml, media_type="application/xml")


# ---------- earn ----------
@app.post("/api/earnings/xray")
def xray(b: XRayIn):
    r = earnings.real_hourly_earnings(b.gross, b.hours_worked, b.waiting_hours, b.commission, b.fuel, b.emi_per_day, b.other_costs)
    flags = []
    for d in b.deductions:
        label = str(d.get("label", "")).strip().lower()
        if label not in earnings.EXPECTED_DEDUCTIONS:
            flags.append(i18n.t(b.lang, "flag_unknown", label=d.get("label"), amt=i18n.fmt(float(d.get("amount", 0)))))
    total_ded = sum(float(d.get("amount", 0)) for d in b.deductions) + b.commission
    if b.gross > 0 and total_ded / b.gross * 100 > 25:
        flags.append(i18n.t(b.lang, "flag_total", pct=round(total_ded / b.gross * 100)))
    r["flags"] = flags
    r["message"] = i18n.t(b.lang, "xray", net=i18n.fmt(r["net"]), gross=i18n.fmt(r["gross"]), hourly=i18n.fmt(r["real_hourly"]), hours=i18n.fmt(r["total_hours"]))
    return r


@app.post("/api/trip-worth")
def trip(b: TripIn):
    d = b.model_dump(exclude={"lang"})
    r = earnings.trip_worth(**d)
    r["message"] = i18n.t(b.lang, "trip", fare=i18n.fmt(b.fare), km=i18n.fmt(b.distance_km), net=i18n.fmt(r["net_profit"]),
                          hourly=i18n.fmt(r["net_per_hour"]), verdict=i18n.t(b.lang, "v_" + r["verdict"]))
    return r


@app.post("/api/shift-planner")
def shift(b: ShiftIn):
    p = planner.shift_plan(b.work_type, b.weather, b.festival)
    w = p["windows"]
    w2 = f"{_hhmm(w[1]['start'])}-{_hhmm(w[1]['end'])}" if len(w) > 1 else "-"
    p["message"] = i18n.t(b.lang, "shift", w1=f"{_hhmm(w[0]['start'])}-{_hhmm(w[0]['end'])}", w2=w2)
    p["tips"] = [i18n.t(b.lang, k) for k in p["tips"]]
    return p


@app.post("/api/incentive")
def incentive(b: IncentiveIn):
    r = planner.incentive(b.trips_done, b.trips_target, b.hours_left)
    r["message"] = i18n.t(b.lang, r.pop("key"), rem=r["rem"], bonus=i18n.fmt(b.bonus), per_hr=r["per_hr"], hours=i18n.fmt(b.hours_left))
    return r


@app.post("/api/compare-apps")
def compare(b: AppsIn):
    r = earnings.compare_apps(b.apps)
    if not r:
        raise HTTPException(422, "provide at least one app with hours > 0")
    return r


@app.get("/api/side-income")
def side_income(work_type: str = "delivery"):
    data = json.loads((ROOT / "data" / "side_income.json").read_text(encoding="utf-8"))
    return {"note": data["note"], "ideas": data.get(work_type, [])}


# ---------- money ----------
@app.post("/api/safe-to-spend")
def safe(b: SafeIn):
    r = money.safe_to_spend(**b.model_dump(exclude={"lang"}))
    r["message"] = i18n.t(b.lang, "safe_short" if r["shortfall"] else "safe", limit=i18n.fmt(r["daily_limit"]), left=i18n.fmt(r["left_today"]),
                          fixed=i18n.fmt(r["fixed_monthly"]), sav=i18n.fmt(r["savings_monthly"]))
    return r


@app.post("/api/loan-check")
def loan(b: LoanIn):
    try:
        r = money.loan_check(**b.model_dump(exclude={"lang"}))
    except ValueError as e:
        raise HTTPException(422, str(e))
    r["message"] = i18n.t(b.lang, "loan", recv=i18n.fmt(r["money_received"]), total=i18n.fmt(r["total_repayment"]),
                          pct=r["yearly_interest_pct"], risk=i18n.t(b.lang, "r_" + r["risk"]))
    return r


@app.get("/api/money/summary/{user}")
def money_summary(user: str, lang: str = "en"):
    s = store.daily_summary(user)
    s["message"] = i18n.t(lang, "summary", earned=i18n.fmt(s["earned"]), spent=i18n.fmt(s["spent"]), saved=i18n.fmt(s["saved"]))
    return s


@app.get("/api/money/leaks/{user}")
def money_leaks(user: str):
    return {"leaks": money.find_leaks(store.monthly_totals(user))}


@app.get("/api/diary/{user}")
def diary(user: str):
    rows = store.entries(user, "diary")
    return {"entries": rows, "total_due": round(sum(r["amount"] for r in rows), 2),
            "note": "Dated entries can support a wage-due notice. Keep photos/messages too."}


# ---------- rights, documents, safety ----------
@app.post("/api/schemes/match")
def schemes_match(b: SchemeIn):
    return {"matches": rag.match_schemes(**b.model_dump(exclude={"lang"})),
            "note": i18n.t(b.lang, "knowledge_hdr")}


@app.get("/api/schemes/search")
def schemes_search(q: str, k: int = 3):
    return {"results": rag.get_retriever().search(q, k=min(k, 10))}


@app.post("/api/document/scan")
def document_scan(b: DocScanIn):
    found = docs.scan(b.text)
    if not found:
        return {"risks": [], "message": i18n.t(b.lang, "risk_none")}
    risks = [{"point": i18n.t(b.lang, f["key"]), "snippet": f["snippet"]} for f in found]
    return {"risks": risks, "message": i18n.t(b.lang, "doc_hdr")}


@app.post("/api/vault")
def vault_add(b: VaultIn):
    if b.doc_type not in docs.DOC_LABEL_KEY:
        raise HTTPException(422, f"doc_type must be one of {sorted(docs.DOC_LABEL_KEY)}")
    try:
        date.fromisoformat(b.expiry)
    except ValueError:
        raise HTTPException(422, "expiry must be YYYY-MM-DD")
    store.vault_set(b.user, b.doc_type, b.expiry)
    return vault_get(b.user, b.lang)


@app.get("/api/vault/{user}")
def vault_get(user: str, lang: str = "en"):
    items = []
    for r in store.vault_list(user):
        st = docs.expiry_status(r["expiry"])
        name = i18n.t(lang, docs.DOC_LABEL_KEY[r["doc_type"]])
        items.append({"doc_type": r["doc_type"], "expiry": r["expiry"], "days_left": st["days_left"],
                      "status": st["key"], "message": i18n.t(lang, st["key"], doc=name, days=st["days"])})
    return {"items": items}


@app.post("/api/fatigue")
def fatigue(b: FatigueIn):
    key = planner.fatigue_level(b.hours_worked, b.hours_slept, b.temp_c)
    return {"level": key.split("_")[1], "message": i18n.t(b.lang, key)}


@app.get("/api/sos")
def sos(lang: str = "en"):
    return {"message": i18n.t(lang, "sos"), "numbers": {"emergency": "112", "ambulance": "108", "women": "181", "legal_aid": "15100", "cyber": "1930"}}


# ---------- grievances, practice, collective voice ----------
@app.post("/api/grievance")
def grievance_draft(b: GrievanceIn):
    try:
        r = grievance.draft(**b.model_dump())
    except ValueError as e:
        raise HTTPException(422, str(e))
    r["message"] = i18n.t(b.lang, "letter_note")
    return r


@app.get("/api/practice/scenarios")
def practice_list(lang: str = "en"):
    return {"scenarios": [{"id": k, "title": practice.pick(v["title"], lang)} for k, v in practice.SCENARIOS.items()]}


@app.post("/api/practice/start")
def practice_start(b: PracticeStartIn):
    r = practice.start(b.scenario, b.lang)
    if not r:
        raise HTTPException(404, "unknown scenario")
    return r


@app.post("/api/practice/step")
def practice_step(b: PracticeStepIn):
    r = practice.reply(b.scenario, b.step, b.answer, b.lang)
    if not r:
        raise HTTPException(422, "invalid scenario or step")
    return r


@app.post("/api/collective/report")
def collective_report(b: ReportIn):
    store.report_add(b.company, b.issue, b.city)
    return collective_summary(b.lang)


@app.get("/api/collective/summary")
def collective_summary(lang: str = "en"):
    return {"groups": community.groups(lang)}
