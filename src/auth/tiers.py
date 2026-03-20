"""Tier system — Free / Pro / Business gating and rate limits.

Defines which tools each tier can access and daily call limits.
"""

from __future__ import annotations

import logging
from typing import Any

from src.config import get_settings
from src.db.database import get_daily_usage_count

logger = logging.getLogger("linewhiz.auth.tiers")

TIERS: dict[str, dict[str, Any]] = {
    "free": {
        "allowed_tools": [
            "get_account_info",
            "get_friend_count",
            "get_message_quota",
        ],
        "daily_call_limit": 100,
    },
    "pro": {
        "allowed_tools": [
            "get_account_info",
            "get_friend_count",
            "get_message_quota",
            "send_broadcast",
            "send_push_message",
            "send_multicast",
            "send_narrowcast",
            "get_message_stats",
            "get_user_profile",
            "list_rich_menus",
            "create_rich_menu",
            "set_default_rich_menu",
            "link_rich_menu_to_user",
        ],
        "daily_call_limit": 5000,
    },
    "business": {
        "allowed_tools": "__all__",
        "daily_call_limit": -1,  # unlimited
    },
}


def get_current_tier() -> str:
    """Get the current tier from env config."""
    return get_settings().linewhiz_tier


def check_tier_access(tool_name: str, tier: str | None = None) -> bool:
    """Check if a tool is allowed for the given tier.

    Returns True if access is granted, False if denied.
    """
    tier = tier or get_current_tier()
    tier_config = TIERS.get(tier)
    if tier_config is None:
        logger.error("Unknown tier: %s", tier)
        return False

    allowed = tier_config["allowed_tools"]
    if allowed == "__all__":
        return True
    return tool_name in allowed


async def check_rate_limit(api_key_id: int, tier: str | None = None) -> bool:
    """Check if the API key is under the daily call cap.

    Returns True if under limit, False if exceeded.
    """
    tier = tier or get_current_tier()
    tier_config = TIERS.get(tier)
    if tier_config is None:
        return False

    daily_limit = tier_config["daily_call_limit"]
    if daily_limit == -1:
        return True  # unlimited

    current_count = await get_daily_usage_count(api_key_id)
    if current_count >= daily_limit:
        logger.warning(
            "Rate limit exceeded for api_key_id=%d: %d/%d",
            api_key_id,
            current_count,
            daily_limit,
        )
        return False
    return True
