"""Messaging tools — send_broadcast, send_push_message, send_multicast.

Includes input validation per CLAUDE.md spec:
- user_id must match r"^U[a-f0-9]{32}$"
- message max 5000 chars
- user_ids max 500 items
"""

from __future__ import annotations

import re

from src.services.line_api import LineAPIClient

# Validation patterns
USER_ID_PATTERN = re.compile(r"^U[a-f0-9]{32}$")
MAX_MESSAGE_LENGTH = 5000
MAX_MULTICAST_USERS = 500


def _validate_user_id(user_id: str) -> str | None:
    """Validate LINE user ID format. Returns error message or None."""
    if not USER_ID_PATTERN.match(user_id):
        return f"Invalid user ID format: '{user_id}'. Must match U + 32 hex characters."
    return None


def _validate_message(message: str) -> str | None:
    """Validate message content. Returns error message or None."""
    if not message:
        return "Message cannot be empty."
    if len(message) > MAX_MESSAGE_LENGTH:
        return f"Message too long: {len(message)} chars (max {MAX_MESSAGE_LENGTH})."
    return None


async def send_broadcast(client: LineAPIClient, message: str) -> str:
    """Send a text message to ALL friends of this LINE OA.

    Use carefully — this reaches everyone and costs message quota.

    Args:
        client: LINE API client instance.
        message: Text message to broadcast (max 5000 chars).
    """
    error = _validate_message(message)
    if error:
        return f"Validation error: {error}"

    data = {"messages": [{"type": "text", "text": message}]}
    await client.post("/message/broadcast", data)
    return f"Broadcast sent successfully. Message: '{message[:50]}...'"


async def send_push_message(client: LineAPIClient, user_id: str, message: str) -> str:
    """Send a direct text message to a specific user by their LINE user ID.

    Args:
        client: LINE API client instance.
        user_id: LINE user ID (starts with U).
        message: Text message to send.
    """
    error = _validate_user_id(user_id)
    if error:
        return f"Validation error: {error}"
    error = _validate_message(message)
    if error:
        return f"Validation error: {error}"

    data = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}],
    }
    await client.post("/message/push", data)
    return f"Push message sent to {user_id}. Message: '{message[:50]}...'"


async def send_multicast(client: LineAPIClient, user_ids: list[str], message: str) -> str:
    """Send a text message to multiple users at once (max 500 user IDs).

    Args:
        client: LINE API client instance.
        user_ids: List of LINE user IDs (max 500).
        message: Text message to send.
    """
    if len(user_ids) > MAX_MULTICAST_USERS:
        return f"Error: Maximum {MAX_MULTICAST_USERS} user IDs allowed per multicast."
    if not user_ids:
        return "Error: user_ids list cannot be empty."

    for uid in user_ids:
        error = _validate_user_id(uid)
        if error:
            return f"Validation error: {error}"

    error = _validate_message(message)
    if error:
        return f"Validation error: {error}"

    data = {
        "to": user_ids,
        "messages": [{"type": "text", "text": message}],
    }
    await client.post("/message/multicast", data)
    return f"Multicast sent to {len(user_ids)} users. Message: '{message[:50]}...'"
