# Security

GigSaathi handles income data, documents and complaints of vulnerable workers. This page lists what protects that data today and what is still missing.

## What is in place

| Area | Control | Where |
|---|---|---|
| Secrets the app must never see | Never asks for OTP, PIN, password or full Aadhaar. A message containing one gets a warning instead of being processed. | `app/guardrails.py` |
| Data sent to the AI model | Aadhaar, PAN, card numbers and OTPs are masked before any LLM call, including document text. Prompts treat user content as data, not instructions. | `app/llm.py`, `app/guardrails.py` |
| Screenshots | OCR runs in the browser. The image is not uploaded. | `web/lib/ocr.ts` |
| Browser access | CORS allows only GigSaathi's own frontends (`CORS_ORIGINS`), with only the methods and headers the app uses. | `app/main.py` |
| HTTP headers | CSP, HSTS, `X-Frame-Options: DENY`, `nosniff`, a strict referrer policy and a Permissions-Policy (mic and location only, after in-app consent). | `app/security.py`, `web/next.config.mjs` |
| Abuse | Per-client sliding-window rate limits (AI routes 20/min, writes 60/min, reads 240/min) and a 10 MB request cap. | `app/security.py` |
| Input | Pydantic validation on every field (lengths, ranges, user-id format, image type allowlist). Parameterised SQL only. | `app/main.py`, `app/routers.py` |
| WhatsApp webhook | Rejects requests without a valid Twilio signature when `TWILIO_AUTH_TOKEN` is set. Stores a hash of the phone number, not the number. | `app/main.py` |
| Errors | Unhandled errors return a generic message, with no stack traces. | `app/main.py` |
| Caching | Per-user API responses are `Cache-Control: no-store`. Only shared reference data is cacheable. | `app/security.py` |
| Privacy | One-tap export and erasure of all of a user's data. Demo data is isolated under reserved `demo-` ids. | `/api/user/{id}` |
| Dependencies | Python dependencies are pinned. `npm audit` reports 0 vulnerabilities in production dependencies. | `requirements.txt`, `web/package.json` |

All of the above is covered by `tests/test_security.py`.

## Known limitations

- **Identity:** a random device token (at least 16 characters) acts as a bearer secret and appears in API paths. There is no account login yet, so anyone holding the token can read that device's data. The plan is Supabase Auth with row-level security.
- **Rate limits** are kept in memory per server instance. A global limit needs a shared store such as Redis.
- **Storage:** SQLite on Vercel is ephemeral and not encrypted at rest. The plan is managed Postgres with encryption at rest.

## Reporting a vulnerability

Please do not open a public issue. Email the maintainer (GitHub: `vermaaman0502`) with steps to reproduce. We aim to reply within 7 days.
