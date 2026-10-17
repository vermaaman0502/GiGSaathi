"""Money tools: safe-to-spend, loan trap detector, leak finder, expense categoriser."""
from collections import Counter
from typing import Dict, List

CATEGORY_KEYWORDS = {
    "fuel": ["petrol", "diesel", "fuel", "cng", "पेट्रोल", "डीजल", "tel"],
    "food": ["chai", "tea", "khana", "food", "lunch", "dinner", "nashta", "चाय", "खाना", "नाश्ता"],
    "rent": ["rent", "kiraya", "kiraaya", "किराया"],
    "emi": ["emi", "kist", "किस्त", "loan"],
    "mobile": ["recharge", "data", "mobile", "रिचार्ज"],
    "vehicle": ["repair", "puncture", "service", "tyre", "garage", "mechanic", "मरम्मत"],
    "family": ["school", "doctor", "dawai", "medicine", "दवाई", "बच्चे"],
}


def categorise(text: str) -> str:
    t = text.lower()
    for cat, words in CATEGORY_KEYWORDS.items():
        if any(w in t for w in words):
            return cat
    return "other"


def safe_to_spend(
    expected_monthly_income: float,
    rent: float = 0.0,
    emi: float = 0.0,
    bills: float = 0.0,
    savings_pct: float = 10.0,
    days_in_month: int = 30,
    spent_today: float = 0.0,
) -> Dict:
    """One daily spending limit after fixed costs and a savings cut."""
    fixed = rent + emi + bills
    savings = expected_monthly_income * savings_pct / 100
    free = expected_monthly_income - fixed - savings
    daily = free / days_in_month
    return {
        "fixed_monthly": round(fixed, 2),
        "savings_monthly": round(savings, 2),
        "daily_limit": round(max(daily, 0), 2),
        "left_today": round(max(daily - spent_today, 0), 2),
        "shortfall": free < 0,
    }


def _monthly_rate_from_cashflow(principal: float, emi: float, months: int) -> float:
    """Solve for monthly IRR by bisection."""
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if mid == 0:
            pv = emi * months
        else:
            pv = emi * (1 - (1 + mid) ** -months) / mid
        if pv > principal:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def loan_check(principal: float, emi: float, months: int, upfront_fee: float = 0.0) -> Dict:
    """Real yearly interest (effective, fees included) and total repayment."""
    if principal <= 0 or emi <= 0 or months <= 0:
        raise ValueError("principal, emi and months must be positive")
    received = principal - upfront_fee
    total = emi * months
    if total <= received:
        raise ValueError("total repayment is not more than money received - check the numbers")
    r = _monthly_rate_from_cashflow(received, emi, months)
    apr = r * 12 * 100
    effective = ((1 + r) ** 12 - 1) * 100
    if apr >= 36:
        risk = "high"
    elif apr >= 24:
        risk = "medium"
    else:
        risk = "low"
    return {
        "money_received": round(received, 2),
        "total_repayment": round(total, 2),
        "extra_paid": round(total - received, 2),
        "yearly_interest_pct": round(apr, 1),
        "effective_yearly_pct": round(effective, 1),
        "risk": risk,
        "safer_options": [
            "Bank / cooperative bank / SHG loan (usually 10-18% a year)",
            "PM Mudra (Shishu) or PM SVANidhi for small business and vendors",
            "Ask your platform for an advance with no interest before taking an app loan",
        ],
    }


def find_leaks(expenses: List[Dict], min_count: int = 4, max_each: float = 150.0) -> List[Dict]:
    """Repeated small spends. Each expense: {category, amount, note}."""
    small = [e for e in expenses if float(e["amount"]) <= max_each]
    counts = Counter(e.get("category", "other") for e in small)
    leaks = []
    for cat, n in counts.most_common():
        if n < min_count:
            continue
        total = sum(float(e["amount"]) for e in small if e.get("category", "other") == cat)
        leaks.append({"category": cat, "times": n, "total": round(total, 2)})
    return leaks
