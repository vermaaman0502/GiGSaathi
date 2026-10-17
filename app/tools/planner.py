"""Shift planner, fatigue check and incentive tracker. Rule-based; returns i18n keys/values so
the API layer can render in the worker's language."""
from typing import Dict, List

# Relative demand (0-10) by hour of day for each kind of work. Indicative, not measured data -
# replace with the worker's own history / city data when available.
_FOOD = {11: 5, 12: 8, 13: 8, 14: 5, 15: 3, 18: 6, 19: 9, 20: 10, 21: 9, 22: 6}
_RIDE = {6: 4, 7: 8, 8: 10, 9: 9, 10: 6, 16: 5, 17: 8, 18: 10, 19: 10, 20: 8, 21: 6, 22: 5}
_PARCEL = {9: 5, 10: 7, 11: 8, 12: 8, 13: 7, 14: 7, 15: 7, 16: 6, 17: 5}
CURVES = {"food": _FOOD, "ride": _RIDE, "parcel": _PARCEL}


def shift_plan(work_type: str = "food", weather: str = "clear", festival: bool = False, window: int = 3) -> Dict:
    curve = dict(CURVES.get(work_type, _FOOD))
    tips: List[str] = []
    if weather == "rain":
        for h in list(curve):
            if work_type != "parcel" and h >= 18 or work_type == "ride":
                curve[h] = curve[h] * 1.25
        tips.append("tip_rain")
    if weather == "hot":
        for h in list(curve):
            if 12 <= h < 16:
                curve[h] = curve[h] * 0.5
        tips.append("tip_heat")
    if festival:
        for h in list(curve):
            if 17 <= h <= 22:
                curve[h] = curve[h] * 1.15
        tips.append("tip_festival")
    tips.append("tip_rest")

    def score(start: int) -> float:
        return sum(curve.get(h, 0) for h in range(start, start + window))

    starts = sorted(range(6, 24 - window + 1), key=score, reverse=True)
    chosen: List[int] = []
    for s in starts:
        if all(abs(s - c) >= window for c in chosen):
            chosen.append(s)
        if len(chosen) == 2:
            break
    windows = [{"start": s, "end": s + window, "score": round(score(s) / window, 1)} for s in chosen]
    return {"windows": windows, "tips": tips}


def fatigue_level(hours_worked: float, hours_slept: float, temp_c: float = 30.0) -> str:
    pts = 0
    pts += 2 if hours_worked > 10 else 1 if hours_worked > 8 else 0
    pts += 2 if hours_slept < 5 else 1 if hours_slept < 6.5 else 0
    pts += 1 if temp_c >= 40 else 0
    return "fatigue_high" if pts >= 4 else "fatigue_med" if pts >= 2 else "fatigue_low"


def incentive(trips_done: int, trips_target: int, hours_left: float) -> Dict:
    remaining = max(trips_target - trips_done, 0)
    if remaining == 0:
        return {"key": "incentive_done", "rem": 0, "per_hr": 0.0}
    per_hr = round(remaining / hours_left, 1) if hours_left > 0 else 99.0
    return {"key": "incentive_far" if per_hr > 4 else "incentive", "rem": remaining, "per_hr": per_hr}
