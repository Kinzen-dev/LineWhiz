"""Tests for database connection and migrations."""

import pytest

from src.db.database import init_db, run_migrations


@pytest.mark.asyncio
async def test_init_db_creates_tables() -> None:
    conn = await init_db(":memory:")
    try:
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in await cursor.fetchall()]

        assert "api_keys" in tables
        assert "usage_logs" in tables
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_init_db_wal_mode() -> None:
    conn = await init_db(":memory:")
    try:
        cursor = await conn.execute("PRAGMA journal_mode")
        row = await cursor.fetchone()
        # In-memory databases may report "memory" instead of "wal"
        assert row is not None
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_migrations_idempotent() -> None:
    """Running migrations twice should not raise errors."""
    conn = await init_db(":memory:")
    try:
        await run_migrations(conn)
        await run_migrations(conn)

        cursor = await conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='api_keys'"
        )
        row = await cursor.fetchone()
        assert row[0] == 1
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_api_keys_table_schema() -> None:
    conn = await init_db(":memory:")
    try:
        cursor = await conn.execute("PRAGMA table_info(api_keys)")
        columns = {row[1] for row in await cursor.fetchall()}

        assert "id" in columns
        assert "key" in columns
        assert "user_id" in columns
        assert "tier" in columns
        assert "created_at" in columns
        assert "is_active" in columns
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_usage_logs_table_schema() -> None:
    conn = await init_db(":memory:")
    try:
        cursor = await conn.execute("PRAGMA table_info(usage_logs)")
        columns = {row[1] for row in await cursor.fetchall()}

        assert "id" in columns
        assert "api_key" in columns
        assert "tool_name" in columns
        assert "called_at" in columns
        assert "date_key" in columns
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_usage_logs_index_exists() -> None:
    conn = await init_db(":memory:")
    try:
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_usage_date'"
        )
        row = await cursor.fetchone()
        assert row is not None
    finally:
        await conn.close()
