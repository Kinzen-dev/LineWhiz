"""Tests for LINE API client wrapper."""

import httpx
import pytest

from src.services.line_api import LINE_API_BASE, LineClient


def _mock_transport(
    method: str,
    path: str,
    status: int,
    json_body: dict,
) -> httpx.MockTransport:
    """Create a mock transport for a single endpoint."""

    def handler(request: httpx.Request) -> httpx.Response:
        if path in request.url.path:
            return httpx.Response(status, json=json_body)
        return httpx.Response(404, json={"error": "Not found"})

    return httpx.MockTransport(handler)


class MockableLineClient(LineClient):
    """LineClient subclass that accepts a mock transport."""

    def __init__(self, transport: httpx.MockTransport) -> None:
        super().__init__(token="test-token-123")
        self._transport = transport

    async def get(self, path: str) -> dict:
        async with httpx.AsyncClient(transport=self._transport) as client:
            resp = await client.get(
                f"{LINE_API_BASE}{path}",
                headers=self.headers,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    async def post(self, path: str, data: dict) -> dict:
        async with httpx.AsyncClient(transport=self._transport) as client:
            resp = await client.post(
                f"{LINE_API_BASE}{path}",
                headers=self.headers,
                json=data,
                timeout=30,
            )
            resp.raise_for_status()
            if resp.status_code == 200 and resp.text:
                return resp.json()
            return {"status": "ok", "code": resp.status_code}


@pytest.mark.asyncio
async def test_get_success() -> None:
    transport = _mock_transport("GET", "/info", 200, {"displayName": "TestBot"})
    client = MockableLineClient(transport)

    result = await client.get("/info")
    assert result["displayName"] == "TestBot"


@pytest.mark.asyncio
async def test_get_raises_on_error() -> None:
    transport = _mock_transport("GET", "/info", 401, {"message": "Unauthorized"})
    client = MockableLineClient(transport)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await client.get("/info")
    assert exc_info.value.response.status_code == 401


@pytest.mark.asyncio
async def test_post_success() -> None:
    transport = _mock_transport("POST", "/message/push", 200, {"status": "ok"})
    client = MockableLineClient(transport)

    result = await client.post("/message/push", {"to": "U123", "messages": []})
    assert result["status"] == "ok"


@pytest.mark.asyncio
async def test_post_raises_on_error() -> None:
    transport = _mock_transport("POST", "/message/push", 400, {"message": "Bad request"})
    client = MockableLineClient(transport)

    with pytest.raises(httpx.HTTPStatusError):
        await client.post("/message/push", {"messages": []})


def test_client_sets_auth_header() -> None:
    client = LineClient(token="my-secret-token")

    assert client.headers["Authorization"] == "Bearer my-secret-token"
    assert client.headers["Content-Type"] == "application/json"


def test_client_reads_env_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "env-token-456")
    client = LineClient()

    assert client.token == "env-token-456"
    assert "env-token-456" in client.headers["Authorization"]
