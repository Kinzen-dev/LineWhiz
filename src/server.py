"""LineWhiz MCP Server — Entry point and tool registration.

Premium MCP server that lets AI agents manage LINE Official Accounts.
Supports both STDIO (local) and SSE (remote/Railway) transports.

Run locally:  linewhiz              (or: uv run src/server.py)
Run SSE:      LINEWHIZ_TRANSPORT=sse linewhiz
Test:         mcp dev src/server.py
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from mcp.server import Server
from mcp.types import TextContent, Tool

if TYPE_CHECKING:
    from starlette.applications import Starlette

from src.auth.tiers import check_tier_access, get_current_tier
from src.config import get_settings, setup_logging
from src.db.database import close_db, init_db
from src.services.line_api import LineAPIClient, LineAPIError
from src.tools import account, insights, messaging, richmenu

logger: logging.Logger | None = None

server = Server("linewhiz")


# ─── Tool Definitions ───────────────────────────────────────────────────────

TOOL_DEFINITIONS: list[Tool] = [
    # --- Free tier ---
    Tool(
        name="get_account_info",
        description=("Get LINE Official Account info: name, friend count, plan, picture URL."),
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_friend_count",
        description=(
            "Get the number of LINE OA friends/followers on a specific date. "
            "Provide date as YYYYMMDD or omit for yesterday."
        ),
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
        description=(
            "Get remaining message quota for this month. "
            "Shows total allowed, used, and remaining messages."
        ),
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    # --- Pro tier ---
    Tool(
        name="send_broadcast",
        description=(
            "Send a text message to ALL friends of this LINE OA. "
            "Use carefully — this reaches everyone and costs message quota."
        ),
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
                    "description": "LINE user ID (starts with U, 33 chars)",
                },
                "message": {
                    "type": "string",
                    "description": "Text message to send (max 5000 chars)",
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
                    "description": "Text message to send (max 5000 chars)",
                },
            },
            "required": ["user_ids", "message"],
        },
    ),
    Tool(
        name="get_message_delivery_stats",
        description=(
            "Get delivery statistics (sent, opened, clicked) for messages sent on a specific date."
        ),
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
                    "description": "LINE user ID (starts with U, 33 chars)",
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


# ─── MCP Handlers ────────────────────────────────────────────────────────────


@server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
async def list_tools() -> list[Tool]:
    """Return the list of available tools."""
    return TOOL_DEFINITIONS


@server.call_tool()  # type: ignore[untyped-decorator]
async def call_tool(name: str, arguments: dict) -> list[TextContent]:  # type: ignore[type-arg]
    """MCP tool call handler — implements the request pipeline.

    Pipeline:
      1. check_tier_access(tool_name, tier)
      2. execute tool handler
      3. return result or error (always TextContent)
    """
    assert logger is not None
    try:
        # Step 1: Check tier access
        tier = get_current_tier()
        if not check_tier_access(name, tier):
            return [
                TextContent(
                    type="text",
                    text=f"Access denied: '{name}' is not available on the {tier} tier. "
                    f"Upgrade your plan to use this tool.",
                )
            ]

        # Step 2: Execute tool handler
        result = await _dispatch_tool(name, arguments)

        # Step 3: Return result
        return [TextContent(type="text", text=result)]

    except LineAPIError as e:
        logger.warning("LINE API error in %s: %s", name, e.message)
        return [TextContent(type="text", text=f"LINE API Error: {e.message}")]

    except Exception as e:
        logger.error("Unexpected error in %s: %s", name, str(e), exc_info=True)
        return [TextContent(type="text", text=f"Error: {e!s}")]


async def _dispatch_tool(name: str, args: dict) -> str:  # type: ignore[type-arg]
    """Route tool calls to the appropriate handler."""
    client = LineAPIClient()

    match name:
        # ── Free tier ──
        case "get_account_info":
            return await account.get_account_info(client)
        case "get_friend_count":
            return await account.get_friend_count(client, args.get("date"))
        case "get_message_quota":
            return await account.get_message_quota(client)

        # ── Pro tier ──
        case "send_broadcast":
            return await messaging.send_broadcast(client, args["message"])
        case "send_push_message":
            return await messaging.send_push_message(client, args["user_id"], args["message"])
        case "send_multicast":
            return await messaging.send_multicast(client, args["user_ids"], args["message"])
        case "get_message_delivery_stats":
            return await insights.get_message_delivery_stats(client, args["date"])
        case "get_user_profile":
            return await insights.get_user_profile(client, args["user_id"])
        case "list_rich_menus":
            return await richmenu.list_rich_menus(client)

        case _:
            return f"Unknown tool: {name}"


# ─── Transport: STDIO ────────────────────────────────────────────────────────


async def run_stdio() -> None:
    """Run the MCP server via STDIO transport (local usage)."""
    from mcp.server.stdio import stdio_server

    assert logger is not None
    logger.info("Starting LineWhiz MCP server [STDIO] (tier=%s)", get_current_tier())
    await init_db()

    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    finally:
        await close_db()


# ─── Transport: SSE (for Railway / remote deployment) ────────────────────────


def create_sse_app() -> Starlette:
    """Create a Starlette ASGI app with SSE transport + health endpoint."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    sse_transport = SseServerTransport("/messages/")

    async def handle_sse(request: Request):  # type: ignore[no-untyped-def]
        """SSE connection endpoint — clients connect here."""
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options(),
            )

    async def handle_messages(request: Request):  # type: ignore[no-untyped-def]
        """Message POST endpoint — clients send tool calls here."""
        await sse_transport.handle_post_message(request.scope, request.receive, request._send)

    async def handle_health(request: Request) -> JSONResponse:
        """Health check endpoint for Railway / load balancers."""
        return JSONResponse(
            {"status": "healthy", "server": "linewhiz", "tier": get_current_tier()},
            status_code=200,
        )

    @asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Initialize DB on startup, clean up on shutdown."""
        assert logger is not None
        logger.info("Starting LineWhiz MCP server [SSE] (tier=%s)", get_current_tier())
        await init_db()
        yield
        await close_db()

    return Starlette(
        routes=[
            Route("/health", handle_health, methods=["GET"]),
            Route("/sse", handle_sse),
            Route("/messages/", handle_messages, methods=["POST"]),
        ],
        lifespan=lifespan,
    )


async def run_sse() -> None:
    """Run the MCP server via SSE transport (Railway / remote)."""
    import uvicorn

    app = create_sse_app()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )
    uv_server = uvicorn.Server(config)
    await uv_server.serve()


# ─── Entry Points ────────────────────────────────────────────────────────────


async def main() -> None:
    """Main async entry point — picks transport based on LINEWHIZ_TRANSPORT setting."""
    settings = get_settings()

    if settings.linewhiz_transport == "sse":
        await run_sse()
    else:
        await run_stdio()


def cli_main() -> None:
    """Sync entry point for `linewhiz` CLI command (pyproject.toml [project.scripts])."""
    global logger  # noqa: PLW0603
    logger = setup_logging()
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
