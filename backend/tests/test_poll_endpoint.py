import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from backend.api.poll import router


def make_app():
    app = FastAPI()
    app.include_router(router)
    return app


class TestPollOptionsEndpointRemoved:
    """
    The POST /poll/options public endpoint has been removed as part of the
    RESTful API redesign. All requests to this endpoint must return 404.
    Internal polling is now handled exclusively by the background polling
    service and is not exposed as a public API.
    """

    def test_post_poll_options_returns_404(self):
        """POST /poll/options is no longer a public endpoint and must return 404."""
        app = make_app()
        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": ["AAPL"]})

        assert response.status_code == 404

    def test_get_poll_options_returns_404(self):
        """GET /poll/options is not a valid endpoint and must return 404."""
        app = make_app()
        client = TestClient(app)

        response = client.get("/poll/options")

        assert response.status_code == 404

    def test_post_poll_options_empty_tickers_returns_404(self):
        """POST /poll/options with empty tickers still returns 404 — endpoint is removed."""
        app = make_app()
        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": []})

        assert response.status_code == 404

    def test_post_poll_options_missing_body_returns_404(self):
        """POST /poll/options with missing body still returns 404 — endpoint is removed."""
        app = make_app()
        client = TestClient(app)

        response = client.post("/poll/options", json={})

        assert response.status_code == 404

    def test_post_poll_options_multiple_tickers_returns_404(self):
        """POST /poll/options with multiple tickers still returns 404 — endpoint is removed."""
        app = make_app()
        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": ["AAPL", "MSFT"]})

        assert response.status_code == 404