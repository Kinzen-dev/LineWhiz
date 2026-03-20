"""SQLite async database initialization and migrations.

Uses aiosqlite for async access. Schema matches CLAUDE.md spec.
"""

from __future__ import annotations

import logging

import aiosqlite

from src.config import get_settings

logger = logging.getLogger("linewhiz.db")

_db: aiosqlite.Connection | None = None

SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS api_keys (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash    TEXT    NOT NULL UNIQUE,
    tier        TEXT    NOT NULL DEFAULT 'free',
    label       TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);

CREATE TABLE IF NOT EXISTS usage_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id  INTEGER NOT NULL REFERENCES api_keys(id),
    tool_name   TEXT    NOT NULL,
    success     INTEGER NOT NULL DEFAULT 1,
    error_msg   TEXT,
    called_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_usage_api_date ON usage_logs(api_key_id, called_at);
"""


async def get_db() -> aiosqlite.Connection:
    """Get or create the database connection."""
    global _db  # noqa: PLW0603
    if _db is None:
        settings = get_settings()
        # Extract path from sqlite:///path format
        db_path = settings.linewhiz_database_url.replace("sqlite:///", "")
        _db = await aiosqlite.connect(db_path)
        _db.row_factory = aiosqlite.Row
        await _db.executescript(SQL_SCHEMA)
        logger.info("Database initialized at %s", db_path)
    return _db


async def close_db() -> None:
    """Close the database connection."""
    global _db  # noqa: PLW0603
    if _db is not None:
        await _db.close()
        _db = None
        logger.info("Database connection closed")


async def log_usage(
    api_key_id: int,
    tool_name: str,
    *,
    success: bool = True,
    error_msg: str | None = None,
) -> None:
    """Log a tool call to the usage_logs table."""
    db = await get_db()
    await db.execute(
        "INSERT INTO usage_logs (api_key_id, tool_name, success, error_msg) VALUES (?, ?, ?, ?)",
        (api_key_id, tool_name, int(success), error_msg),
    )
    await db.commit()


async def get_daily_usage_count(api_key_id: int) -> int:
    """Get the number of tool calls made today by an API key."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT COUNT(*) FROM usage_logs WHERE api_key_id = ? AND called_at >= date('now')",
        (api_key_id,),
    )
    row = await cursor.fetchone()
    return row[0] if row else 0
