"""Async LINE API wrapper — all HTTP calls go through here.

Centralizes authorization headers, error handling, and rate limit awareness.
Never expose raw LINE API error bodies to the user.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.config import get_settings

logger = logging.getLogger("linewhiz.services.line_api")

LINE_API_BASE = "https://api.line.me/v2/bot"
LINE_DATA_API_BASE = "https://api-data.line.me/v2/bot"

# Human-friendly error messages — never expose raw LINE error bodies
ERROR_MESSAGES: dict[int, str] = {
    400: "Invalid request. Check your input.",
    401: "LINE auth failed. Check LINE_CHANNEL_ACCESS_TOKEN.",
    403: "Permission denied. Your LINE OA plan may not support this.",
    404: "Not found. Check the user ID or rich menu ID.",
    429: "LINE rate limit hit. Wait a moment and retry.",
    500: "LINE Platform error. Temporary — retry in a few seconds.",
}


class LineAPIClient:
    """Async HTTP client for the LINE Messaging API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._token = settings.line_channel_access_token
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def get(self, path: str, *, base_url: str = LINE_API_BASE) -> dict[str, Any]:
        """Send a GET request to the LINE API."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{base_url}{path}",
                headers=self._headers,
                timeout=30,
            )
            self._handle_error(resp)
            return resp.json()  # type: ignore[no-any-return]

    async def post(
        self, path: str, data: dict[str, Any], *, base_url: str = LINE_API_BASE
    ) -> dict[str, Any]:
        """Send a POST request to the LINE API."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{base_url}{path}",
                headers=self._headers,
                json=data,
                timeout=30,
            )
            self._handle_error(resp)
            # Some POST endpoints return empty body
            if resp.status_code == 200 and resp.text:
                return resp.json()  # type: ignore[no-any-return]
            return {"status": "ok", "code": resp.status_code}

    def _handle_error(self, resp: httpx.Response) -> None:
        """Raise a friendly error if the response is not OK."""
        if resp.is_success:
            return
        status = resp.status_code
        friendly = ERROR_MESSAGES.get(status, f"LINE API returned HTTP {status}.")
        logger.error("LINE API error %d: %s", status, resp.text)
        raise LineAPIError(status_code=status, message=friendly)


class LineAPIError(Exception):
    """Friendly LINE API error — safe to surface to user."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)
