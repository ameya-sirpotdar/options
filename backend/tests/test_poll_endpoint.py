import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestPollOptionsEndpointRemoved:
    """
    The /poll/options endpoint has been removed from the public API as part of
    the RESTful API redesign (issue #88). These tests verify that the endpoint
    is no longer accessible.
    """

    def test_poll_options_endpoint_not_registered(self):
        """
        Verify that /poll/options is not registered on a plain FastAPI app
        (i.e. the poll router no longer exposes this route publicly).
        """
        app = FastAPI()
        client = TestClient(app, raise_server_exceptions=False)

        response = client.post("/poll/options", json={"tickers": ["AAPL"]})

        assert response.status_code == 404

    def test_poll_options_get_not_registered(self):
        """
        Verify that GET /poll/options is also not accessible.
        """
        app = FastAPI()
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/poll/options")

        assert response.status_code == 404