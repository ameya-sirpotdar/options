import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from backend.api.poll import router


def make_app(mock_schwab_client=None):
    app = FastAPI()
    app.include_router(router)

    if mock_schwab_client is not None:
        app.state.schwab_client = mock_schwab_client

    return app


class TestPollOptionsEndpoint:
    """POST /poll/options is an internal endpoint and must not be publicly accessible."""

    def test_post_poll_options_not_found(self):
        """POST /poll/options is hidden from the public API and must return 404."""
        mock_client = MagicMock()
        mock_client.get_option_chain = AsyncMock(return_value={})

        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": ["AAPL"]})

        assert response.status_code == 404

    def test_get_poll_options_not_found(self):
        """GET /poll/options is hidden from the public API and must return 404."""
        mock_client = MagicMock()
        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        response = client.get("/poll/options")

        assert response.status_code == 404