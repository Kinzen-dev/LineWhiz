"""Tests for pro tier messaging tools: broadcast, push, multicast, narrowcast."""

import httpx
import pytest

from src.auth.api_keys import generate_api_key
from src.auth.gate import GateError, authorize_tool_call
from src.db.database import init_db
from src.tools.messaging import (
    send_broadcast,
    send_multicast,
    send_narrowcast,
    send_push_message,
)
from tests.conftest import MockLineClient, make_mock_transport


@pytest.fixture
async def db():
    """In-memory database for tier restriction tests."""
    conn = await init_db(":memory:")
    yield conn
    await conn.close()


def _ok_transport(path_key: str) -> httpx.MockTransport:
    """Create a transport that returns 200 OK for the given path."""
    return make_mock_transport({
        path_key: httpx.Response(200, json={"status": "ok"}),
    })


# === send_broadcast ===


@pytest.mark.asyncio
async def test_send_broadcast_text_success() -> None:
    client = MockLineClient(_ok_transport("/message/broadcast"))
    result = await send_broadcast(client, message="สวัสดีครับ")

    assert "สำเร็จ" in result
    assert "เพื่อนทั้งหมด" in result
    assert "สวัสดีครับ" in result


@pytest.mark.asyncio
async def test_send_broadcast_image_success() -> None:
    client = MockLineClient(_ok_transport("/message/broadcast"))
    result = await send_broadcast(
        client,
        message_type="image",
        image_url="https://example.com/img.jpg",
        preview_image_url="https://example.com/preview.jpg",
    )

    assert "broadcast" in result.lower()
    assert "image" in result


@pytest.mark.asyncio
async def test_send_broadcast_flex_success() -> None:
    client = MockLineClient(_ok_transport("/message/broadcast"))
    flex = {"type": "bubble", "body": {"type": "box", "layout": "vertical", "contents": []}}
    result = await send_broadcast(
        client,
        message_type="flex",
        flex_contents=flex,
        alt_text="Test flex",
    )

    assert "broadcast" in result.lower()
    assert "flex" in result


@pytest.mark.asyncio
async def test_send_broadcast_no_message() -> None:
    client = MockLineClient(_ok_transport("/message/broadcast"))

    with pytest.raises(ValueError, match="message"):
        await send_broadcast(client, message_type="text")


@pytest.mark.asyncio
async def test_send_broadcast_api_error() -> None:
    transport = make_mock_transport({
        "/message/broadcast": httpx.Response(403, json={"message": "Forbidden"}),
    })
    client = MockLineClient(transport)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await send_broadcast(client, message="test")
    assert exc_info.value.response.status_code == 403


# === send_push_message ===


@pytest.mark.asyncio
async def test_send_push_message_text_success() -> None:
    client = MockLineClient(_ok_transport("/message/push"))
    result = await send_push_message(client, user_id="U1234", message="Hello!")

    assert "U1234" in result
    assert "สำเร็จ" in result


@pytest.mark.asyncio
async def test_send_push_message_image_success() -> None:
    client = MockLineClient(_ok_transport("/message/push"))
    result = await send_push_message(
        client,
        user_id="U1234",
        message_type="image",
        image_url="https://example.com/img.jpg",
    )

    assert "U1234" in result
    assert "image" in result


@pytest.mark.asyncio
async def test_send_push_message_no_user_id() -> None:
    client = MockLineClient(_ok_transport("/message/push"))

    with pytest.raises(ValueError, match="user_id"):
        await send_push_message(client, user_id="", message="test")


@pytest.mark.asyncio
async def test_send_push_message_api_error() -> None:
    transport = make_mock_transport({
        "/message/push": httpx.Response(400, json={"message": "Bad request"}),
    })
    client = MockLineClient(transport)

    with pytest.raises(httpx.HTTPStatusError):
        await send_push_message(client, user_id="U1234", message="test")


# === send_multicast ===


@pytest.mark.asyncio
async def test_send_multicast_text_success() -> None:
    client = MockLineClient(_ok_transport("/message/multicast"))
    result = await send_multicast(
        client,
        user_ids=["U1111", "U2222", "U3333"],
        message="โปรโมชั่นพิเศษ!",
    )

    assert "3 คนสำเร็จ" in result


@pytest.mark.asyncio
async def test_send_multicast_flex_success() -> None:
    client = MockLineClient(_ok_transport("/message/multicast"))
    flex = {"type": "bubble", "body": {"type": "box", "layout": "vertical", "contents": []}}
    result = await send_multicast(
        client,
        user_ids=["U1111"],
        message_type="flex",
        flex_contents=flex,
    )

    assert "1 คนสำเร็จ" in result
    assert "flex" in result


@pytest.mark.asyncio
async def test_send_multicast_empty_user_ids() -> None:
    client = MockLineClient(_ok_transport("/message/multicast"))

    with pytest.raises(ValueError, match="user_id"):
        await send_multicast(client, user_ids=[], message="test")


@pytest.mark.asyncio
async def test_send_multicast_too_many_users() -> None:
    client = MockLineClient(_ok_transport("/message/multicast"))
    user_ids = [f"U{i:04d}" for i in range(501)]

    with pytest.raises(ValueError, match="500"):
        await send_multicast(client, user_ids=user_ids, message="test")


@pytest.mark.asyncio
async def test_send_multicast_api_error() -> None:
    transport = make_mock_transport({
        "/message/multicast": httpx.Response(429, json={"message": "Rate limit"}),
    })
    client = MockLineClient(transport)

    with pytest.raises(httpx.HTTPStatusError):
        await send_multicast(client, user_ids=["U1111"], message="test")


# === send_narrowcast ===


@pytest.mark.asyncio
async def test_send_narrowcast_text_success() -> None:
    client = MockLineClient(_ok_transport("/message/narrowcast"))
    result = await send_narrowcast(
        client,
        message="ข้อเสนอพิเศษ",
        recipient={"type": "audience", "audienceGroupId": 12345},
    )

    assert "narrowcast" in result.lower()
    assert "สำเร็จ" in result


@pytest.mark.asyncio
async def test_send_narrowcast_with_filter() -> None:
    client = MockLineClient(_ok_transport("/message/narrowcast"))
    result = await send_narrowcast(
        client,
        message="ข้อเสนอ",
        demographic_filter={
            "demographic": {
                "type": "operator",
                "and": [
                    {"type": "gender", "oneOf": ["female"]},
                    {"type": "age", "gte": "age_25", "lt": "age_40"},
                ],
            }
        },
    )

    assert "narrowcast" in result.lower()
    assert "สำเร็จ" in result


@pytest.mark.asyncio
async def test_send_narrowcast_image_success() -> None:
    client = MockLineClient(_ok_transport("/message/narrowcast"))
    result = await send_narrowcast(
        client,
        message_type="image",
        image_url="https://example.com/promo.jpg",
    )

    assert "narrowcast" in result.lower()
    assert "image" in result


@pytest.mark.asyncio
async def test_send_narrowcast_no_message() -> None:
    client = MockLineClient(_ok_transport("/message/narrowcast"))

    with pytest.raises(ValueError, match="message"):
        await send_narrowcast(client, message_type="text")


@pytest.mark.asyncio
async def test_send_narrowcast_api_error() -> None:
    transport = make_mock_transport({
        "/message/narrowcast": httpx.Response(500, json={"message": "Internal error"}),
    })
    client = MockLineClient(transport)

    with pytest.raises(httpx.HTTPStatusError):
        await send_narrowcast(client, message="test")


# === Tier restriction tests ===
# All messaging tools are Pro tier — free users should be blocked.


@pytest.mark.asyncio
async def test_send_broadcast_blocked_for_free_tier(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")
    with pytest.raises(GateError, match="Pro"):
        await authorize_tool_call(db, key, "send_broadcast")


@pytest.mark.asyncio
async def test_send_push_message_blocked_for_free_tier(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")
    with pytest.raises(GateError, match="Pro"):
        await authorize_tool_call(db, key, "send_push_message")


@pytest.mark.asyncio
async def test_send_multicast_blocked_for_free_tier(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")
    with pytest.raises(GateError, match="Pro"):
        await authorize_tool_call(db, key, "send_multicast")


@pytest.mark.asyncio
async def test_send_narrowcast_blocked_for_free_tier(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")
    with pytest.raises(GateError, match="Pro"):
        await authorize_tool_call(db, key, "send_narrowcast")
