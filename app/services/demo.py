"""Synthetic demo worker. Everything here is invented, flagged is_demo=1, and only ever written for ids that
start with 'demo-'. No real worker data or documents are used."""
from datetime import date, timedelta

from .. import store
from . import earn, ledger

PLATFORMS = ["SwiftEats (demo)", "QuickRide (demo)"]


def is_demo_id(user: str) -> bool:
    return user.startswith("demo-")


def seed(user: str) -> dict:
    if not is_demo_id(user):
        raise ValueError("demo data can only be created for ids starting with 'demo-'")
    store.delete_user(user)
    today = date.today()
    for i in range(13, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        evening = i % 2 == 0
        earn.add_shift(user, {"day": d, "platform": PLATFORMS[0] if evening else PLATFORMS[1], "hours": 6 if evening else 7,
                              "start_hour": 18 if evening else 10, "gross": 980 if evening else 760, "commission": 196 if evening else 152,
                              "deductions": 20, "incentive": 150 if evening and i % 4 == 0 else 0, "fuel": 160 if evening else 190, "other_expenses": 30,
                              "source": "demo"}, True)
    # one synthetic payout that is short of the platform's own numbers (possible discrepancy)
    earn.add_shift(user, {"day": today.isoformat(), "platform": PLATFORMS[0], "hours": 7, "start_hour": 18, "gross": 1100, "commission": 220, "deductions": 40,
                          "incentive": 200, "fuel": 170, "other_expenses": 30, "promised": 1040, "received": 880, "source": "demo", "note": "synthetic payout"}, True)
    for c, a in [("chai", 20)] * 7 + [("lunch", 60)] * 3 + [("recharge", 199)]:
        store.add(user, "expense", a, "food" if c != "recharge" else "mobile", c)
    earn.diary_add(user, {"day": (today - timedelta(days=5)).isoformat(), "employer": "Demo Contractor", "work": "masonry helper", "hours": 8, "promised": 700, "received": 500}, True)
    earn.diary_add(user, {"day": (today - timedelta(days=4)).isoformat(), "employer": "Demo Contractor", "work": "masonry helper", "hours": 8, "promised": 700, "received": 700}, True)
    store.vault_set(user, "puc", (today + timedelta(days=12)).isoformat())
    store.vault_set(user, "insurance", (today + timedelta(days=200)).isoformat())
    ledger.tracker_save(user, "eshram", "documents_ready", (today + timedelta(days=3)).isoformat(), is_demo=True)
    ledger.impact_add(user, "expense_avoided", 450, "user_reported", "skipped two low-fare trips (demo)", True)
    ledger.impact_add(user, "extra_payment", 160, "estimated", "possible shortfall found (demo)", True)
    return {"user": user, "demo": True, "note": "Synthetic data for demonstration only."}
