"""Worker Opportunity Engine: up to three evidence-backed actions (earn more / save money / rights & benefits).
Each shows why it appears, the data used, impact if calculable, confidence, effort and a next action."""
from datetime import date, timedelta
from typing import Dict, List

from .. import store
from ..messages import m
from . import earn, ledger


def _conf(n: int) -> str:
    return "high" if n >= 15 else "medium" if n >= 8 else "low"


def build(user: str, lang: str = "en") -> Dict:
    items: List[Dict] = []
    stats = earn.band_stats(user)

    # 1. EARN MORE
    best = None
    if stats["enough_data"]:
        ok = [b for b in stats["bands"] if b["n"] >= 2]
        if len(ok) >= 2:
            best = max(ok, key=lambda b: b["avg"])
            others = [b for b in ok if b is not best]
            other_avg = round(sum(b["avg"] * b["n"] for b in others) / sum(b["n"] for b in others), 2)
            if best["avg"] > other_avg:
                band = f"{best['start']:02d}:00-{best['end']:02d}:00"
                items.append({"category": "earn_more", "title": m(lang, "opp_hours_title", band=band),
                              "why": m(lang, "opp_hours_why", n=stats["total_shifts"], a=round(best["avg"]), b=round(other_avg), band=band),
                              "evidence": [f"{b['n']} shifts starting {b['start']:02d}:00-{b['end']:02d}:00: Rs {b['avg']:.0f}/h" for b in stats["bands"]],
                              "impact": {"value_per_hour": round(best["avg"] - other_avg, 2), "basis": "estimated", "note": "difference in your own average take-home per hour"},
                              "confidence": _conf(stats["total_shifts"]), "effort": "low", "next": {"label": m(lang, "opp_hours_next"), "href": "/earnings?tab=shift"}})
    if not any(i["category"] == "earn_more" for i in items):
        items.append({"category": "earn_more", "title": m(lang, "opp_data_title"), "why": m(lang, "opp_data_why", n=stats["total_shifts"]),
                      "evidence": [f"{stats['total_shifts']} shifts with a start time"], "impact": None, "confidence": "none", "effort": "low",
                      "next": {"label": m(lang, "opp_data_next"), "href": "/earnings?tab=log"}})

    # 2. SAVE MONEY
    lk = earn.leaks(user)
    hist = earn.history_stats(user)
    if lk:
        top = lk[0]
        items.append({"category": "save_money", "title": m(lang, "opp_leak_title", cat=top["category"]),
                      "why": m(lang, "opp_leak_why", n=top["times"], cat=top["category"], total=round(top["total"])),
                      "evidence": [f"{top['times']} expenses, Rs {top['total']:.0f} total"],
                      "impact": {"value": top["total"], "basis": "estimated", "note": "spend to review - not a confirmed saving"},
                      "confidence": "low", "effort": "low", "next": {"label": m(lang, "opp_leak_next"), "href": "/earnings?tab=leaks"}})
    elif hist and hist["avg_net_per_hour"]:
        items.append({"category": "save_money", "title": m(lang, "opp_trip_title"), "why": m(lang, "opp_trip_why", ph=round(hist["avg_net_per_hour"])),
                      "evidence": [f"{hist['shifts']} logged shifts"], "impact": None, "confidence": _conf(hist["shifts"]), "effort": "low",
                      "next": {"label": m(lang, "opp_trip_next"), "href": "/earnings?tab=trip"}})

    # 3. RIGHTS & BENEFITS (priority: discrepancy > grievance follow-up > scheme)
    disc = next((s for s in earn.shifts(user, 30) if s["discrepancy"]["status"] == "possible_discrepancy"), None)
    sub = next((g for g in ledger.grievance_list(user) if g["status"] == "submitted"), None)
    if disc:
        amt = max(disc["discrepancy"]["shortfall_vs_calculated"] or 0, disc["discrepancy"]["shortfall_vs_promised"] or 0)
        items.append({"category": "rights_benefits", "title": m(lang, "opp_disc_title", amt=round(amt)),
                      "why": m(lang, "opp_disc_why", day=disc["day"], platform=disc["platform"], amt=round(amt)),
                      "evidence": [f"Figures add up to Rs {disc['discrepancy']['expected_payout']:.0f}, received Rs {disc['received']:.0f}"],
                      "impact": {"value": round(amt, 2), "basis": "estimated", "note": "possible missing payment - not money received"},
                      "confidence": "medium", "effort": "medium", "next": {"label": m(lang, "opp_disc_next"), "href": "/earnings?tab=xray"}})
    elif sub:
        items.append({"category": "rights_benefits", "title": m(lang, "opp_griev_title", company=sub["company"]), "why": m(lang, "opp_griev_why", day=sub["submitted_on"]),
                      "evidence": [f"Follow-up dates: {', '.join(sub['follow_ups'])}"], "impact": None, "confidence": "medium", "effort": "low",
                      "next": {"label": m(lang, "opp_griev_next"), "href": "/rights?tab=grievance"}})
    else:
        items.append({"category": "rights_benefits", "title": m(lang, "opp_scheme_title"), "why": m(lang, "opp_scheme_why"),
                      "evidence": ["No saved welfare schemes"] if not ledger.tracker_get(user) else [f"{len(ledger.tracker_get(user))} saved"],
                      "impact": None, "confidence": "none", "effort": "medium", "next": {"label": m(lang, "opp_scheme_next"), "href": "/rights?tab=schemes"}})
    return {"data_source": earn.data_source(user), "items": items,
            "safety_note": "Never work unsafe hours, take risky loans or overspend because of a suggestion. Rest and safety come first."}
