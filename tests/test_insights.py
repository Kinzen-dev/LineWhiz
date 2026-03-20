"""Tests for free tier tools: get_account_info, get_friend_count, get_message_quota."""

import json

import httpx
import pytest

from src.auth.api_keys import generate_api_key
from src.auth.gate import authorize_tool_call
from src.db.database import init_db
from src.tools.insights import get_account_info, get_friend_count, get_message_quota
from tests.conftest import MockLineClient, make_mock_transport


@pytest.fixture
async def db():
    """In-memory database for tier restriction tests."""
    conn = await init_db(":memory:")
    yield conn
    await conn.close()

# === get_account_info ===


@pytest.mark.asyncio
async def test_get_account_info_success() -> None:
    transport = make_mock_transport({
        "/info": httpx.Response(200, json={
            "displayName": "TestBot",
            "userId": "U1234567890",
            "basicId": "@testbot",
            "premiumId": "@premium",
            "pictureUrl": "https://example.com/pic.jpg",
            "chatMode": "chat",
            "markAsReadMode": "auto",
        }),
    })
    client = MockLineClient(transport)
    result = json.loads(await get_account_info(client))

    assert result["bot_name"] == "TestBot"
    assert result["user_id"] == "U1234567890"
    assert result["basic_id"] == "@testbot"
    assert result["picture_url"] == "https://example.com/pic.jpg"


@pytest.mark.asyncio
async def test_get_account_info_api_error() -> None:
    transport = make_mock_transport({
        "/info": httpx.Response(401, json={"message": "Unauthorized"}),
    })
    client = MockLineClient(transport)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await get_account_info(client)
    assert exc_info.value.response.status_code == 401


@pytest.mark.asyncio
async def test_get_account_info_missing_fields() -> None:
    """Fields not returned by API should default to N/A."""
    transport = make_mock_transport({
        "/info": httpx.Response(200, json={"displayName": "Minimal"}),
    })
    client = MockLineClient(transport)
    result = json.loads(await get_account_info(client))

    assert result["bot_name"] == "Minimal"
    assert result["premium_id"] == "N/A"
    assert result["picture_url"] == "N/A"


# === get_friend_count ===


@pytest.mark.asyncio
async def test_get_friend_count_success() -> None:
    transport = make_mock_transport({
        "/insight/followers": httpx.Response(200, json={
            "status": "ready",
            "followers": 1500,
            "targetedReaches": 1200,
            "blocks": 50,
        }),
    })
    client = MockLineClient(transport)
    result = json.loads(await get_friend_count(client, date="20260315"))

    assert result["date"] == "20260315"
    assert result["followers"] == 1500
    assert result["targeted_reaches"] == 1200
    assert result["blocks"] == 50
    assert result["status"] == "ready"


@pytest.mark.asyncio
async def test_get_friend_count_default_date() -> None:
    """Omitting date should use yesterday's date."""
    transport = make_mock_transport({
        "/insight/followers": httpx.Response(200, json={
            "status": "ready",
            "followers": 100,
            "targetedReaches": 80,
            "blocks": 5,
        }),
    })
    client = MockLineClient(transport)
    result = json.loads(await get_friend_count(client))

    # Date should be set (yesterday), just verify it's 8 digits
    assert len(result["date"]) == 8
    assert result["date"].isdigit()


@pytest.mark.asyncio
async def test_get_friend_count_api_error() -> None:
    transport = make_mock_transport({
        "/insight/followers": httpx.Response(400, json={"message": "Invalid date"}),
    })
    client = MockLineClient(transport)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await get_friend_count(client, date="invalid")
    assert exc_info.value.response.status_code == 400


# === get_message_quota ===


@pytest.mark.asyncio
async def test_get_message_quota_success() -> None:
    transport = make_mock_transport({
        "/message/quota/consumption": httpx.Response(200, json={"totalUsage": 3500}),
        "/message/quota": httpx.Response(200, json={"type": "limited", "value": 10000}),
    })
    client = MockLineClient(transport)
    result = json.loads(await get_message_quota(client))

    assert result["quota_type"] == "limited"
    assert result["total_quota"] == 10000
    assert result["used_this_month"] == 3500
    assert result["remaining"] == 6500


@pytest.mark.asyncio
async def test_get_message_quota_unlimited() -> None:
    """When total quota is 0, remaining should be 'unlimited'."""
    transport = make_mock_transport({
        "/message/quota/consumption": httpx.Response(200, json={"totalUsage": 100}),
        "/message/quota": httpx.Response(200, json={"type": "none", "value": 0}),
    })
    client = MockLineClient(transport)
    result = json.loads(await get_message_quota(client))

    assert result["remaining"] == "unlimited"


@pytest.mark.asyncio
async def test_get_message_quota_api_error() -> None:
    transport = make_mock_transport({
        "/message/quota": httpx.Response(500, json={"message": "Server error"}),
    })
    client = MockLineClient(transport)

    with pytest.raises(httpx.HTTPStatusError):
        await get_message_quota(client)


# === Tier restriction tests ===
# Free tier tools should be accessible by all tiers.
# These verify the gate correctly allows free-tier tools.


@pytest.mark.asyncio
async def test_get_account_info_allowed_for_free_tier(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")
    await authorize_tool_call(db, key, "get_account_info")


@pytest.mark.asyncio
async def test_get_friend_count_allowed_for_free_tier(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")
    await authorize_tool_call(db, key, "get_friend_count")


@pytest.mark.asyncio
async def test_get_message_quota_allowed_for_free_tier(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")
    await authorize_tool_call(db, key, "get_message_quota")
