"""Tests for auth: API keys, tier gating, usage tracking, and full gate flow."""

import pytest

from src.auth.api_keys import (
    deactivate_api_key,
    generate_api_key,
    update_tier,
    validate_api_key,
)
from src.auth.gate import GateError, authorize_tool_call
from src.auth.tiers import (
    get_daily_limit,
    get_limit_exceeded_message,
    get_upgrade_message,
    is_tool_allowed,
)
from src.db.database import init_db
from src.models.usage import get_daily_usage, record_usage


@pytest.fixture
async def db():
    """Create an in-memory SQLite database for testing."""
    conn = await init_db(":memory:")
    yield conn
    await conn.close()


# =============================================================
# API Keys
# =============================================================


@pytest.mark.asyncio
async def test_generate_api_key(db) -> None:
    key = await generate_api_key(db, user_id="user1")

    assert key.startswith("lw_")
    assert len(key) > 10


@pytest.mark.asyncio
async def test_validate_api_key_success(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="pro")
    info = await validate_api_key(db, key)

    assert info is not None
    assert info.user_id == "user1"
    assert info.tier == "pro"
    assert info.is_active is True


@pytest.mark.asyncio
async def test_validate_api_key_not_found(db) -> None:
    info = await validate_api_key(db, "lw_nonexistent")

    assert info is None


@pytest.mark.asyncio
async def test_deactivate_api_key(db) -> None:
    key = await generate_api_key(db, user_id="user1")
    result = await deactivate_api_key(db, key)

    assert result is True
    info = await validate_api_key(db, key)
    assert info is not None
    assert info.is_active is False


@pytest.mark.asyncio
async def test_deactivate_nonexistent_key(db) -> None:
    result = await deactivate_api_key(db, "lw_fake")

    assert result is False


@pytest.mark.asyncio
async def test_update_tier(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")
    result = await update_tier(db, key, "pro")

    assert result is True
    info = await validate_api_key(db, key)
    assert info is not None
    assert info.tier == "pro"


# =============================================================
# Tiers
# =============================================================


def test_free_tier_allows_account_info() -> None:
    assert is_tool_allowed("free", "get_account_info") is True


def test_free_tier_allows_friend_count() -> None:
    assert is_tool_allowed("free", "get_friend_count") is True


def test_free_tier_allows_message_quota() -> None:
    assert is_tool_allowed("free", "get_message_quota") is True


def test_free_tier_blocks_broadcast() -> None:
    assert is_tool_allowed("free", "send_broadcast") is False


def test_free_tier_blocks_rich_menu() -> None:
    assert is_tool_allowed("free", "list_rich_menus") is False


def test_pro_tier_allows_broadcast() -> None:
    assert is_tool_allowed("pro", "send_broadcast") is True


def test_pro_tier_allows_rich_menu() -> None:
    assert is_tool_allowed("pro", "list_rich_menus") is True


def test_pro_tier_allows_all_13_tools() -> None:
    pro_tools = [
        "get_account_info", "get_friend_count", "get_message_quota",
        "send_broadcast", "send_push_message", "send_multicast",
        "send_narrowcast", "get_message_stats", "get_user_profile",
        "list_rich_menus", "create_rich_menu",
        "set_default_rich_menu", "link_rich_menu_to_user",
    ]
    for tool in pro_tools:
        assert is_tool_allowed("pro", tool) is True, f"Pro should allow {tool}"


def test_business_tier_allows_everything() -> None:
    assert is_tool_allowed("business", "get_account_info") is True
    assert is_tool_allowed("business", "send_broadcast") is True
    assert is_tool_allowed("business", "any_future_tool") is True


def test_unknown_tier_blocks_all() -> None:
    assert is_tool_allowed("unknown", "get_account_info") is False


def test_daily_limits() -> None:
    assert get_daily_limit("free") == 100
    assert get_daily_limit("pro") == 5000
    assert get_daily_limit("business") == -1
    assert get_daily_limit("unknown") == 0


def test_upgrade_message_free() -> None:
    msg = get_upgrade_message("free", "send_broadcast")
    assert "send_broadcast" in msg
    assert "Pro" in msg
    assert "฿500" in msg
    assert "อัปเกรด" in msg


def test_upgrade_message_pro() -> None:
    msg = get_upgrade_message("pro", "some_business_tool")
    assert "Business" in msg
    assert "฿1,500" in msg


def test_limit_exceeded_message_free() -> None:
    msg = get_limit_exceeded_message("free", 100)
    assert "100" in msg
    assert "Pro" in msg
    assert "ครั้ง/วัน" in msg


def test_limit_exceeded_message_pro() -> None:
    msg = get_limit_exceeded_message("pro", 5000)
    assert "5,000" in msg
    assert "Business" in msg


# =============================================================
# Usage Tracking
# =============================================================


@pytest.mark.asyncio
async def test_record_and_get_usage(db) -> None:
    key = await generate_api_key(db, user_id="user1")

    await record_usage(db, key, "get_account_info")
    await record_usage(db, key, "get_friend_count")
    await record_usage(db, key, "get_account_info")

    usage = await get_daily_usage(db, key)
    assert usage == 3


@pytest.mark.asyncio
async def test_usage_zero_for_new_key(db) -> None:
    key = await generate_api_key(db, user_id="user1")

    usage = await get_daily_usage(db, key)
    assert usage == 0


# =============================================================
# Full Gate Flow (authorize_tool_call)
# =============================================================


@pytest.mark.asyncio
async def test_gate_free_allowed_tool(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")

    # Should not raise
    await authorize_tool_call(db, key, "get_account_info")

    usage = await get_daily_usage(db, key)
    assert usage == 1


@pytest.mark.asyncio
async def test_gate_free_blocked_tool(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")

    with pytest.raises(GateError, match="Pro"):
        await authorize_tool_call(db, key, "send_broadcast")


@pytest.mark.asyncio
async def test_gate_free_daily_limit_exceeded(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")

    # Fill up 100 calls
    for _ in range(100):
        await record_usage(db, key, "get_account_info")

    with pytest.raises(GateError, match="100"):
        await authorize_tool_call(db, key, "get_account_info")


@pytest.mark.asyncio
async def test_gate_pro_allowed_tool(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="pro")

    await authorize_tool_call(db, key, "send_broadcast")

    usage = await get_daily_usage(db, key)
    assert usage == 1


@pytest.mark.asyncio
async def test_gate_pro_daily_limit(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="pro")

    for _ in range(5000):
        await record_usage(db, key, "send_broadcast")

    with pytest.raises(GateError, match="5,000"):
        await authorize_tool_call(db, key, "send_broadcast")


@pytest.mark.asyncio
async def test_gate_business_unlimited(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="business")

    # Record many calls — should never hit limit
    for _ in range(200):
        await record_usage(db, key, "get_account_info")

    # Should still work
    await authorize_tool_call(db, key, "get_account_info")
    await authorize_tool_call(db, key, "any_future_tool")


@pytest.mark.asyncio
async def test_gate_invalid_api_key(db) -> None:
    with pytest.raises(GateError, match="ไม่ถูกต้อง"):
        await authorize_tool_call(db, "lw_fake_key", "get_account_info")


@pytest.mark.asyncio
async def test_gate_deactivated_key(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="pro")
    await deactivate_api_key(db, key)

    with pytest.raises(GateError, match="ปิดการใช้งาน"):
        await authorize_tool_call(db, key, "get_account_info")
