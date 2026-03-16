"""
LINE Official Account MCP Server — Starter Code
Version: 0.1.0 (MVP)

Run: uv run server.py
Test: mcp dev server.py
"""

import os
import json
import httpx
from datetime import datetime, timedelta
from mcp.server import Server
from mcp.types import Tool, TextContent

# === Config ===
LINE_API_BASE = "https://api.line.me/v2/bot"
LINE_DATA_API_BASE = "https://api-data.line.me/v2/bot"

server = Server("line-oa-mcp")

# === LINE API Client ===
class LineClient:
    def __init__(self):
        self.token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def get(self, path: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{LINE_API_BASE}{path}",
                headers=self.headers,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    async def post(self, path: str, data: dict) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{LINE_API_BASE}{path}",
                headers=self.headers,
                json=data,
                timeout=30,
            )
            resp.raise_for_status()
            # Some POST endpoints return empty body
            if resp.status_code == 200 and resp.text:
                return resp.json()
            return {"status": "ok", "code": resp.status_code}

line = LineClient()


# =============================================================
# FREE TIER TOOLS
# =============================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # --- Free ---
        Tool(
            name="get_account_info",
            description="Get LINE Official Account info: name, friend count, plan, picture URL.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_friend_count",
            description="Get the number of LINE OA friends/followers on a specific date. "
                        "Provide date as YYYYMMDD or omit for yesterday.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYYMMDD format. Defaults to yesterday.",
                    }
                },
            },
        ),
        Tool(
            name="get_message_quota",
            description="Get remaining message quota for this month. "
                        "Shows total allowed, used, and remaining messages.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        # --- Pro ---
        Tool(
            name="send_broadcast",
            description="Send a text message to ALL friends of this LINE OA. "
                        "Use carefully — this reaches everyone.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Text message to broadcast (max 5000 chars)",
                    }
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="send_push_message",
            description="Send a direct text message to a specific user by their LINE user ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "LINE user ID (starts with U)",
                    },
                    "message": {
                        "type": "string",
                        "description": "Text message to send",
                    },
                },
                "required": ["user_id", "message"],
            },
        ),
        Tool(
            name="send_multicast",
            description="Send a text message to multiple users at once (max 500 user IDs).",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of LINE user IDs (max 500)",
                    },
                    "message": {
                        "type": "string",
                        "description": "Text message to send",
                    },
                },
                "required": ["user_ids", "message"],
            },
        ),
        Tool(
            name="get_message_delivery_stats",
            description="Get delivery statistics (sent, opened, clicked) for messages "
                        "sent on a specific date.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYYMMDD format",
                    }
                },
                "required": ["date"],
            },
        ),
        Tool(
            name="get_user_profile",
            description="Get profile info of a LINE user: display name, picture, status message.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "LINE user ID",
                    }
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="list_rich_menus",
            description="List all rich menus created for this LINE OA.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        result = await _dispatch_tool(name, arguments)
        return [TextContent(type="text", text=result)]
    except httpx.HTTPStatusError as e:
        error_body = e.response.text if e.response else "No response body"
        return [TextContent(
            type="text",
            text=f"LINE API Error {e.response.status_code}: {error_body}",
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _dispatch_tool(name: str, args: dict) -> str:
    match name:
        # ---- Free Tier ----
        case "get_account_info":
            return await _get_account_info()
        case "get_friend_count":
            return await _get_friend_count(args.get("date"))
        case "get_message_quota":
            return await _get_message_quota()

        # ---- Pro Tier ----
        case "send_broadcast":
            return await _send_broadcast(args["message"])
        case "send_push_message":
            return await _send_push_message(args["user_id"], args["message"])
        case "send_multicast":
            return await _send_multicast(args["user_ids"], args["message"])
        case "get_message_delivery_stats":
            return await _get_message_delivery_stats(args["date"])
        case "get_user_profile":
            return await _get_user_profile(args["user_id"])
        case "list_rich_menus":
            return await _list_rich_menus()

        case _:
            return f"Unknown tool: {name}"


# =============================================================
# Tool Implementations
# =============================================================

async def _get_account_info() -> str:
    data = await line.get("/info")
    return json.dumps({
        "bot_name": data.get("displayName", "N/A"),
        "user_id": data.get("userId", "N/A"),
        "basic_id": data.get("basicId", "N/A"),
        "premium_id": data.get("premiumId", "N/A"),
        "picture_url": data.get("pictureUrl", "N/A"),
        "chat_mode": data.get("chatMode", "N/A"),
        "mark_as_read_mode": data.get("markAsReadMode", "N/A"),
    }, ensure_ascii=False, indent=2)


async def _get_friend_count(date: str | None = None) -> str:
    if not date:
        yesterday = datetime.now() - timedelta(days=1)
        date = yesterday.strftime("%Y%m%d")
    data = await line.get(f"/insight/followers?date={date}")
    return json.dumps({
        "date": date,
        "followers": data.get("followers", 0),
        "targeted_reaches": data.get("targetedReaches", 0),
        "blocks": data.get("blocks", 0),
        "status": data.get("status", "unknown"),
    }, ensure_ascii=False, indent=2)


async def _get_message_quota() -> str:
    quota = await line.get("/message/quota")
    consumption = await line.get("/message/quota/consumption")
    total = quota.get("value", 0)
    used = consumption.get("totalUsage", 0)
    remaining = total - used if total > 0 else "unlimited"
    return json.dumps({
        "quota_type": quota.get("type", "N/A"),
        "total_quota": total,
        "used_this_month": used,
        "remaining": remaining,
    }, ensure_ascii=False, indent=2)


async def _send_broadcast(message: str) -> str:
    data = {
        "messages": [{"type": "text", "text": message}]
    }
    result = await line.post("/message/broadcast", data)
    return f"Broadcast sent successfully. Message: '{message[:50]}...'"


async def _send_push_message(user_id: str, message: str) -> str:
    data = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}],
    }
    result = await line.post("/message/push", data)
    return f"Push message sent to {user_id}. Message: '{message[:50]}...'"


async def _send_multicast(user_ids: list[str], message: str) -> str:
    if len(user_ids) > 500:
        return "Error: Maximum 500 user IDs allowed per multicast."
    data = {
        "to": user_ids,
        "messages": [{"type": "text", "text": message}],
    }
    result = await line.post("/message/multicast", data)
    return f"Multicast sent to {len(user_ids)} users. Message: '{message[:50]}...'"


async def _get_message_delivery_stats(date: str) -> str:
    data = await line.get(f"/insight/message/delivery?date={date}")
    return json.dumps({
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
    }, ensure_ascii=False, indent=2)


async def _get_user_profile(user_id: str) -> str:
    data = await line.get(f"/profile/{user_id}")
    return json.dumps({
        "user_id": data.get("userId", "N/A"),
        "display_name": data.get("displayName", "N/A"),
        "picture_url": data.get("pictureUrl", "N/A"),
        "status_message": data.get("statusMessage", "N/A"),
        "language": data.get("language", "N/A"),
    }, ensure_ascii=False, indent=2)


async def _list_rich_menus() -> str:
    data = await line.get("/richmenu/list")
    menus = data.get("richmenus", [])
    if not menus:
        return "No rich menus found for this LINE OA."
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


# =============================================================
# Entry Point
# =============================================================

async def main():
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
