"""Earnings X-Ray, trip-worth and incentive maths. Pure functions, no I/O."""
from typing import Dict, List, Optional

# Deduction labels a worker can reasonably expect on a payout statement.
EXPECTED_DEDUCTIONS = {"commission", "platform fee", "gst", "tds", "insurance", "fuel advance"}


def real_hourly_earnings(
    gross: float,
    hours_worked: float,
    waiting_hours: float = 0.0,
    commission: float = 0.0,
    fuel: float = 0.0,
    emi_per_day: float = 0.0,
    other_costs: float = 0.0,
) -> Dict:
    """Net earnings per hour *including* unpaid waiting time."""
    total_hours = hours_worked + waiting_hours
    if total_hours <= 0:
        raise ValueError("hours_worked must be positive")
    net = gross - commission - fuel - emi_per_day - other_costs
    return {
        "gross": round(gross, 2),
        "net": round(net, 2),
        "total_hours": round(total_hours, 2),
        "gross_hourly": round(gross / total_hours, 2),
        "real_hourly": round(net / total_hours, 2),
        "keep_pct": round(100 * net / gross, 1) if gross > 0 else 0.0,
    }


def flag_deductions(deductions: List[Dict], gross: float, max_pct: float = 25.0) -> List[str]:
    """Flag unknown or unusually large deductions. Each item: {label, amount}."""
    flags = []
    total = 0.0
    for d in deductions:
        label = str(d.get("label", "")).strip().lower()
        amount = float(d.get("amount", 0))
        total += amount
        if label not in EXPECTED_DEDUCTIONS:
            flags.append(f"Unexplained deduction '{d.get('label')}' of Rs {amount:.0f} - ask support for a breakdown.")
        elif gross > 0 and amount / gross * 100 > max_pct:
            flags.append(f"'{d.get('label')}' is {amount / gross * 100:.0f}% of gross, above the usual {max_pct:.0f}%.")
    if gross > 0 and total / gross * 100 > max_pct:
        flags.append(f"Total deductions are {total / gross * 100:.0f}% of gross earnings.")
    return flags


def incentive_progress(trips_done: int, trips_target: int, bonus: float, hours_left: float) -> Dict:
    remaining = max(trips_target - trips_done, 0)
    pace = remaining / hours_left if hours_left > 0 else float("inf")
    return {
        "remaining_trips": remaining,
        "trips_per_hour_needed": None if pace == float("inf") else round(pace, 2),
        "bonus": bonus,
        "reached": remaining == 0,
    }


def trip_worth(
    fare: float,
    distance_km: float,
    time_min: float,
    return_km: float = 0.0,
    mileage_kmpl: float = 40.0,
    fuel_price: float = 100.0,
    commission_pct: float = 0.0,
    wear_per_km: float = 2.0,
    min_hourly: float = 100.0,
    pickup_km: float = 0.0,
    pickup_min: float = 0.0,
) -> Dict:
    """Is This Trip Worth It? Net profit after fuel, wear, commission and dead mileage."""
    if mileage_kmpl <= 0:
        raise ValueError("mileage must be positive")
    km = distance_km + return_km + pickup_km
    minutes = time_min + pickup_min
    fuel_cost = km * fuel_price / mileage_kmpl
    wear = km * wear_per_km
    commission = fare * commission_pct / 100
    net = fare - commission - fuel_cost - wear
    hourly = net / (minutes / 60) if minutes > 0 else 0.0
    if net <= 0:
        verdict = "skip"
    elif hourly >= min_hourly:
        verdict = "accept"
    else:
        verdict = "marginal"
    return {
        "net_profit": round(net, 2),
        "net_per_hour": round(hourly, 2),
        "net_per_km": round(net / km, 2) if km else 0.0,
        "fuel_cost": round(fuel_cost, 2),
        "wear_cost": round(wear, 2),
        "commission": round(commission, 2),
        "verdict": verdict,
    }


def compare_apps(apps: List[Dict]) -> Optional[Dict]:
    """Multi-app comparison. Each: {name, gross, hours, commission, fuel}. Returns ranked list."""
    rows = []
    for a in apps:
        h = float(a.get("hours", 0))
        if h <= 0:
            continue
        net = float(a["gross"]) - float(a.get("commission", 0)) - float(a.get("fuel", 0))
        rows.append({"name": a["name"], "net": round(net, 2), "net_per_hour": round(net / h, 2)})
    if not rows:
        return None
    rows.sort(key=lambda r: r["net_per_hour"], reverse=True)
    return {"ranking": rows, "best": rows[0]["name"]}
