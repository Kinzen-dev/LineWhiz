"""Tests for server transport and health endpoint."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient


@pytest.fixture
def sse_client() -> TestClient:
    """Create a test client for the SSE app."""
    from src.server import create_sse_app

    app = create_sse_app()
    return TestClient(app)


def test_health_endpoint(sse_client: TestClient) -> None:
    """Health endpoint returns 200 with server info."""
    resp = sse_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["server"] == "linewhiz"
    assert "tier" in data


def test_health_endpoint_tier(sse_client: TestClient) -> None:
    """Health endpoint reflects current tier."""
    resp = sse_client.get("/health")
    data = resp.json()
    assert data["tier"] in ("free", "pro", "business")
