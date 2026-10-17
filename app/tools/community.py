"""Collective Voice: anonymous reports pooled into group petitions. A petition is only produced
once at least K workers reported the same issue (k-anonymity), so nobody is singled out."""
from typing import Dict, List

from .. import i18n, store

K = 3


def groups(lang: str) -> List[Dict]:
    out = []
    for g in store.report_groups():
        item = {"company": g["company"], "issue": g["issue"], "city": g["city"], "count": g["n"], "petition": None}
        if g["n"] >= K:
            item["petition"] = i18n.t(lang, "petition", n=g["n"], company=g["company"].title(), issue=g["issue"], city=g["city"].title())
        else:
            item["message"] = i18n.t(lang, "petition_wait", n=g["n"])
        out.append(item)
    return out
