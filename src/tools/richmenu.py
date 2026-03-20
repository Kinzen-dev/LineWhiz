"""Pro/Business tier tools: rich menu management."""

import json
from typing import Any

from src.services.line_api import LineClient


async def list_rich_menus(line: LineClient) -> str:
    """List all rich menus created for this LINE OA.

    แสดงรายการ Rich Menu ทั้งหมดของ LINE OA นี้
    """
    data = await line.get("/richmenu/list")
    menus = data.get("richmenus", [])

    if not menus:
        return "ไม่พบ Rich Menu สำหรับ LINE OA นี้\nNo rich menus found for this LINE OA."

    result = []
    for m in menus:
        result.append({
            "rich_menu_id": m.get("richMenuId"),
            "name": m.get("name"),
            "chat_bar_text": m.get("chatBarText"),
            "size": m.get("size"),
            "selected": m.get("selected", False),
            "areas_count": len(m.get("areas", [])),
        })
    return json.dumps(result, ensure_ascii=False, indent=2)


async def create_rich_menu(
    line: LineClient,
    name: str,
    chat_bar_text: str,
    areas: list[dict[str, Any]],
    size_width: int = 2500,
    size_height: int = 1686,
    selected: bool = False,
) -> str:
    """Create a new rich menu for this LINE OA.

    สร้าง Rich Menu ใหม่สำหรับ LINE OA นี้
    Size defaults to 2500x1686 (full). Use 2500x843 for half.
    """
    if not name:
        raise ValueError(
            "ต้องระบุชื่อ Rich Menu\nRich menu name is required."
        )
    if not chat_bar_text:
        raise ValueError(
            "ต้องระบุข้อความ chat bar\nchat_bar_text is required."
        )
    if not areas:
        raise ValueError(
            "ต้องระบุ areas อย่างน้อย 1 รายการ\nAt least one area is required."
        )

    data: dict[str, Any] = {
        "size": {"width": size_width, "height": size_height},
        "selected": selected,
        "name": name,
        "chatBarText": chat_bar_text,
        "areas": areas,
    }

    result = await line.post("/richmenu", data)
    rich_menu_id = result.get("richMenuId", "unknown")

    return (
        f"สร้าง Rich Menu สำเร็จ\n"
        f"Rich menu created successfully.\n"
        f"Rich Menu ID: {rich_menu_id}"
    )


async def set_default_rich_menu(line: LineClient, rich_menu_id: str) -> str:
    """Set a rich menu as the default for all users.

    ตั้ง Rich Menu เป็นค่าเริ่มต้นสำหรับผู้ใช้ทุกคน
    """
    if not rich_menu_id:
        raise ValueError(
            "ต้องระบุ rich_menu_id\nrich_menu_id is required."
        )

    await line.post(f"/user/all/richmenu/{rich_menu_id}", {})

    return (
        f"ตั้ง Rich Menu เป็นค่าเริ่มต้นสำเร็จ\n"
        f"Default rich menu set successfully.\n"
        f"Rich Menu ID: {rich_menu_id}"
    )


async def link_rich_menu_to_user(
    line: LineClient,
    user_id: str,
    rich_menu_id: str,
) -> str:
    """Link a specific rich menu to a specific user.

    เชื่อมโยง Rich Menu กับผู้ใช้ที่ระบุ
    """
    if not user_id:
        raise ValueError(
            "ต้องระบุ user_id\nuser_id is required."
        )
    if not rich_menu_id:
        raise ValueError(
            "ต้องระบุ rich_menu_id\nrich_menu_id is required."
        )

    await line.post(f"/user/{user_id}/richmenu/{rich_menu_id}", {})

    return (
        f"เชื่อมโยง Rich Menu กับผู้ใช้สำเร็จ\n"
        f"Rich menu linked to user successfully.\n"
        f"User: {user_id}, Rich Menu: {rich_menu_id}"
    )
