"""Shared test fixtures for LineWhiz tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.services.line_api import LineAPIClient


class MockLineAPIClient(LineAPIClient):
    """Mock LINE API client for testing — no real HTTP calls."""

    def __init__(self) -> None:
        # Skip parent __init__ which reads env vars
        self._token = "test_token"
        self._headers = {
            "Authorization": "Bearer test_token",
            "Content-Type": "application/json",
        }
        self.get = AsyncMock()  # type: ignore[assignment]
        self.post = AsyncMock()  # type: ignore[assignment]


@pytest.fixture
def mock_client() -> MockLineAPIClient:
    """Provide a mock LINE API client."""
    return MockLineAPIClient()


@pytest.fixture
def sample_account_info() -> dict[str, Any]:
    """Sample LINE account info response."""
    return {
        "displayName": "Test Bot",
        "userId": "U1234567890abcdef1234567890abcdef",
        "basicId": "@testbot",
        "premiumId": "@testbot",
        "pictureUrl": "https://example.com/pic.jpg",
        "chatMode": "chat",
        "markAsReadMode": "manual",
    }


@pytest.fixture
def sample_user_profile() -> dict[str, Any]:
    """Sample LINE user profile response."""
    return {
        "userId": "U1234567890abcdef1234567890abcdef",
        "displayName": "Test User",
        "pictureUrl": "https://example.com/user.jpg",
        "statusMessage": "Hello!",
        "language": "en",
    }
