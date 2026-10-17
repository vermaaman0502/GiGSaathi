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
    return [t.lower() for t in _TOKEN.findall(text) if t.lower() not in STOP]


class Retriever:
    def __init__(self, docs: List[Dict]):
        self.docs = docs
        self.toks = [_tok(" ".join([d["title"], d["keywords"], d["summary"]])) for d in docs]
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
    """Rule-based Scheme Matchmaker. Returns ids with reason; always says 'confirm on portal'."""
    r = get_retriever()
    by_id = {d["id"]: d for d in r.docs}
    ids = []
    if 16 <= age <= 59 and not epfo_member and not income_tax_payer:
        ids.append(("eshram", "Age 16-59 and not in EPFO/ESIC"))
    if 18 <= age <= 40 and monthly_income <= 15000 and not epfo_member and has_bank:
        ids.append(("pmsym", "Age 18-40 with income up to Rs 15,000"))
    if 18 <= age <= 40 and has_bank:
        ids.append(("apy", "Age 18-40 with a bank account"))
    if 18 <= age <= 70 and has_bank:
        ids.append(("pmsby", "Age 18-70 with a bank account"))
    if 18 <= age <= 50 and has_bank:
        ids.append(("pmjjby", "Age 18-50 with a bank account"))
    ids.append(("pmjay", "Check family eligibility; gig workers may be covered"))
    if street_vendor:
        ids.append(("svanidhi", "You are a street vendor"))
    ids.append(("mudra", "For tools/vehicle instead of high-interest loans"))
    ids.append(("pmkvy", "Free training to move up"))
    return [{"scheme": by_id[i], "why": why} for i, why in ids if i in by_id]
