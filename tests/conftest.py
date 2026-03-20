"""Shared test fixtures for LineWhiz tests."""

from typing import Any

import httpx

from src.services.line_api import LINE_API_BASE, LineClient


def make_mock_transport(routes: dict[str, httpx.Response]) -> httpx.MockTransport:
    """Create a mock transport that returns predefined responses based on URL path.

    Args:
        routes: mapping of URL path substrings to httpx.Response objects.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        for route_key, response in routes.items():
            if route_key in path:
                return response
        return httpx.Response(404, json={"error": "Not found"})

    return httpx.MockTransport(handler)


class MockLineClient(LineClient):
    """LineClient that uses a mock transport for testing."""

    def __init__(self, transport: httpx.MockTransport) -> None:
        super().__init__(token="test-token")
        self._transport = transport

    async def get(self, path: str) -> dict[str, Any]:
        async with httpx.AsyncClient(transport=self._transport) as client:
            resp = await client.get(
                f"{LINE_API_BASE}{path}",
                headers=self.headers,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]

    async def post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(transport=self._transport) as client:
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
