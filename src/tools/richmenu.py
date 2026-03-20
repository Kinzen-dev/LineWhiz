"""Rich menu tools — list_rich_menus (MVP), create/set/link (v1.1+)."""

from __future__ import annotations

import json
from typing import Any

from src.services.line_api import LineAPIClient


async def list_rich_menus(client: LineAPIClient) -> str:
    """List all rich menus created for this LINE OA."""
    data = await client.get("/richmenu/list")
    menus: list[dict[str, Any]] = data.get("richmenus", [])
    if not menus:
        return "No rich menus found for this LINE OA."

    result = []
    for m in menus:
        result.append(
            {
                "rich_menu_id": m.get("richMenuId"),
                "name": m.get("name"),
                "chat_bar_text": m.get("chatBarText"),
                "size": m.get("size"),
                "selected": m.get("selected", False),
                "areas_count": len(m.get("areas", [])),
            }
        )
    return json.dumps(result, ensure_ascii=False, indent=2)
