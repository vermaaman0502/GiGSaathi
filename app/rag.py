"""Small dependency-free BM25 retriever over data/schemes.json.
Swap for pgvector/Qdrant + multilingual embeddings when the corpus grows."""
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List

DATA = Path(__file__).resolve().parent.parent / "data" / "schemes.json"
_TOKEN = re.compile(r"[\wऀ-ॿ]+")
MIN_SCORE = 1.0


STOP = set("a an the is are am was of to for in on at and or my me i you we it this that what how do does can get with by be from as please tell about which who when where kya hai ka ki ke ko se mein me hain hoon main mera meri aur ya".split())


def _tok(text: str) -> List[str]:
    toks = [t.lower() for t in _TOKEN.findall(text) if t.lower() not in STOP]
    return [t[:6] if t.isascii() and len(t) > 6 else t for t in toks]     # crude stem: register ~ registration


class Retriever:
    def __init__(self, docs: List[Dict]):
        self.docs = docs
        self.toks = [_tok(" ".join([d["title"], d["keywords"], d["title"], d["keywords"], d["summary"]] + [v for loc in (d.get("i18n") or {}).values() for v in loc.values()])) for d in docs]
        self.avgdl = sum(len(t) for t in self.toks) / max(len(self.toks), 1)
        df = Counter()
        for t in self.toks:
            df.update(set(t))
        n = len(docs)
        self.idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}

    def search(self, query: str, k: int = 3) -> List[Dict]:
        q = _tok(query)
        scored = []
        for doc, toks in zip(self.docs, self.toks):
            tf = Counter(toks)
            score = 0.0
            for w in q:
                if w in tf:
                    f = tf[w]
                    score += self.idf.get(w, 0) * f * 2.2 / (f + 1.2 * (0.25 + 0.75 * len(toks) / self.avgdl))
            if score >= MIN_SCORE:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:k]]


_retriever = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever(json.loads(DATA.read_text(encoding="utf-8")))
    return _retriever


def match_schemes(age: int, monthly_income: float, epfo_member: bool = False, has_bank: bool = True,
                  income_tax_payer: bool = False, street_vendor: bool = False) -> List[Dict]:
    """Legacy lite-UI wrapper over the structured evaluator in app.schemes (drops ruled-out schemes)."""
    from . import schemes
    answers = {"age": age, "monthly_income": monthly_income, "epfo_member": epfo_member, "has_bank": has_bank,
               "income_tax_payer": income_tax_payer, "street_vendor": street_vendor, "nps_member": False, "govt_pension": False}
    out = []
    for c in schemes.match(answers):
        if c["state"] == "appears_ineligible" or (c["missing"] and c["state"] == "more_info_needed" and not c["why_qualify"]):
            continue
        scheme = schemes.get(c["id"])
        out.append({"scheme": scheme, "why": "; ".join(c["why_qualify"]) or c["state_label"], "state": c["state"]})
    return out
