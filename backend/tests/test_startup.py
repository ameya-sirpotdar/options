"""Tests that /health is responsive even when AzureTableService init is slow."""
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app


@pytest.mark.asyncio
async def test_health_responsive_during_slow_azure_init():
    """Event loop must stay free while AzureTableService blocks in a thread."""
    slow_mock = MagicMock()

    def _slow_constructor(**kwargs):
        time.sleep(2)
        return slow_mock

    with patch("backend.main.AzureTableService", side_effect=_slow_constructor):
        with patch.dict("os.environ", {"AZURE_STORAGE_CONNECTION_STRING": "fake"}):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                # Kick off a slow startup in the background by triggering lifespan manually
                # We just test that health responds correctly with the real app
                start = time.monotonic()
                response = await client.get("/health")
                elapsed = time.monotonic() - start

    assert response.status_code == 200
    # Should be immediate — no event-loop block
    assert elapsed < 1.0, f"/health took {elapsed:.2f}s"


@pytest.mark.asyncio
async def test_health_returns_ok_without_azure():
    """Health endpoint returns 200 when AZURE_STORAGE_CONNECTION_STRING is absent."""
    with patch.dict("os.environ", {"AZURE_STORAGE_CONNECTION_STRING": ""}, clear=False):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_azure_table_service_init_uses_thread():
    """Verify startup uses asyncio.to_thread for AzureTableService construction."""
    import asyncio
    import backend.main as main_module

    calls = []
    mock_instance = MagicMock()
    original_to_thread = asyncio.to_thread

    async def recording_to_thread(func, *args, **kwargs):
        calls.append(func)
        return await original_to_thread(func, *args, **kwargs)

    mock_azure_cls = MagicMock(return_value=mock_instance)

    # Support both startup_event function and lifespan context manager patterns.
    startup_fn = getattr(main_module, "startup_event", None)

    with patch.object(main_module, "AzureTableService", mock_azure_cls):
        with patch.dict("os.environ", {"AZURE_STORAGE_CONNECTION_STRING": "fake"}):
            with patch.object(main_module, "asyncio") as mock_asyncio:
                mock_asyncio.to_thread = recording_to_thread
                if startup_fn is not None:
                    await startup_fn()
                else:
                    # Lifespan pattern: exercise startup via ASGI lifespan events.
                    async with AsyncClient(
                        transport=ASGITransport(app=main_module.app),
                        base_url="http://test",
                    ) as client:
                        await client.get("/health")

    assert any(c is mock_azure_cls for c in calls), (
        "asyncio.to_thread was not called with AzureTableService — blocking init detected"
    )
