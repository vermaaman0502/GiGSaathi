from typing import Dict, List, Optional
from xml.sax.saxutils import escape

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from . import orchestrator, rag
from .tools import earnings, grievance, money

app = FastAPI(title="GigSaathi", version="0.1.0",
              description="GenAI assistant for gig and informal workers: earnings, money, safety, rights, documents, grievances.")

STATIC = __import__("pathlib").Path(__file__).resolve().parent.parent / "static"


class ChatIn(BaseModel):
    user: str = Field(..., description="Opaque user id (e.g. hashed phone)")
    text: str = Field(..., max_length=2000)


class XRayIn(BaseModel):
    gross: float = Field(..., ge=0)
    hours_worked: float = Field(..., gt=0)
    waiting_hours: float = Field(0, ge=0)
    commission: float = Field(0, ge=0)
    fuel: float = Field(0, ge=0)
    emi_per_day: float = Field(0, ge=0)
    other_costs: float = Field(0, ge=0)
    deductions: List[Dict] = []


class TripIn(BaseModel):
    fare: float = Field(..., ge=0)
    distance_km: float = Field(..., ge=0)
    time_min: float = Field(..., gt=0)
    return_km: float = Field(0, ge=0)
    mileage_kmpl: float = Field(40, gt=0)
    fuel_price: float = Field(100, gt=0)
    commission_pct: float = Field(0, ge=0, le=100)


class SafeIn(BaseModel):
    expected_monthly_income: float = Field(..., ge=0)
    rent: float = Field(0, ge=0)
    emi: float = Field(0, ge=0)
    bills: float = Field(0, ge=0)
    savings_pct: float = Field(10, ge=0, le=100)
    spent_today: float = Field(0, ge=0)


class LoanIn(BaseModel):
    principal: float = Field(..., gt=0)
    emi: float = Field(..., gt=0)
    months: int = Field(..., gt=0)
    upfront_fee: float = Field(0, ge=0)


class GrievanceIn(BaseModel):
    kind: str
    name: str
    company: str
    details: str = ""
    amount: float = 0
    incident_date: Optional[str] = None
    evidence: List[str] = []


class SchemeIn(BaseModel):
    age: int = Field(..., ge=14, le=100)
    monthly_income: float = Field(..., ge=0)
    epfo_member: bool = False
    has_bank: bool = True
    income_tax_payer: bool = False
    street_vendor: bool = False


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(body: ChatIn):
    return orchestrator.handle(body.user, body.text)


@app.post("/whatsapp", include_in_schema=False)
def whatsapp(Body: str = Form(""), From: str = Form("unknown")):
    """Twilio WhatsApp webhook (form-encoded). Replies in TwiML."""
    import hashlib
    uid = hashlib.sha256(From.encode()).hexdigest()[:16]  # store a hash, not the phone number
    out = orchestrator.handle(uid, Body)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escape(out["reply"])}</Message></Response>'
    return Response(content=xml, media_type="application/xml")


@app.post("/api/earnings/xray")
def xray(b: XRayIn):
    res = earnings.real_hourly_earnings(b.gross, b.hours_worked, b.waiting_hours, b.commission, b.fuel, b.emi_per_day, b.other_costs)
    res["flags"] = earnings.flag_deductions(b.deductions, b.gross)
    return res


@app.post("/api/trip-worth")
def trip(b: TripIn):
    return earnings.trip_worth(**b.model_dump())


@app.post("/api/safe-to-spend")
def safe(b: SafeIn):
    return money.safe_to_spend(**b.model_dump())


@app.post("/api/loan-check")
def loan(b: LoanIn):
    try:
        return money.loan_check(**b.model_dump())
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/api/grievance")
def grievance_draft(b: GrievanceIn):
    try:
        return grievance.draft(**b.model_dump())
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/api/schemes/match")
def schemes_match(b: SchemeIn):
    return {"matches": rag.match_schemes(**b.model_dump()), "note": "Eligibility is indicative. Confirm on the official portal or at a CSC."}


@app.get("/api/schemes/search")
def schemes_search(q: str, k: int = 3):
    return {"results": rag.get_retriever().search(q, k=min(k, 10))}
