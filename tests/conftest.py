import os

# The suite fires hundreds of requests from one client; rate limiting has its own dedicated tests.
os.environ.setdefault("RATE_LIMIT", "0")
