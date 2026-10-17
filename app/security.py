"""HTTP hardening: security headers, request-size cap, per-client rate limits and Twilio webhook signatures.
Pure standard library so it adds no dependencies. The rate limiter is in-memory, i.e. per server instance -
good enough to blunt abuse of a single instance; use a shared store (Redis/Upstash) for a global limit."""
import base64
import hashlib
import hmac
import os
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Mapping, Tuple

from fastapi import Request
from fastapi.responses import JSONResponse

MAX_BODY_BYTES = int(os.environ.get("MAX_BODY_BYTES", 10 * 1024 * 1024))   # base64 screenshots are the largest bodies

# (requests, window seconds). Expensive routes (LLM / vision / document parsing) get a tighter budget.
LIMITS: Dict[str, Tuple[int, int]] = {
    "ai": (int(os.environ.get("RATE_AI_PER_MIN", 20)), 60),
    "write": (int(os.environ.get("RATE_WRITE_PER_MIN", 60)), 60),
    "read": (int(os.environ.get("RATE_READ_PER_MIN", 240)), 60),
}
AI_PATHS = ("/chat", "/whatsapp", "/api/extract/", "/api/document/", "/api/proof-to-action")

HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(self), geolocation=(self), payment=()",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "Cross-Origin-Opener-Policy": "same-origin",
}
# The bundled lite page (static/index.html) uses inline script/style; everything else is JSON.
PAGE_CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
API_CSP = "default-src 'none'; frame-ancestors 'none'"
# Reference data that is the same for every user: let browsers/CDN cache it briefly instead of refetching.
PUBLIC_GET = ("/api/languages", "/api/i18n/", "/api/side-income", "/api/skills", "/api/haq/questions", "/api/haq/scheme/",
              "/api/practice/scenarios", "/api/sos", "/health")
DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")   # Swagger UI loads its assets from a CDN, so it keeps the default policy


class RateLimiter:
    def __init__(self) -> None:
        self._hits: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, client: str, bucket: str, now: float = 0.0) -> Tuple[bool, int]:
        """Sliding-window check. Returns (allowed, seconds until a slot frees up)."""
        limit, window = LIMITS[bucket]
        now = now or time.monotonic()
        with self._lock:
            q = self._hits[(client, bucket)]
            while q and q[0] <= now - window:
                q.popleft()
            if len(q) >= limit:
                return False, max(1, int(q[0] + window - now) + 1)
            q.append(now)
            if len(self._hits) > 50_000:          # bound memory: drop idle clients
                for k in [k for k, v in self._hits.items() if not v]:
                    del self._hits[k]
            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def client_id(request: Request) -> str:
    # Vercel / most proxies put the original client first in X-Forwarded-For.
    fwd = request.headers.get("x-forwarded-for", "")
    return (fwd.split(",")[0].strip() or request.headers.get("x-real-ip", "") or (request.client.host if request.client else "unknown"))


def bucket_for(request: Request) -> str:
    if request.url.path.startswith(AI_PATHS):
        return "ai"
    return "read" if request.method in ("GET", "HEAD", "OPTIONS") else "write"


async def harden(request: Request, call_next):
    """Middleware: reject oversized bodies, rate-limit, then add security headers to every response."""
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > MAX_BODY_BYTES:
        return JSONResponse({"detail": "Request too large"}, status_code=413)
    if request.method != "OPTIONS" and os.environ.get("RATE_LIMIT", "1") != "0":
        ok, retry = limiter.allow(client_id(request), bucket_for(request))
        if not ok:
            return JSONResponse({"detail": "Too many requests. Please wait a moment and try again."}, status_code=429,
                                headers={"Retry-After": str(retry)})
    response = await call_next(request)
    for k, v in HEADERS.items():
        response.headers.setdefault(k, v)
    path = request.url.path
    if not path.startswith(DOCS_PATHS):
        response.headers.setdefault("Content-Security-Policy", PAGE_CSP if response.headers.get("content-type", "").startswith("text/html") else API_CSP)
    if request.method == "GET" and "cache-control" not in response.headers:
        if path.startswith(PUBLIC_GET) and response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=300, s-maxage=3600, stale-while-revalidate=86400"
        elif path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"     # per-user data must not sit in shared caches
    return response


def twilio_signature_ok(url: str, params: Mapping[str, str], signature: str, token: str) -> bool:
    """Twilio request validation: base64(HMAC-SHA1(token, url + sorted key+value pairs))."""
    payload = url + "".join(k + params[k] for k in sorted(params))
    digest = base64.b64encode(hmac.new(token.encode(), payload.encode(), hashlib.sha1).digest()).decode()
    return hmac.compare_digest(digest, signature or "")
