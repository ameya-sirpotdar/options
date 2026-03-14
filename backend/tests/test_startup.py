"""Tests that /health is responsive and startup completes correctly."""
import time
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app


@pytest.mark.asyncio
async def test_health_returns_ok():
    """Health endpoint returns 200 OK."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_is_fast():
    """Health endpoint responds quickly without blocking the event loop."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        start = time.monotonic()
        response = await client.get("/health")
        elapsed = time.monotonic() - start

    assert response.status_code == 200
    assert elapsed < 1.0, f"/health took {elapsed:.2f}s"


@pytest.mark.asyncio
async def test_startup_event_runs_without_error():
    """Verify startup_event completes without raising exceptions."""
    import backend.main as main_module

    # startup_event should be callable and complete without error
    await main_module.startup_event()
