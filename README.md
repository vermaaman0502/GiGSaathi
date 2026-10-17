# GigSaathi

A GenAI-ready assistant for gig and informal workers (delivery partners, drivers, domestic and daily-wage workers): earnings, money, safety, rights/schemes, document help and grievance drafting, delivered over chat (WhatsApp/Twilio webhook), a voice-enabled web page, and a REST API.

## What works today (v0.2)

**12 languages, selectable in the UI and auto-detected in chat/WhatsApp:** English, हिन्दी, Hinglish, বাংলা, தமிழ், తెలుగు, मराठी, ગુજરાતી, ಕನ್ನಡ, മലയാളം, ਪੰਜਾਬੀ, ଓଡ଼ିଆ. Every calculation result, safety message, tip and UI label is translated; strings live in `app/locales/<code>.json` so native speakers can review and fix them (a test enforces that all 12 files have identical keys and placeholders). Browser voice input/output uses each language's locale.

| Area | Implemented |
|---|---|
| Earn | Earnings X-Ray (real hourly pay incl. waiting, fuel, commission, EMI; unexplained-deduction flags), Is-This-Trip-Worth-It, Shift Planner (time windows + rain/heat/festival tips), Incentive tracker, multi-app comparison, side-income & skill ladder |
| Money | Safe-to-Spend, Loan Trap Detector (true yearly rate incl. fees), Leak Finder, voice/chat expense + income diary, daily earned/spent/saved, wage diary with total due |
| Rights | RAG (BM25) over `data/schemes.json` with source links; rule-based Scheme Matchmaker |
| Documents | Kagaz Samjho (paste text -> risky-clause flags: interest, penalty, termination, deductions, non-refundable, deposits); document expiry vault (DL/RC/insurance/PUC) |
| Help | One-tap SOS, fatigue check, complaint drafter (English letter + Hindi version) with 5-step Grievance Ladder, Practice Mode role-play (contractor / police / customer) with coaching, Collective Voice (anonymous reports -> petition only when >= 3 workers, no user id stored) |
| Safety/guardrails | PII + OTP masking before any LLM call, never asks for OTP/PIN/Aadhaar, crisis words in all 12 scripts escalate to 112 / 108 / 181 / NALSA 15100 |
| Channels | `POST /whatsapp` (Twilio -> TwiML, language auto-detected), `POST /chat`, responsive web app at `/` (deep links: `/?lang=ta&tab=earn`), REST API at `/docs` |
| LLM | Optional Claude phrasing (`ANTHROPIC_API_KEY`) from retrieved FACTS in the chosen language; deterministic fallback otherwise |

## Not built yet (roadmap)
Payout-screenshot / document-photo OCR, Bhashini/Whisper STT-TTS for IVR calls, ML forecasting for the shift planner (current windows are rule-based and indicative), live weather/IMD alerts, reminder scheduler (EMI/document-expiry pushes), PDF export, per-language scheme summaries (scheme text is English unless the LLM is enabled), Postgres/pgvector. Intent routing is keyword-based; swapping to LLM tool-calling is the next step.

## Translation quality
Translations were machine-drafted and are **not yet reviewed by native speakers**. Please have each language checked (especially safety/legal wording) before field use.

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
uvicorn app.main:app --reload     # http://localhost:8000  (docs at /docs)
```

## WhatsApp (Twilio sandbox)
Point the sandbox "when a message comes in" webhook to `https://<your-host>/whatsapp` (POST).

## Deploy (Vercel)
`vercel --prod` from the repo root (`vercel.json` + `api/index.py` are included). Note: SQLite lives in `/tmp` on serverless, so entries are ephemeral - set up Postgres/Supabase for persistence, or deploy the same app on a Droplet/Render with a disk.

## Trust & safety notes
- `data/schemes.json` is **seed data** written from general knowledge, not a live scrape. Verify every scheme against its official source before real use; each record links its source.
- The BM25 retriever is lexical: an off-topic query can still match on a shared word. The LLM prompt tells the model to say "not sure" when FACTS don't cover the question.
- Loan/trip numbers use stated assumptions (e.g. 40 km/l, petrol Rs 100) - override via the API.
- Not legal, medical or financial advice. Serious cases are routed to human helplines.
