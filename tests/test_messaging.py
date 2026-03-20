"""Tests for messaging tools — send_broadcast, send_push_message, send_multicast."""

from __future__ import annotations

import pytest

from src.tools.messaging import send_broadcast, send_multicast, send_push_message
from tests.conftest import MockLineAPIClient

VALID_USER_ID = "U1234567890abcdef1234567890abcdef"


@pytest.mark.asyncio
async def test_send_broadcast_success(mock_client: MockLineAPIClient) -> None:
    """Test successful broadcast."""
    mock_client.post.return_value = {"status": "ok", "code": 200}

    result = await send_broadcast(mock_client, "Hello everyone!")
    assert "Broadcast sent successfully" in result
    mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_send_broadcast_empty_message(mock_client: MockLineAPIClient) -> None:
    """Test broadcast rejects empty message."""
    result = await send_broadcast(mock_client, "")
    assert "Validation error" in result
    mock_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_send_broadcast_long_message(mock_client: MockLineAPIClient) -> None:
    """Test broadcast rejects message over 5000 chars."""
    result = await send_broadcast(mock_client, "x" * 5001)
    assert "Validation error" in result
    assert "5000" in result
    mock_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_send_push_message_success(mock_client: MockLineAPIClient) -> None:
    """Test successful push message."""
    mock_client.post.return_value = {"status": "ok", "code": 200}

    result = await send_push_message(mock_client, VALID_USER_ID, "Hi there!")
    assert "Push message sent" in result
    assert VALID_USER_ID in result


@pytest.mark.asyncio
async def test_send_push_message_invalid_user_id(
    mock_client: MockLineAPIClient,
) -> None:
    """Test push message rejects invalid user ID."""
    result = await send_push_message(mock_client, "invalid_id", "Hello")
    assert "Validation error" in result
    mock_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_send_multicast_success(mock_client: MockLineAPIClient) -> None:
    """Test successful multicast."""
    mock_client.post.return_value = {"status": "ok", "code": 200}
    user_ids = [VALID_USER_ID]

    result = await send_multicast(mock_client, user_ids, "Group message!")
    assert "Multicast sent to 1 users" in result


@pytest.mark.asyncio
async def test_send_multicast_too_many_users(mock_client: MockLineAPIClient) -> None:
    """Test multicast rejects more than 500 user IDs."""
    user_ids = [VALID_USER_ID] * 501
    result = await send_multicast(mock_client, user_ids, "Too many!")
    assert "Maximum 500" in result
    mock_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_send_multicast_empty_list(mock_client: MockLineAPIClient) -> None:
    """Test multicast rejects empty user list."""
    result = await send_multicast(mock_client, [], "No one!")
    assert "Error" in result
    mock_client.post.assert_not_called()
