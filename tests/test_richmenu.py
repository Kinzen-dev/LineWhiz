"""Tests for rich menu tools — list_rich_menus."""

from __future__ import annotations

import json

import pytest

from src.tools.richmenu import list_rich_menus
from tests.conftest import MockLineAPIClient


@pytest.mark.asyncio
async def test_list_rich_menus_with_menus(mock_client: MockLineAPIClient) -> None:
    """Test listing rich menus returns formatted data."""
    mock_client.get.return_value = {
        "richmenus": [
            {
                "richMenuId": "richmenu-abc123",
                "name": "Main Menu",
                "chatBarText": "Menu",
                "size": {"width": 2500, "height": 1686},
                "selected": True,
                "areas": [{"action": {"type": "uri"}}],
            }
        ]
    }

    result = await list_rich_menus(mock_client)
    data = json.loads(result)

    assert len(data) == 1
    assert data[0]["rich_menu_id"] == "richmenu-abc123"
    assert data[0]["name"] == "Main Menu"
    assert data[0]["selected"] is True
    assert data[0]["areas_count"] == 1


@pytest.mark.asyncio
async def test_list_rich_menus_empty(mock_client: MockLineAPIClient) -> None:
    """Test listing rich menus when none exist."""
    mock_client.get.return_value = {"richmenus": []}

    result = await list_rich_menus(mock_client)
    assert "No rich menus found" in result
