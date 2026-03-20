"""Tests for rich menu tools: list, create, set default, link to user."""

import json

import httpx
import pytest

from src.auth.api_keys import generate_api_key
from src.auth.gate import GateError, authorize_tool_call
from src.db.database import init_db
from src.tools.richmenu import (
    create_rich_menu,
    link_rich_menu_to_user,
    list_rich_menus,
    set_default_rich_menu,
)
from tests.conftest import MockLineClient, make_mock_transport


@pytest.fixture
async def db():
    """In-memory database for tier restriction tests."""
    conn = await init_db(":memory:")
    yield conn
    await conn.close()

SAMPLE_AREA = {
    "bounds": {"x": 0, "y": 0, "width": 1250, "height": 1686},
    "action": {"type": "message", "text": "hello"},
}

SAMPLE_MENUS = {
    "richmenus": [
        {
            "richMenuId": "richmenu-abc123",
            "name": "Main Menu",
            "chatBarText": "เมนู",
            "size": {"width": 2500, "height": 1686},
            "selected": True,
            "areas": [SAMPLE_AREA],
        },
        {
            "richMenuId": "richmenu-def456",
            "name": "Promo Menu",
            "chatBarText": "โปรโมชั่น",
            "size": {"width": 2500, "height": 843},
            "selected": False,
            "areas": [SAMPLE_AREA, SAMPLE_AREA],
        },
    ]
}


def _ok_transport(path_key: str) -> httpx.MockTransport:
    return make_mock_transport({
        path_key: httpx.Response(200, json={"status": "ok"}),
    })


# === list_rich_menus ===


@pytest.mark.asyncio
async def test_list_rich_menus_success() -> None:
    transport = make_mock_transport({
        "/richmenu/list": httpx.Response(200, json=SAMPLE_MENUS),
    })
    client = MockLineClient(transport)
    result = json.loads(await list_rich_menus(client))

    assert len(result) == 2
    assert result[0]["rich_menu_id"] == "richmenu-abc123"
    assert result[0]["name"] == "Main Menu"
    assert result[0]["selected"] is True
    assert result[0]["areas_count"] == 1
    assert result[1]["areas_count"] == 2


@pytest.mark.asyncio
async def test_list_rich_menus_empty() -> None:
    transport = make_mock_transport({
        "/richmenu/list": httpx.Response(200, json={"richmenus": []}),
    })
    client = MockLineClient(transport)
    result = await list_rich_menus(client)

    assert "ไม่พบ" in result
    assert "No rich menus" in result


@pytest.mark.asyncio
async def test_list_rich_menus_api_error() -> None:
    transport = make_mock_transport({
        "/richmenu/list": httpx.Response(401, json={"message": "Unauthorized"}),
    })
    client = MockLineClient(transport)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await list_rich_menus(client)
    assert exc_info.value.response.status_code == 401


# === create_rich_menu ===


@pytest.mark.asyncio
async def test_create_rich_menu_success() -> None:
    transport = make_mock_transport({
        "/richmenu": httpx.Response(200, json={"richMenuId": "richmenu-new123"}),
    })
    client = MockLineClient(transport)
    result = await create_rich_menu(
        client,
        name="New Menu",
        chat_bar_text="เมนูใหม่",
        areas=[SAMPLE_AREA],
    )

    assert "สำเร็จ" in result
    assert "richmenu-new123" in result


@pytest.mark.asyncio
async def test_create_rich_menu_half_size() -> None:
    transport = make_mock_transport({
        "/richmenu": httpx.Response(200, json={"richMenuId": "richmenu-half"}),
    })
    client = MockLineClient(transport)
    result = await create_rich_menu(
        client,
        name="Half Menu",
        chat_bar_text="เมนู",
        areas=[SAMPLE_AREA],
        size_width=2500,
        size_height=843,
    )

    assert "richmenu-half" in result


@pytest.mark.asyncio
async def test_create_rich_menu_no_name() -> None:
    client = MockLineClient(_ok_transport("/richmenu"))

    with pytest.raises(ValueError, match="name"):
        await create_rich_menu(client, name="", chat_bar_text="bar", areas=[SAMPLE_AREA])


@pytest.mark.asyncio
async def test_create_rich_menu_no_chat_bar_text() -> None:
    client = MockLineClient(_ok_transport("/richmenu"))

    with pytest.raises(ValueError, match="chat_bar_text"):
        await create_rich_menu(client, name="Menu", chat_bar_text="", areas=[SAMPLE_AREA])


@pytest.mark.asyncio
async def test_create_rich_menu_no_areas() -> None:
    client = MockLineClient(_ok_transport("/richmenu"))

    with pytest.raises(ValueError, match="area"):
        await create_rich_menu(client, name="Menu", chat_bar_text="bar", areas=[])


@pytest.mark.asyncio
async def test_create_rich_menu_api_error() -> None:
    transport = make_mock_transport({
        "/richmenu": httpx.Response(400, json={"message": "Invalid areas"}),
    })
    client = MockLineClient(transport)

    with pytest.raises(httpx.HTTPStatusError):
        await create_rich_menu(
            client, name="Menu", chat_bar_text="bar", areas=[SAMPLE_AREA]
        )


# === set_default_rich_menu ===


@pytest.mark.asyncio
async def test_set_default_rich_menu_success() -> None:
    transport = make_mock_transport({
        "/user/all/richmenu/": httpx.Response(200, json={"status": "ok"}),
    })
    client = MockLineClient(transport)
    result = await set_default_rich_menu(client, rich_menu_id="richmenu-abc123")

    assert "สำเร็จ" in result
    assert "richmenu-abc123" in result


@pytest.mark.asyncio
async def test_set_default_rich_menu_no_id() -> None:
    client = MockLineClient(_ok_transport("/user/all/richmenu/"))

    with pytest.raises(ValueError, match="rich_menu_id"):
        await set_default_rich_menu(client, rich_menu_id="")


@pytest.mark.asyncio
async def test_set_default_rich_menu_api_error() -> None:
    transport = make_mock_transport({
        "/user/all/richmenu/": httpx.Response(404, json={"message": "Not found"}),
    })
    client = MockLineClient(transport)

    with pytest.raises(httpx.HTTPStatusError):
        await set_default_rich_menu(client, rich_menu_id="richmenu-invalid")


# === link_rich_menu_to_user ===


@pytest.mark.asyncio
async def test_link_rich_menu_to_user_success() -> None:
    transport = make_mock_transport({
        "/user/U1234/richmenu/": httpx.Response(200, json={"status": "ok"}),
    })
    client = MockLineClient(transport)
    result = await link_rich_menu_to_user(
        client, user_id="U1234", rich_menu_id="richmenu-abc123"
    )

    assert "สำเร็จ" in result
    assert "U1234" in result
    assert "richmenu-abc123" in result


@pytest.mark.asyncio
async def test_link_rich_menu_to_user_no_user_id() -> None:
    client = MockLineClient(_ok_transport("/user/"))

    with pytest.raises(ValueError, match="user_id"):
        await link_rich_menu_to_user(client, user_id="", rich_menu_id="richmenu-abc")


@pytest.mark.asyncio
async def test_link_rich_menu_to_user_no_menu_id() -> None:
    client = MockLineClient(_ok_transport("/user/"))

    with pytest.raises(ValueError, match="rich_menu_id"):
        await link_rich_menu_to_user(client, user_id="U1234", rich_menu_id="")


@pytest.mark.asyncio
async def test_link_rich_menu_to_user_api_error() -> None:
    transport = make_mock_transport({
        "/user/U1234/richmenu/": httpx.Response(404, json={"message": "Not found"}),
    })
    client = MockLineClient(transport)

    with pytest.raises(httpx.HTTPStatusError):
        await link_rich_menu_to_user(
            client, user_id="U1234", rich_menu_id="richmenu-invalid"
        )


# === Tier restriction tests ===
# All rich menu tools are Pro tier — free users should be blocked.


@pytest.mark.asyncio
async def test_list_rich_menus_blocked_for_free_tier(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")
    with pytest.raises(GateError, match="Pro"):
        await authorize_tool_call(db, key, "list_rich_menus")


@pytest.mark.asyncio
async def test_create_rich_menu_blocked_for_free_tier(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")
    with pytest.raises(GateError, match="Pro"):
        await authorize_tool_call(db, key, "create_rich_menu")


@pytest.mark.asyncio
async def test_set_default_rich_menu_blocked_for_free_tier(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")
    with pytest.raises(GateError, match="Pro"):
        await authorize_tool_call(db, key, "set_default_rich_menu")


@pytest.mark.asyncio
async def test_link_rich_menu_to_user_blocked_for_free_tier(db) -> None:
    key = await generate_api_key(db, user_id="user1", tier="free")
    with pytest.raises(GateError, match="Pro"):
        await authorize_tool_call(db, key, "link_rich_menu_to_user")
