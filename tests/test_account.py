"""Tests for account tools — get_account_info, get_friend_count, get_message_quota."""

from __future__ import annotations

import json

import pytest

from src.tools.account import get_account_info, get_friend_count, get_message_quota
from tests.conftest import MockLineAPIClient


@pytest.mark.asyncio
async def test_get_account_info(
    mock_client: MockLineAPIClient, sample_account_info: dict
) -> None:
    """Test get_account_info returns formatted account data."""
    mock_client.get.return_value = sample_account_info

    result = await get_account_info(mock_client)
    data = json.loads(result)

    assert data["bot_name"] == "Test Bot"
    assert data["basic_id"] == "@testbot"
    assert data["chat_mode"] == "chat"
    mock_client.get.assert_called_once_with("/info")


@pytest.mark.asyncio
async def test_get_friend_count_with_date(mock_client: MockLineAPIClient) -> None:
    """Test get_friend_count with explicit date."""
    mock_client.get.return_value = {
        "status": "ready",
        "followers": 1500,
        "targetedReaches": 1200,
        "blocks": 50,
    }

    result = await get_friend_count(mock_client, "20260315")
    data = json.loads(result)

    assert data["date"] == "20260315"
    assert data["followers"] == 1500
    assert data["blocks"] == 50
    mock_client.get.assert_called_once_with("/insight/followers?date=20260315")


@pytest.mark.asyncio
async def test_get_friend_count_default_date(mock_client: MockLineAPIClient) -> None:
    """Test get_friend_count defaults to yesterday when no date given."""
    mock_client.get.return_value = {"status": "ready", "followers": 100}

    result = await get_friend_count(mock_client)
    data = json.loads(result)

    # Should have a date (yesterday)
    assert "date" in data
    assert len(data["date"]) == 8


@pytest.mark.asyncio
async def test_get_message_quota(mock_client: MockLineAPIClient) -> None:
    """Test get_message_quota combines quota and consumption data."""
    mock_client.get.side_effect = [
        {"type": "limited", "value": 1000},  # quota
        {"totalUsage": 350},  # consumption
    ]

    result = await get_message_quota(mock_client)
    data = json.loads(result)

    assert data["total_quota"] == 1000
    assert data["used_this_month"] == 350
    assert data["remaining"] == 650
