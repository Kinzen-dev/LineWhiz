"""Pro tier messaging tools: broadcast, push, multicast, narrowcast.

Supports message types: text, image, flex.
"""

from typing import Any

from src.services.line_api import LineClient


def _build_messages(
    message: str | None = None,
    message_type: str = "text",
    image_url: str | None = None,
    preview_image_url: str | None = None,
    flex_contents: dict[str, Any] | None = None,
    alt_text: str | None = None,
) -> list[dict[str, Any]]:
    """Build LINE message objects from parameters.

    Supported types:
    - text: simple text message
    - image: image with original + preview URLs
    - flex: Flex Message with custom JSON contents
    """
    if message_type == "image":
        if not image_url:
            raise ValueError(
                "ต้องระบุ image_url สำหรับ image message\n"
                "image_url is required for image message type."
            )
        return [
            {
                "type": "image",
                "originalContentUrl": image_url,
                "previewImageUrl": preview_image_url or image_url,
            }
        ]

    if message_type == "flex":
        if not flex_contents:
            raise ValueError(
                "ต้องระบุ flex_contents สำหรับ flex message\n"
                "flex_contents is required for flex message type."
            )
        return [
            {
                "type": "flex",
                "altText": alt_text or "Flex Message",
                "contents": flex_contents,
            }
        ]

    # Default: text
    if not message:
        raise ValueError(
            "ต้องระบุ message สำหรับ text message\n"
            "message is required for text message type."
        )
    return [{"type": "text", "text": message}]


async def send_broadcast(
    line: LineClient,
    message: str | None = None,
    message_type: str = "text",
    image_url: str | None = None,
    preview_image_url: str | None = None,
    flex_contents: dict[str, Any] | None = None,
    alt_text: str | None = None,
) -> str:
    """Send a message to ALL friends of this LINE OA.

    ส่งข้อความถึงเพื่อนทั้งหมดของ LINE OA นี้
    ⚠️ ระวัง: ข้อความจะถูกส่งไปยังเพื่อนทุกคน ใช้โควตาข้อความ

    Supports text, image, and flex message types.
    """
    messages = _build_messages(
        message=message,
        message_type=message_type,
        image_url=image_url,
        preview_image_url=preview_image_url,
        flex_contents=flex_contents,
        alt_text=alt_text,
    )
    data: dict[str, Any] = {"messages": messages}
    await line.post("/message/broadcast", data)

    preview = _message_preview(message_type, message)
    return (
        f"ส่ง broadcast สำเร็จไปยังเพื่อนทั้งหมด ({message_type})\n"
        f"Broadcast sent to all friends. {preview}"
    )


async def send_push_message(
    line: LineClient,
    user_id: str,
    message: str | None = None,
    message_type: str = "text",
    image_url: str | None = None,
    preview_image_url: str | None = None,
    flex_contents: dict[str, Any] | None = None,
    alt_text: str | None = None,
) -> str:
    """Send a direct message to a specific user by their LINE user ID.

    ส่งข้อความตรงไปยังผู้ใช้ที่ระบุ
    """
    if not user_id:
        raise ValueError(
            "ต้องระบุ user_id\nuser_id is required."
        )

    messages = _build_messages(
        message=message,
        message_type=message_type,
        image_url=image_url,
        preview_image_url=preview_image_url,
        flex_contents=flex_contents,
        alt_text=alt_text,
    )
    data: dict[str, Any] = {"to": user_id, "messages": messages}
    await line.post("/message/push", data)

    preview = _message_preview(message_type, message)
    return (
        f"ส่งข้อความถึงผู้ใช้ {user_id} สำเร็จ ({message_type})\n"
        f"Push message sent to {user_id}. {preview}"
    )


async def send_multicast(
    line: LineClient,
    user_ids: list[str],
    message: str | None = None,
    message_type: str = "text",
    image_url: str | None = None,
    preview_image_url: str | None = None,
    flex_contents: dict[str, Any] | None = None,
    alt_text: str | None = None,
) -> str:
    """Send a message to multiple users at once (max 500 user IDs).

    ส่งข้อความถึงผู้ใช้หลายคนพร้อมกัน (สูงสุด 500 คน)
    """
    if not user_ids:
        raise ValueError(
            "ต้องระบุ user_ids อย่างน้อย 1 คน\n"
            "At least one user_id is required."
        )
    if len(user_ids) > 500:
        raise ValueError(
            "ส่งได้สูงสุด 500 คนต่อครั้ง\n"
            "Maximum 500 user IDs allowed per multicast."
        )

    messages = _build_messages(
        message=message,
        message_type=message_type,
        image_url=image_url,
        preview_image_url=preview_image_url,
        flex_contents=flex_contents,
        alt_text=alt_text,
    )
    data: dict[str, Any] = {"to": user_ids, "messages": messages}
    await line.post("/message/multicast", data)

    count = len(user_ids)
    preview = _message_preview(message_type, message)
    return (
        f"ส่งข้อความถึงผู้ใช้ {count} คนสำเร็จ ({message_type})\n"
        f"Multicast sent to {count} users. {preview}"
    )


async def send_narrowcast(
    line: LineClient,
    message: str | None = None,
    message_type: str = "text",
    image_url: str | None = None,
    preview_image_url: str | None = None,
    flex_contents: dict[str, Any] | None = None,
    alt_text: str | None = None,
    recipient: dict[str, Any] | None = None,
    demographic_filter: dict[str, Any] | None = None,
) -> str:
    """Send a message to a subset of friends based on targeting criteria.

    ส่งข้อความถึงกลุ่มเพื่อนที่เลือกตามเงื่อนไข (narrowcast)
    Uses LINE's audience targeting. Provide recipient and/or demographic_filter.
    """
    messages = _build_messages(
        message=message,
        message_type=message_type,
        image_url=image_url,
        preview_image_url=preview_image_url,
        flex_contents=flex_contents,
        alt_text=alt_text,
    )
    data: dict[str, Any] = {"messages": messages}
    if recipient:
        data["recipient"] = recipient
    if demographic_filter:
        data["filter"] = demographic_filter

    await line.post("/message/narrowcast", data)

    preview = _message_preview(message_type, message)
    return (
        f"ส่ง narrowcast สำเร็จ ({message_type})\n"
        f"Narrowcast sent successfully. {preview}"
    )


def _message_preview(message_type: str, message: str | None) -> str:
    """Create a short preview of the message for confirmation."""
    if message_type == "text" and message:
        truncated = f"{message[:50]}..." if len(message) > 50 else message
        return f"ข้อความ: '{truncated}'"
    return f"ประเภท: {message_type}"
