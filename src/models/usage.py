"""Usage tracking — count calls per day per API key."""

from datetime import datetime, timezone

import aiosqlite


def _today_key() -> str:
    """Get today's date key in YYYYMMDD format (UTC)."""
    return datetime.now(timezone.utc).strftime("%Y%m%d")


async def record_usage(
    conn: aiosqlite.Connection,
    api_key: str,
    tool_name: str,
) -> None:
    """Record a tool call for usage tracking.

    บันทึกการเรียกใช้เครื่องมือสำหรับการติดตามการใช้งาน
    """
    date_key = _today_key()
    await conn.execute(
        "INSERT INTO usage_logs (api_key, tool_name, date_key) VALUES (?, ?, ?)",
        (api_key, tool_name, date_key),
    )
    await conn.commit()


async def get_daily_usage(
    conn: aiosqlite.Connection,
    api_key: str,
    date_key: str | None = None,
) -> int:
    """Get the number of tool calls made today (or on a specific date).

    ดึงจำนวนครั้งที่เรียกใช้เครื่องมือวันนี้ (หรือวันที่ระบุ)
    """
    if date_key is None:
        date_key = _today_key()

    cursor = await conn.execute(
        "SELECT COUNT(*) FROM usage_logs WHERE api_key = ? AND date_key = ?",
        (api_key, date_key),
    )
    row = await cursor.fetchone()
    return row[0] if row else 0


async def check_within_limit(
    conn: aiosqlite.Connection,
    api_key: str,
    daily_limit: int,
) -> bool:
    """Check if the API key is within its daily call limit.

    ตรวจสอบว่า API key ยังอยู่ในจำนวนครั้งที่จำกัดต่อวัน
    Returns True if within limit, False if exceeded.
    -1 means unlimited (always returns True).
    """
    if daily_limit == -1:
        return True

    usage = await get_daily_usage(conn, api_key)
    return usage < daily_limit
