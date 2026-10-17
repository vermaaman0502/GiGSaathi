# GigSaathi

A GenAI-ready assistant for gig and informal workers (delivery partners, drivers, domestic and daily-wage workers): earnings, money, safety, rights/schemes, document help and grievance drafting, delivered over chat (WhatsApp/Twilio webhook), a voice-enabled web page, and a REST API.

## What works today (v0.1)

| Area | Implemented |
|---|---|
| Earnings X-Ray | real hourly pay incl. waiting time, fuel, commission, EMI; unexplained-deduction flags; incentive progress; multi-app comparison (`app/tools/earnings.py`) |
| Is This Trip Worth It? | net profit/hour with dead mileage and wear |
| Money | Safe-to-Spend, Loan Trap Detector (true yearly rate incl. fees), Leak Finder, voice-style expense/income/wage diary via chat (SQLite) |
| Rights & schemes | RAG (BM25) over `data/schemes.json` with source links; rule-based Scheme Matchmaker |
| Grievances | letter drafter (deactivation, wage due, deductions, general) + 5-step Grievance Ladder |
| Safety/guardrails | PII + OTP masking before any LLM call, never asks for OTP/PIN/Aadhaar, crisis/SOS escalation to 112 / 108 / 181 / NALSA 15100 |
| Channels | `POST /whatsapp` (Twilio form webhook -> TwiML), `POST /chat`, web UI at `/` with browser speech-to-text/text-to-speech |
| LLM | Optional Claude phrasing (`ANTHROPIC_API_KEY`), constrained to retrieved FACTS; deterministic template fallback otherwise |

## Not built yet (roadmap)
Payout-screenshot/document OCR (Kagaz Samjho), Bhashini/Whisper STT-TTS for IVR calls, shift planner/forecasting, fatigue & weather alerts, reminder scheduler (EMI/document expiry), PDF export, practice mode, collective petitions, Postgres/pgvector. Intent routing is keyword-based; swapping to LLM tool-calling is the next step.

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
