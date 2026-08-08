"""
SQLite database layer for the SST Face Mask Detection System.

Uses Streamlit's built-in SQL connector (st.connection), which wraps
SQLAlchemy, and stores everything in a single local .db file — no
server, credentials, or separate database creation step needed.

SETUP:
1. pip install -r requirements.txt   (already includes sqlalchemy)
2. That's it. The first run creates mask_detection.db (and its tables)
   automatically in the project folder via init_db().
"""
import hashlib

import pandas as pd
import streamlit as st
from sqlalchemy import text

# Name of the local SQLite file. It's created automatically on first run,
# in the same folder you launch `streamlit run app.py` from.
DB_PATH = "mask_detection.db"


def get_conn():
    """
    Returns a cached connection to a local SQLite file using Streamlit's
    generic "sql" connection type. Streamlit reuses this connection across
    reruns/users instead of opening a new one every time.

    No secrets.toml entry is required — the SQLite URL is passed directly.
    (If a [connections.sql] entry exists in .streamlit/secrets.toml, that
    would be used instead; we don't rely on that here to keep setup simple.)
    """
    return st.connection("sql", url=f"sqlite:///{DB_PATH}")


def hash_password(password: str) -> str:
    """
    Turns a plaintext password into a SHA-256 hash so raw passwords are
    never stored in the database.

    TODO: for a real production app, use a slower salted algorithm
    instead (e.g. bcrypt or argon2 via the `passlib` package) — sha256
    alone is fast enough to brute-force and has no per-user salt.
    """
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    """
    Creates the tables this app needs, if they don't already exist.
    Safe to call every time the app starts — CREATE TABLE IF NOT EXISTS
    is a no-op once the tables are there.
    """
    conn = get_conn()
    with conn.session as s:
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                full_name VARCHAR(100),
                email VARCHAR(100),
                password_hash VARCHAR(64) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                result VARCHAR(20) NOT NULL,
                confidence FLOAT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS saved (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                UNIQUE (username, filename)
            )
        """))
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                subject VARCHAR(150),
                message TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        s.commit()


# ============================================================
#  AUTH
# ============================================================
def register_user(username: str, password: str, full_name: str = "", email: str = ""):
    """Inserts a new user row. Returns (success: bool, message: str)."""
    conn = get_conn()
    try:
        with conn.session as s:
            s.execute(
            text("INSERT INTO users (username, full_name, email, password_hash) VALUES (:u, :f, :e, :p)"),
                params={"u": username, "f": full_name, "e": email, "p": hash_password(password)},
            )
            s.commit()
        return True, "Account created successfully."
    except Exception as e:
        # Most common case: username already exists (UNIQUE constraint)
        return False, f"Could not create account: {e}"


def get_user(username: str):
    """Returns a dict of {full_name, email, created_at} for this user, or None."""
    conn = get_conn()
    df = conn.query(
        "SELECT full_name, email, created_at FROM users WHERE username = :u",
        params={"u": username},
        ttl=0,
    )
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def verify_user(username: str, password: str) -> bool:
    """Checks a username/password pair against the users table."""
    conn = get_conn()
    df = conn.query(
        "SELECT password_hash FROM users WHERE username = :u",
        params={"u": username},
        ttl=0,   # always hit the DB fresh for auth checks, never use the cache
    )
    if df.empty:
        return False
    return df.iloc[0]["password_hash"] == hash_password(password)


# ============================================================
#  DETECTIONS  (History page)
# ============================================================
def log_detection_db(username: str, filename: str, result: str, confidence: float):
    conn = get_conn()
    with conn.session as s:
        s.execute(
            text("INSERT INTO detections (username, filename, result, confidence) VALUES (:u, :f, :r, :c)"),
            params={"u": username, "f": filename, "r": result, "c": confidence},
        )
        s.commit()


def get_history_db(username: str):
    """Returns this user's detections, most recent first, as a list of dicts."""
    conn = get_conn()
    df = conn.query(
        "SELECT filename, result, confidence, created_at FROM detections "
        "WHERE username = :u ORDER BY created_at DESC",
        params={"u": username},
        ttl=0,
    )
    # SQLite has no native DATETIME type — it stores (and returns) the
    # created_at column as plain text, unlike MySQL which hands back a
    # real datetime object. Parse it explicitly so callers (e.g. the
    # History page's row["created_at"].strftime(...)) keep working the
    # same way regardless of which database backend is in use.
    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"])
    return df.to_dict("records")


# ============================================================
#  SAVED  (Saved page)
# ============================================================
def toggle_saved_db(username: str, filename: str):
    """Adds the row if it's not saved yet, removes it if it already is."""
    conn = get_conn()
    df = conn.query(
        "SELECT id FROM saved WHERE username = :u AND filename = :f",
        params={"u": username, "f": filename},
        ttl=0,
    )
    with conn.session as s:
        if df.empty:
            s.execute(
                text("INSERT INTO saved (username, filename) VALUES (:u, :f)"),
                params={"u": username, "f": filename},
            )
        else:
            s.execute(
                text("DELETE FROM saved WHERE username = :u AND filename = :f"),
                params={"u": username, "f": filename},
            )
        s.commit()


def get_saved_db(username: str):
    """Returns the list of filenames this user has saved."""
    conn = get_conn()
    df = conn.query(
        "SELECT filename FROM saved WHERE username = :u",
        params={"u": username},
        ttl=0,
    )
    return df["filename"].tolist()


# ============================================================
#  CONTACT US
# ============================================================
def save_contact_message(name: str, email: str, subject: str, message: str):
    """Inserts a row into the messages table. Returns (success: bool, message: str)."""
    conn = get_conn()
    try:
        with conn.session as s:
            s.execute(
                text(
                    "INSERT INTO messages (name, email, subject, message) "
                    "VALUES (:n, :e, :s, :m)"
                ),
                params={"n": name, "e": email, "s": subject, "m": message},
            )
            s.commit()
        return True, "Your message has been sent. We'll get back to you soon."
    except Exception as e:
        return False, f"Could not send message: {e}"


# ============================================================
#  VISUALIZATION  (today's detection stats, across all users)
# ============================================================
def get_today_detection_stats():
    """
    Returns a dict {total, mask, no_mask} counting every row in the
    detections table whose created_at date is today (UTC, since
    CURRENT_TIMESTAMP in SQLite is UTC) — combined across every signed-in
    user, so the Visualization page reflects the whole app, not just one
    account.
    """
    conn = get_conn()
    df = conn.query(
        "SELECT result, COUNT(*) AS cnt FROM detections "
        "WHERE date(created_at) = date('now') "
        "GROUP BY result",
        ttl=0,
    )
    counts = {"Mask": 0, "No Mask": 0}
    for _, row in df.iterrows():
        if row["result"] in counts:
            counts[row["result"]] = int(row["cnt"])
    total = counts["Mask"] + counts["No Mask"]
    return {"total": total, "mask": counts["Mask"], "no_mask": counts["No Mask"]}
