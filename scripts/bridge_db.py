"""SQLite store for per-session results.

Schema:
  clubs      — one row per club (slug + metadata)
  sessions   — one row per (club, session_date); pairs/ngs captured live

Status is computed at query time, not stored — thresholds may evolve.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "data" / "bridge_results.db"

PAIRS_THRESHOLD = 14
NGS_THRESHOLD = 52.0  # strictly greater than this


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clubs (
            slug          TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            day           TEXT NOT NULL,
            time_uk       TEXT NOT NULL,
            results_url   TEXT NOT NULL,
            platform      TEXT NOT NULL,
            updated_at    TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            club_slug      TEXT NOT NULL,
            session_date   TEXT NOT NULL,
            event_id       TEXT,
            pairs          INTEGER,
            ngs            REAL,
            fetched_at     TEXT NOT NULL,
            PRIMARY KEY (club_slug, session_date),
            FOREIGN KEY (club_slug) REFERENCES clubs(slug) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(session_date);
    """)
    conn.commit()


def upsert_club(conn, slug, name, day, time_uk, results_url, platform):
    conn.execute("""
        INSERT INTO clubs (slug, name, day, time_uk, results_url, platform, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(slug) DO UPDATE SET
            name=excluded.name,
            day=excluded.day,
            time_uk=excluded.time_uk,
            results_url=excluded.results_url,
            platform=excluded.platform,
            updated_at=excluded.updated_at
    """, (slug, name, day, time_uk, results_url, platform, datetime.utcnow().isoformat()))


def record_session(conn, slug, session_date, event_id, pairs, ngs):
    conn.execute("""
        INSERT INTO sessions (club_slug, session_date, event_id, pairs, ngs, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(club_slug, session_date) DO UPDATE SET
            event_id=excluded.event_id,
            pairs=COALESCE(excluded.pairs, sessions.pairs),
            ngs=COALESCE(excluded.ngs, sessions.ngs),
            fetched_at=excluded.fetched_at
    """, (slug, session_date, event_id, pairs, ngs, datetime.utcnow().isoformat()))


def latest_per_club(conn, day=None):
    """Return list of dicts: one row per club with latest session's pairs+ngs."""
    sql = """
        SELECT
          c.slug, c.name, c.day, c.time_uk, c.results_url, c.platform,
          s.session_date, s.pairs, s.ngs
        FROM clubs c
        LEFT JOIN sessions s ON s.club_slug = c.slug AND s.session_date = (
            SELECT MAX(session_date) FROM sessions WHERE club_slug = c.slug
        )
    """
    params = ()
    if day:
        sql += " WHERE c.day = ?"
        params = (day,)
    sql += " ORDER BY c.time_uk, c.name"
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def classify(pairs, ngs):
    """Return one of: include / exclude_pairs / exclude_ngs / exclude_both / no_data."""
    if pairs is None and ngs is None:
        return "no_data"
    pairs_ok = pairs is not None and pairs >= PAIRS_THRESHOLD
    ngs_ok = ngs is not None and ngs > NGS_THRESHOLD
    if pairs_ok and ngs_ok:
        return "include"
    if not pairs_ok and not ngs_ok:
        return "exclude_both"
    if not pairs_ok:
        return "exclude_pairs"
    return "exclude_ngs"
