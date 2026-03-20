"""Tool call gating — validates API key, tier access, and daily limits."""

import aiosqlite

from src.auth.api_keys import validate_api_key
from src.auth.tiers import (
    get_daily_limit,
    get_limit_exceeded_message,
    get_upgrade_message,
    is_tool_allowed,
)
from src.models.usage import check_within_limit, record_usage


class GateError(Exception):
    """Raised when a tool call is blocked by gating checks."""


async def authorize_tool_call(
    conn: aiosqlite.Connection,
    api_key: str,
    tool_name: str,
) -> None:
    """Run all gating checks for a tool call. Raises GateError if blocked.

    ตรวจสอบสิทธิ์การเรียกใช้เครื่องมือ — API key, แผน, และจำนวนครั้ง/วัน

    Steps:
    1. Validate the API key
    2. Check if the key is active
    3. Check if the tool is allowed for the user's tier
    4. Check if daily call limit is exceeded
    5. Record the usage
    """
    # 1. Validate API key
    key_info = await validate_api_key(conn, api_key)
    if key_info is None:
        raise GateError(
            "API key ไม่ถูกต้องหรือไม่พบในระบบ\n"
            "Invalid or unknown API key."
        )

    # 2. Check if active
    if not key_info.is_active:
        raise GateError(
            "API key นี้ถูกปิดการใช้งานแล้ว กรุณาติดต่อฝ่ายสนับสนุน\n"
            "This API key has been deactivated. Please contact support."
        )

    # 3. Check tier access
    if not is_tool_allowed(key_info.tier, tool_name):
        raise GateError(get_upgrade_message(key_info.tier, tool_name))

    # 4. Check daily limit
    daily_limit = get_daily_limit(key_info.tier)
    if not await check_within_limit(conn, api_key, daily_limit):
        raise GateError(get_limit_exceeded_message(key_info.tier, daily_limit))

    # 5. Record usage
    await record_usage(conn, api_key, tool_name)
