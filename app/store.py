"""Tiny SQLite store for wage diary, income and expenses. Stores only what the feature needs.
On serverless hosts the default /tmp path is ephemeral - point DB_PATH at a volume or swap for Postgres."""
import os
import sqlite3
import threading
from datetime import date
from typing import Dict, List, Optional

DB_PATH = os.environ.get("DB_PATH", "/tmp/gigsaathi.db")
_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None


def _db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS entries (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user TEXT NOT NULL, day TEXT NOT NULL,
              kind TEXT NOT NULL,            -- income | expense | diary
              category TEXT, amount REAL, note TEXT
            );
            CREATE INDEX IF NOT EXISTS ix_entries_user ON entries(user, day);
            CREATE TABLE IF NOT EXISTS vault (
              user TEXT NOT NULL, doc_type TEXT NOT NULL, expiry TEXT NOT NULL,
              PRIMARY KEY (user, doc_type)
            );
            -- Collective Voice: deliberately has NO user column (anonymous by design).
            CREATE TABLE IF NOT EXISTS reports (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              day TEXT NOT NULL, company TEXT NOT NULL, issue TEXT NOT NULL, city TEXT NOT NULL
            );
            """
        )
    return _conn


def add(user: str, kind: str, amount: float = 0.0, category: str = "", note: str = "", day: Optional[str] = None) -> None:
    with _lock:
        c = _db()
        c.execute("INSERT INTO entries(user,day,kind,category,amount,note) VALUES (?,?,?,?,?,?)",
                  (user, day or date.today().isoformat(), kind, category, amount, note))
        c.commit()


def entries(user: str, kind: str, day: Optional[str] = None) -> List[Dict]:
    with _lock:
        q, args = "SELECT * FROM entries WHERE user=? AND kind=?", [user, kind]
        if day:
            q += " AND day=?"
            args.append(day)
        return [dict(r) for r in _db().execute(q + " ORDER BY id", args)]


def daily_summary(user: str, day: Optional[str] = None) -> Dict:
    day = day or date.today().isoformat()
    earned = sum(e["amount"] for e in entries(user, "income", day))
    spent = sum(e["amount"] for e in entries(user, "expense", day))
    return {"day": day, "earned": round(earned, 2), "spent": round(spent, 2), "saved": round(earned - spent, 2)}


def reset_for_tests(path: str) -> None:
    global _conn, DB_PATH
    if _conn is not None:
        _conn.close()
    _conn = None
    DB_PATH = path


def vault_set(user: str, doc_type: str, expiry: str) -> None:
    with _lock:
        c = _db()
        c.execute("INSERT OR REPLACE INTO vault(user,doc_type,expiry) VALUES (?,?,?)", (user, doc_type, expiry))
        c.commit()


def vault_list(user: str) -> List[Dict]:
    with _lock:
        return [dict(r) for r in _db().execute("SELECT doc_type, expiry FROM vault WHERE user=? ORDER BY expiry", (user,))]


def report_add(company: str, issue: str, city: str) -> None:
    with _lock:
        c = _db()
        c.execute("INSERT INTO reports(day,company,issue,city) VALUES (?,?,?,?)",
                  (date.today().isoformat(), company.strip().lower(), issue.strip().lower(), city.strip().lower()))
        c.commit()


def report_groups() -> List[Dict]:
    with _lock:
        rows = _db().execute("SELECT company, issue, city, COUNT(*) AS n FROM reports GROUP BY company, issue, city ORDER BY n DESC").fetchall()
        return [dict(r) for r in rows]


def monthly_totals(user: str) -> List[Dict]:
    """Per-category expense totals for the Leak Finder."""
    return entries(user, "expense")
