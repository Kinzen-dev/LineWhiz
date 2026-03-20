"""Tests for auth — tier access checking and rate limit logic."""

from __future__ import annotations

import pytest

from src.auth.api_keys import hash_api_key, validate_api_key
from src.auth.tiers import TIERS, check_tier_access

# ─── API Key Tests ────────────────────────────────────────────────────────────


def test_hash_api_key_deterministic() -> None:
    """Test that hashing the same key always produces the same hash."""
    key = "test-api-key-12345"
    assert hash_api_key(key) == hash_api_key(key)


def test_hash_api_key_different_keys() -> None:
    """Test that different keys produce different hashes."""
    assert hash_api_key("key-a") != hash_api_key("key-b")


@pytest.mark.asyncio
async def test_validate_api_key_empty() -> None:
    """Test that empty API key is rejected."""
    assert await validate_api_key("") is False


@pytest.mark.asyncio
async def test_validate_api_key_valid() -> None:
    """Test that non-empty API key is accepted (MVP mode)."""
    assert await validate_api_key("any-non-empty-key") is True


# ─── Tier Access Tests ────────────────────────────────────────────────────────


def test_free_tier_allows_account_tools() -> None:
    """Test that free tier allows account info tools."""
    assert check_tier_access("get_account_info", "free") is True
    assert check_tier_access("get_friend_count", "free") is True
    assert check_tier_access("get_message_quota", "free") is True


def test_free_tier_denies_pro_tools() -> None:
    """Test that free tier denies messaging tools."""
    assert check_tier_access("send_broadcast", "free") is False
    assert check_tier_access("send_push_message", "free") is False
    assert check_tier_access("list_rich_menus", "free") is False


def test_pro_tier_allows_messaging() -> None:
    """Test that pro tier allows messaging tools."""
    assert check_tier_access("send_broadcast", "pro") is True
    assert check_tier_access("send_push_message", "pro") is True
    assert check_tier_access("send_multicast", "pro") is True
    assert check_tier_access("list_rich_menus", "pro") is True


def test_business_tier_allows_all() -> None:
    """Test that business tier allows any tool name."""
    assert check_tier_access("get_account_info", "business") is True
    assert check_tier_access("send_broadcast", "business") is True
    assert check_tier_access("any_future_tool", "business") is True


def test_unknown_tier_denies_all() -> None:
    """Test that unknown tier denies access."""
    assert check_tier_access("get_account_info", "invalid_tier") is False


def test_tiers_config_structure() -> None:
    """Test that the TIERS config has the expected structure."""
    assert "free" in TIERS
    assert "pro" in TIERS
    assert "business" in TIERS

    # Free tier
    assert isinstance(TIERS["free"]["allowed_tools"], list)
    assert TIERS["free"]["daily_call_limit"] == 100

    # Pro tier
    assert isinstance(TIERS["pro"]["allowed_tools"], list)
    assert TIERS["pro"]["daily_call_limit"] == 5000

    # Business tier
    assert TIERS["business"]["allowed_tools"] == "__all__"
    assert TIERS["business"]["daily_call_limit"] == -1
