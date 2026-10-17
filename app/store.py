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
            CREATE TABLE IF NOT EXISTS shifts (
              id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT NOT NULL, day TEXT NOT NULL, platform TEXT NOT NULL DEFAULT 'other',
              hours REAL NOT NULL DEFAULT 0, start_hour INTEGER, gross REAL NOT NULL DEFAULT 0, commission REAL NOT NULL DEFAULT 0,
              deductions REAL NOT NULL DEFAULT 0, incentive REAL NOT NULL DEFAULT 0, fuel REAL NOT NULL DEFAULT 0, other_expenses REAL NOT NULL DEFAULT 0,
              promised REAL, received REAL, source TEXT NOT NULL DEFAULT 'manual', is_demo INTEGER NOT NULL DEFAULT 0, note TEXT DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS ix_shifts_user ON shifts(user, day);
            CREATE TABLE IF NOT EXISTS wage_diary (
              id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT NOT NULL, day TEXT NOT NULL, employer TEXT NOT NULL DEFAULT '',
              work TEXT NOT NULL DEFAULT '', hours REAL NOT NULL DEFAULT 0, promised REAL NOT NULL DEFAULT 0, received REAL NOT NULL DEFAULT 0,
              is_demo INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS impact (
              id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT NOT NULL, day TEXT NOT NULL, kind TEXT NOT NULL, amount REAL NOT NULL DEFAULT 0,
              basis TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', is_demo INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS tracker (
              user TEXT NOT NULL, scheme_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'saved', reminder TEXT, checklist TEXT NOT NULL DEFAULT '{}',
              updated TEXT NOT NULL, is_demo INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (user, scheme_id)
            );
            CREATE TABLE IF NOT EXISTS grievances (
              id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT NOT NULL, kind TEXT NOT NULL, company TEXT NOT NULL, facts TEXT NOT NULL DEFAULT '{}',
              letter TEXT NOT NULL DEFAULT '', letter_local TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'draft',
              timeline TEXT NOT NULL DEFAULT '[]', evidence TEXT NOT NULL DEFAULT '[]', created TEXT NOT NULL, updated TEXT NOT NULL,
              submitted_on TEXT, is_demo INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS evidence (
              id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT NOT NULL, day TEXT NOT NULL, kind TEXT NOT NULL, title TEXT NOT NULL,
              data TEXT NOT NULL DEFAULT '{}', is_demo INTEGER NOT NULL DEFAULT 0
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


# ---- generic helpers used by the service modules ----
def q(sql: str, args=()) -> List[Dict]:
    with _lock:
        return [dict(r) for r in _db().execute(sql, args)]


def x(sql: str, args=()) -> int:
    """Execute a write; returns lastrowid."""
    with _lock:
        c = _db()
        cur = c.execute(sql, args)
        c.commit()
        return cur.lastrowid


USER_TABLES = ["entries", "shifts", "wage_diary", "impact", "tracker", "grievances", "evidence", "vault"]


def delete_user(user: str) -> Dict[str, int]:
    """Right to erasure: remove every row belonging to the user."""
    out = {}
    with _lock:
        c = _db()
        for t in USER_TABLES:
            out[t] = c.execute(f"DELETE FROM {t} WHERE user=?", (user,)).rowcount
        c.commit()
    return out


def export_user(user: str) -> Dict[str, List[Dict]]:
    return {t: q(f"SELECT * FROM {t} WHERE user=?", (user,)) for t in USER_TABLES}
