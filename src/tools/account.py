"""Account tools — get_account_info, get_friend_count, get_message_quota."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from src.services.line_api import LineAPIClient


async def get_account_info(client: LineAPIClient) -> str:
    """Get LINE Official Account info: name, friend count, plan, picture URL."""
    data = await client.get("/info")
    return json.dumps(
        {
            "bot_name": data.get("displayName", "N/A"),
            "user_id": data.get("userId", "N/A"),
            "basic_id": data.get("basicId", "N/A"),
            "premium_id": data.get("premiumId", "N/A"),
            "picture_url": data.get("pictureUrl", "N/A"),
            "chat_mode": data.get("chatMode", "N/A"),
            "mark_as_read_mode": data.get("markAsReadMode", "N/A"),
        },
        ensure_ascii=False,
        indent=2,
    )


async def get_friend_count(client: LineAPIClient, date: str | None = None) -> str:
    """Get the number of LINE OA friends/followers on a specific date.

    Args:
        client: LINE API client instance.
        date: Date in YYYYMMDD format. Defaults to yesterday.
    """
    if not date:
        yesterday = datetime.now() - timedelta(days=1)
        date = yesterday.strftime("%Y%m%d")
    data = await client.get(f"/insight/followers?date={date}")
    return json.dumps(
        {
            "date": date,
            "followers": data.get("followers", 0),
            "targeted_reaches": data.get("targetedReaches", 0),
            "blocks": data.get("blocks", 0),
            "status": data.get("status", "unknown"),
        },
        ensure_ascii=False,
        indent=2,
    )


async def get_message_quota(client: LineAPIClient) -> str:
    """Get remaining message quota for this month.

    Shows total allowed, used, and remaining messages.
    """
    quota = await client.get("/message/quota")
    consumption = await client.get("/message/quota/consumption")
    total = quota.get("value", 0)
    used = consumption.get("totalUsage", 0)
    remaining = total - used if total > 0 else "unlimited"
    return json.dumps(
        {
            "quota_type": quota.get("type", "N/A"),
            "total_quota": total,
            "used_this_month": used,
            "remaining": remaining,
        },
        ensure_ascii=False,
        indent=2,
    )
