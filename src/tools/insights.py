"""Insights tools — get_message_delivery_stats, get_user_profile."""

from __future__ import annotations

import json
import re

from src.services.line_api import LineAPIClient

DATE_PATTERN = re.compile(r"^\d{8}$")
USER_ID_PATTERN = re.compile(r"^U[a-f0-9]{32}$")


async def get_message_delivery_stats(client: LineAPIClient, date: str) -> str:
    """Get delivery statistics for messages sent on a specific date.

    Args:
        client: LINE API client instance.
        date: Date in YYYYMMDD format.
    """
    if not DATE_PATTERN.match(date):
        return "Validation error: date must be in YYYYMMDD format."

    data = await client.get(f"/insight/message/delivery?date={date}")
    return json.dumps(
        {
            "date": date,
            "status": data.get("status", "unknown"),
            "broadcast_sent": data.get("broadcast", 0),
            "targeting_sent": data.get("targeting", 0),
            "auto_response_sent": data.get("autoResponse", 0),
            "welcome_response_sent": data.get("welcomeResponse", 0),
            "chat_sent": data.get("chat", 0),
            "api_broadcast_sent": data.get("apiBroadcast", 0),
            "api_push_sent": data.get("apiPush", 0),
            "api_multicast_sent": data.get("apiMulticast", 0),
            "api_reply_sent": data.get("apiReply", 0),
        },
        ensure_ascii=False,
        indent=2,
    )


async def get_user_profile(client: LineAPIClient, user_id: str) -> str:
    """Get profile info of a LINE user: display name, picture, status message.

    Args:
        client: LINE API client instance.
        user_id: LINE user ID.
    """
    if not USER_ID_PATTERN.match(user_id):
        return f"Validation error: Invalid user ID format: '{user_id}'."

    data = await client.get(f"/profile/{user_id}")
    return json.dumps(
        {
            "user_id": data.get("userId", "N/A"),
            "display_name": data.get("displayName", "N/A"),
            "picture_url": data.get("pictureUrl", "N/A"),
            "status_message": data.get("statusMessage", "N/A"),
            "language": data.get("language", "N/A"),
        },
        ensure_ascii=False,
        indent=2,
    )
