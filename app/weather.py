"""Verified weather via Open-Meteo (free, no key). Returns available=False on any failure - never a
made-up forecast."""
from typing import Dict

import httpx

HEAT_C = 40.0
RAIN_PCT = 60


def forecast(lat: float, lon: float, timeout: float = 6.0) -> Dict:
    try:
        r = httpx.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon, "daily": "temperature_2m_max,precipitation_probability_max",
            "timezone": "auto", "forecast_days": 1}, timeout=timeout)
        r.raise_for_status()
        d = r.json()["daily"]
        t, p = d["temperature_2m_max"][0], d["precipitation_probability_max"][0]
        if t is None:
            raise ValueError("no data")
        return {"available": True, "source": "Open-Meteo", "temp_max_c": round(t, 1), "rain_prob_pct": p or 0,
                "heat_alert": t >= HEAT_C, "rain_alert": (p or 0) >= RAIN_PCT}
    except Exception:
        return {"available": False, "source": "Open-Meteo", "heat_alert": False, "rain_alert": False}
