"""Async LINE Messaging API client wrapper."""

import os
from typing import Any

import httpx

LINE_API_BASE = "https://api.line.me/v2/bot"
LINE_DATA_API_BASE = "https://api-data.line.me/v2/bot"


class LineClient:
    """Async HTTP client for LINE Messaging API."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def get(self, path: str) -> dict[str, Any]:
        """Send GET request to LINE API."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{LINE_API_BASE}{path}",
                headers=self.headers,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]

    async def post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        """Send POST request to LINE API."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{LINE_API_BASE}{path}",
                headers=self.headers,
                json=data,
                timeout=30,
            )
            resp.raise_for_status()
            if resp.status_code == 200 and resp.text:
                return resp.json()  # type: ignore[no-any-return]
            return {"status": "ok", "code": resp.status_code}
