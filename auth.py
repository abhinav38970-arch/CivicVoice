"""CivicVoice accounts: SQLite user store with werkzeug password hashing.

Tables:
  users(id, email, name, language, password_hash, created_at)
  reports(id, user_id, issue, description, location, created_at)  -- saved 311 reports

The database file lives at data/users.db and is gitignored (user data).
"""
import os
import sqlite3
import time

from werkzeug.security import generate_password_hash, check_password_hash

REPO = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(REPO, "data", "users.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    password_hash TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    issue TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL
);
"""


def _db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def create_user(email, name, password, language="en"):
    """Create a user. Returns (user_dict, None) or (None, error_code)."""
    email = (email or "").strip().lower()
    name = (name or "").strip()
    if not email or "@" not in email:
        return None, "bad_email"
    if not name:
        return None, "bad_name"
    if not password or len(password) < 6:
        return None, "bad_password"
    conn = _db()
    try:
        cur = conn.execute(
            "INSERT INTO users (email, name, language, password_hash, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (email, name, language, generate_password_hash(password),
             int(time.time())),
        )
        conn.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return None, "email_taken"
    row = conn.execute("SELECT id, email, name, language FROM users WHERE id = ?",
                       (user_id,)).fetchone()
    conn.close()
    return dict(row), None


def verify_user(email, password):
    """Check credentials. Returns user_dict or None."""
    email = (email or "").strip().lower()
    conn = _db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if row is None:
        return None
    if not check_password_hash(row["password_hash"], password or ""):
        return None
    return {"id": row["id"], "email": row["email"], "name": row["name"],
            "language": row["language"]}


def get_user(user_id):
    conn = _db()
    row = conn.execute(
        "SELECT id, email, name, language FROM users WHERE id = ?",
        (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def set_language(user_id, language):
    conn = _db()
    conn.execute("UPDATE users SET language = ? WHERE id = ?",
                 (language, user_id))
    conn.commit()
    conn.close()


def save_report(user_id, issue, description, location=""):
    conn = _db()
    cur = conn.execute(
        "INSERT INTO reports (user_id, issue, description, location, created_at)"
        " VALUES (?, ?, ?, ?, ?)",
        (user_id, issue, description, location, int(time.time())),
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


def list_reports(user_id, limit=10):
    conn = _db()
    rows = conn.execute(
        "SELECT id, issue, description, location, created_at FROM reports"
        " WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
