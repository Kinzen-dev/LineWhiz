"""SQLite async connection + migrations."""

import aiosqlite

MIGRATIONS = [
    # v1: initial schema
    """
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        user_id TEXT NOT NULL,
        tier TEXT NOT NULL DEFAULT 'free',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        is_active INTEGER NOT NULL DEFAULT 1
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS usage_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_key TEXT NOT NULL,
        tool_name TEXT NOT NULL,
        called_at TEXT NOT NULL DEFAULT (datetime('now')),
        date_key TEXT NOT NULL
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_usage_date
    ON usage_logs (api_key, date_key);
    """,
]


async def get_connection(db_path: str = "linewhiz.db") -> aiosqlite.Connection:
    """Open an async SQLite connection."""
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL;")
    return conn


async def run_migrations(conn: aiosqlite.Connection) -> None:
    """Run all database migrations."""
    for sql in MIGRATIONS:
        await conn.executescript(sql)
    await conn.commit()


async def init_db(db_path: str = "linewhiz.db") -> aiosqlite.Connection:
    """Initialize database: connect and run migrations."""
    conn = await get_connection(db_path)
    await run_migrations(conn)
    return conn
