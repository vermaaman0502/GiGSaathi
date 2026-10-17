"""v2 API: dashboard, earnings, HaqFinder, documents, NyaySaathi, safety, impact, demo, privacy.
Identity: an unguessable device token (>=16 chars) acts as a bearer secret until real auth (Supabase) is plugged in.
Ids starting with 'demo-' are reserved for synthetic demo data."""
import re
from datetime import date
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from . import i18n, schemes, store, weather
from .messages import m
from .services import demo, docsvc, earn, ledger, opps, proof
from .tools import earnings as et, planner

r = APIRouter(prefix="/api")
UID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def uid(user: str) -> str:
    if not UID.match(user) or (not user.startswith("demo-") and len(user) < 16):
        raise HTTPException(422, "invalid user id (use a random token of at least 16 characters)")
    return user


class ShiftIn(BaseModel):
    user: str
    day: Optional[str] = None
    platform: str = "other"
    hours: float = Field(0, ge=0, le=24)
    start_hour: Optional[int] = Field(None, ge=0, le=23)
    gross: float = Field(0, ge=0)
    commission: float = Field(0, ge=0)
    deductions: float = Field(0, ge=0)
    incentive: float = Field(0, ge=0)
    fuel: float = Field(0, ge=0)
    other_expenses: float = Field(0, ge=0)
    promised: Optional[float] = Field(None, ge=0)
    received: Optional[float] = Field(None, ge=0)
    source: str = "manual"
    note: str = Field("", max_length=200)


class ProofIn(ShiftIn):
    lang: str = "en"
    create_grievance: bool = False
    name: str = Field("", max_length=80)
    company: str = Field("", max_length=80)
    save: bool = True


class TripIn(BaseModel):
    user: str = ""
    lang: str = "en"
    fare: float = Field(..., ge=0)
    distance_km: float = Field(..., ge=0)
    time_min: float = Field(..., gt=0)
    return_km: float = Field(0, ge=0)
    mileage_kmpl: float = Field(40, gt=0)
    fuel_price: float = Field(100, gt=0)
    commission_pct: float = Field(0, ge=0, le=100)
    tolls: float = Field(0, ge=0)
    other_expenses: float = Field(0, ge=0)
    wear_per_km: float = Field(2.0, ge=0)


class DiaryIn(BaseModel):
    user: str
    day: Optional[str] = None
    employer: str = Field("", max_length=80)
    work: str = Field("", max_length=120)
    hours: float = Field(0, ge=0, le=24)
    promised: float = Field(0, ge=0)
    received: float = Field(0, ge=0)


class AnswersIn(BaseModel):
    lang: str = "en"
    answers: Dict = {}


class TrackIn(BaseModel):
    user: str
    scheme_id: str
    status: Optional[str] = None
    reminder: Optional[str] = None
    checklist: Optional[Dict[str, bool]] = None


class TextIn(BaseModel):
    text: str = Field(..., max_length=20000)
    lang: str = "en"


class ImageIn(BaseModel):
    image_b64: str = Field(..., max_length=8_000_000)
    media_type: str = "image/jpeg"
    lang: str = "en"


class GrievanceIn(BaseModel):
    user: str
    issue: str
    name: str = Field(..., max_length=80)
    company: str = Field(..., max_length=80)
    amount: float = Field(0, ge=0)
    incident_date: Optional[str] = None
    details: str = Field("", max_length=1000)
    evidence: List[str] = []
    lang: str = "en"


class GrievancePatch(BaseModel):
    user: str
    status: Optional[str] = None
    letter: Optional[str] = Field(None, max_length=6000)
    event: Optional[str] = Field(None, max_length=300)
    evidence: Optional[List[str]] = None


class ImpactIn(BaseModel):
    user: str
    kind: str
    amount: float = Field(0, ge=0)
    basis: str
    note: str = Field("", max_length=200)


class IncentiveIn(BaseModel):
    trips_done: int = Field(..., ge=0)
    target_trips: int = Field(..., gt=0)
    reward: float = Field(0, ge=0)
    hours_left: float = Field(..., ge=0)
    lang: str = "en"


# ---------- dashboard / earnings ----------
@r.get("/dashboard/{user}")
def dashboard(user: str, lang: str = "en"):
    return earn.dashboard(uid(user), lang)


@r.post("/shifts")
def shift_add(b: ShiftIn):
    u = uid(b.user)
    sid = earn.add_shift(u, b.model_dump(), demo.is_demo_id(u))
    return {"id": sid, "data_source": earn.data_source(u)}


@r.get("/shifts/{user}")
def shift_list(user: str, days: int = 30):
    return {"shifts": earn.shifts(uid(user), min(days, 365))}


@r.delete("/shifts/{user}/{sid}")
def shift_delete(user: str, sid: int):
    store.x("DELETE FROM shifts WHERE user=? AND id=?", (uid(user), sid))
    return {"deleted": sid}


@r.get("/compare/platforms/{user}")
def compare(user: str, days: int = 30):
    return earn.compare_platforms(uid(user), min(days, 365))


@r.get("/shift-insights/{user}")
def shift_insights(user: str):
    s = earn.band_stats(uid(user))
    s["note"] = ("Ranges come only from your own saved shifts and are not a forecast." if s["enough_data"]
                 else "Not enough data yet - at least 5 shifts with a start time are needed. Showing generic indicative windows instead.")
    s["generic"] = None if s["enough_data"] else planner.shift_plan("food", "clear")["windows"]
    return s


@r.post("/trip-profit")
def trip_profit(b: TripIn):
    d = b.model_dump(exclude={"user", "lang"})
    hist = earn.history_stats(b.user) if b.user and UID.match(b.user) else None
    res = et.trip_worth(**d, history_net_per_hour=hist["avg_net_per_hour"] if hist else None)
    res["data_source"] = "estimate"
    return res


@r.get("/leaks/{user}")
def leaks(user: str):
    return {"leaks": earn.leaks(uid(user)), "note": "These are prompts to review your spending - not confirmed savings."}


@r.get("/weather")
def get_weather(lat: float, lon: float, lang: str = "en"):
    w = weather.forecast(lat, lon)
    w["message"] = (m(lang, "weather_unavailable") if not w["available"] else m(lang, "weather_heat", t=w["temp_max_c"]) if w["heat_alert"]
                    else m(lang, "weather_rain", p=w["rain_prob_pct"]) if w["rain_alert"] else m(lang, "weather_ok"))
    return w


@r.post("/incentive/parse")
def incentive_parse(b: TextIn):
    return docsvc.parse_incentive_rule(b.text)


@r.post("/incentive/progress")
def incentive_progress(b: IncentiveIn):
    p = planner.incentive(b.trips_done, b.target_trips, b.hours_left)
    return {**p, "message": i18n.t(b.lang, p["key"], rem=p["rem"], bonus=i18n.fmt(b.reward), per_hr=p["per_hr"], hours=i18n.fmt(b.hours_left))}


@r.get("/skills")
def skills(work_type: str = "delivery"):
    import json
    from pathlib import Path
    data = json.loads((Path(__file__).resolve().parent.parent / "data" / "side_income.json").read_text(encoding="utf-8"))
    return {"note": data["note"], "ideas": data.get(work_type, []), "resources": data.get("resources", [])}


@r.post("/extract/payout-text")
def extract_payout(b: TextIn):
    return docsvc.parse_payout_text(b.text)


@r.post("/extract/payout-image")
def extract_payout_image(b: ImageIn):
    """Server-side vision extraction. Only available when an LLM key is configured; otherwise the client
    should run on-device OCR and call /extract/payout-text."""
    from . import llm
    out = llm.complete("Read this payout screenshot. Reply with plain text lines 'label: amount' for gross earnings, commission, incentives, each deduction and the final payout, plus the date and hours if shown. Do not guess unreadable values.",
                       "Extract the figures.", 500, b.image_b64, b.media_type)
    if out is None:
        return {"available": False, "reason": "No vision model is configured on the server. Use on-device OCR or enter the figures manually."}
    return {"available": True, **docsvc.parse_payout_text(out), "raw_text": out}


@r.post("/proof-to-action")
def proof_to_action(b: ProofIn):
    u = uid(b.user)
    try:
        rec = b.model_dump(exclude={"user", "lang", "create_grievance", "name", "company", "save"})
        return proof.run(u, rec, b.lang, b.create_grievance, b.name, b.company, demo.is_demo_id(u), b.save)
    except ValueError as e:
        raise HTTPException(422, str(e))


@r.get("/opportunities/{user}")
def opportunities(user: str, lang: str = "en"):
    return opps.build(uid(user), lang)


class ExpenseIn(BaseModel):
    user: str
    category: str = Field("other", max_length=30)
    amount: float = Field(..., gt=0)
    note: str = Field("", max_length=100)


@r.post("/expenses")
def expense_add(b: ExpenseIn):
    u = uid(b.user)
    store.add(u, "expense", b.amount, b.category.strip().lower(), b.note)
    return {"leaks": earn.leaks(u)}


# ---------- wage diary ----------
@r.post("/wage-diary")
def diary_add(b: DiaryIn):
    u = uid(b.user)
    earn.diary_add(u, b.model_dump(), demo.is_demo_id(u))
    return earn.diary_list(u)


@r.get("/wage-diary/{user}")
def diary_get(user: str):
    return earn.diary_list(uid(user))


@r.get("/export/{user}.csv")
def export_csv(user: str):
    return Response(earn.export_csv(uid(user)), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=gigsaathi-evidence.csv"})


# ---------- HaqFinder ----------
@r.post("/haq/match")
def haq_match(b: AnswersIn):
    cards = schemes.match(b.answers, b.lang)
    return {"cards": cards, "next_questions": schemes.next_questions(b.answers, b.lang),
            "note": "Eligibility here is a first check against published rules, not a decision. Confirm on the official portal."}


@r.get("/haq/questions")
def haq_questions(lang: str = "en"):
    return {"questions": schemes.next_questions({}, lang)}


@r.get("/haq/scheme/{scheme_id}")
def haq_scheme(scheme_id: str, lang: str = "en"):
    s = schemes.get(scheme_id)
    if not s:
        raise HTTPException(404, "unknown scheme")
    return schemes.view(s, lang)


@r.post("/haq/track")
def haq_track(b: TrackIn):
    u = uid(b.user)
    try:
        ledger.tracker_save(u, b.scheme_id, b.status, b.reminder, b.checklist, demo.is_demo_id(u))
    except KeyError:
        raise HTTPException(404, "unknown scheme")
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"tracker": ledger.tracker_get(u)}


@r.get("/haq/track/{user}")
def haq_tracked(user: str):
    return {"tracker": ledger.tracker_get(uid(user))}


# ---------- documents ----------
@r.post("/document/analyze")
def doc_analyze(b: TextIn):
    return docsvc.analyze(b.text, b.lang)


class EvidenceIn(BaseModel):
    user: str
    kind: str = "other"
    title: str = Field(..., max_length=120)
    data: Dict = {}


@r.post("/evidence")
def evidence_add(b: EvidenceIn):
    u = uid(b.user)
    ledger.evidence_add(u, b.kind, b.title, b.data, demo.is_demo_id(u))
    return {"evidence": ledger.evidence_list(u)}


@r.get("/evidence/{user}")
def evidence_get(user: str):
    return {"evidence": ledger.evidence_list(uid(user))}


# ---------- NyaySaathi ----------
@r.post("/grievances")
def grievance_create(b: GrievanceIn):
    u = uid(b.user)
    try:
        g = ledger.grievance_create(u, b.issue, b.name, b.company, {"amount": b.amount, "incident_date": b.incident_date, "details": b.details}, b.lang, b.evidence, demo.is_demo_id(u))
    except ValueError as e:
        raise HTTPException(422, str(e))
    return g


@r.get("/grievances/{user}")
def grievance_list(user: str):
    return {"grievances": ledger.grievance_list(uid(user))}


@r.patch("/grievances/{gid}")
def grievance_patch(gid: int, b: GrievancePatch):
    try:
        g = ledger.grievance_update(uid(b.user), gid, b.status, b.letter, b.event, b.evidence)
    except ValueError as e:
        raise HTTPException(422, str(e))
    if not g:
        raise HTTPException(404, "not found")
    return g


# ---------- impact ----------
@r.post("/impact")
def impact_add(b: ImpactIn):
    u = uid(b.user)
    try:
        ledger.impact_add(u, b.kind, b.amount, b.basis, b.note, demo.is_demo_id(u))
    except ValueError as e:
        raise HTTPException(422, str(e))
    return ledger.impact_summary(u)


@r.get("/impact/{user}")
def impact_get(user: str):
    u = uid(user)
    s = ledger.impact_summary(u)
    s["data_source"] = "demo" if demo.is_demo_id(u) else "user"
    return s


# ---------- demo & privacy ----------
@r.post("/demo/seed/{user}")
def demo_seed(user: str):
    u = uid(user)
    try:
        return demo.seed(u)
    except ValueError as e:
        raise HTTPException(422, str(e))


@r.get("/demo/payout-sample")
def demo_payout_sample():
    """Synthetic payout text (what OCR would read from the synthetic demo screenshot)."""
    return {"demo": True, "text": "SwiftEats (demo) - Weekly payout\nDate: 17 Oct 2026\nTotal earnings 1100\nPlatform fee 220\nBonus 200\nPenalty - late delivery 40\nOnline hours 7\nNet payout 880\n"}


@r.delete("/user/{user}")
def user_delete(user: str):
    return {"deleted_rows": store.delete_user(uid(user))}


@r.get("/user/{user}/export")
def user_export(user: str):
    return store.export_user(uid(user))
