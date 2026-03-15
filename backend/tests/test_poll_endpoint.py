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


# NOTE: /poll/options is now an internal-only endpoint (hidden from public API).
# These tests validate the internal polling logic directly via the router,
# not as a publicly advertised REST surface. The public trades API is GET /trades.


SAMPLE_CHAIN_RESPONSE = {
    "symbol": "AAPL",
    "status": "SUCCESS",
    "underlyingPrice": 175.50,
    "callExpDateMap": {
        "2024-01-19:30": {
            "175.0": [
                {
                    "strikePrice": 175.0,
                    "expirationDate": "2024-01-19",
                    "bid": 2.50,
                    "ask": 2.55,
                    "last": 2.52,
                    "volume": 1200,
                    "openInterest": 5000,
                    "delta": 0.52,
                    "gamma": 0.03,
                    "theta": -0.05,
                    "vega": 0.10,
                    "impliedVolatility": 0.25,
                    "inTheMoney": True,
                    "putCall": "CALL",
                    "description": "AAPL Jan 19 2024 175 Call",
                }
            ]
        }
    },
    "putExpDateMap": {
        "2024-01-19:30": {
            "175.0": [
                {
                    "strikePrice": 175.0,
                    "expirationDate": "2024-01-19",
                    "bid": 1.80,
                    "ask": 1.85,
                    "last": 1.82,
                    "volume": 800,
                    "openInterest": 3000,
                    "delta": -0.48,
                    "gamma": 0.03,
                    "theta": -0.04,
                    "vega": 0.09,
                    "impliedVolatility": 0.24,
                    "inTheMoney": False,
                    "putCall": "PUT",
                    "description": "AAPL Jan 19 2024 175 Put",
                }
            ]
        }
    },
}


class TestPollOptionsEndpoint:
    def test_post_poll_options_returns_flat_rows(self):
        mock_client = MagicMock()
        mock_client.get_option_chain = AsyncMock(return_value=SAMPLE_CHAIN_RESPONSE)

        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": ["AAPL"]})

        assert response.status_code == 200
        data = response.json()
        assert "rows" in data
        assert isinstance(data["rows"], list)

    def test_post_poll_options_correct_row_shape(self):
        mock_client = MagicMock()
        mock_client.get_option_chain = AsyncMock(return_value=SAMPLE_CHAIN_RESPONSE)

        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": ["AAPL"]})

        assert response.status_code == 200
        rows = response.json()["rows"]
        assert len(rows) == 2

        call_row = next(r for r in rows if r["putCall"] == "CALL")
        assert call_row["ticker"] == "AAPL"
        assert call_row["strikePrice"] == 175.0
        assert call_row["bid"] == 2.50
        assert call_row["ask"] == 2.55
        assert call_row["delta"] == 0.52
        assert call_row["inTheMoney"] is True

        put_row = next(r for r in rows if r["putCall"] == "PUT")
        assert put_row["ticker"] == "AAPL"
        assert put_row["strikePrice"] == 175.0
        assert put_row["bid"] == 1.80
        assert put_row["inTheMoney"] is False

    def test_post_poll_options_multiple_tickers(self):
        msft_chain = {
            "symbol": "MSFT",
            "status": "SUCCESS",
            "underlyingPrice": 380.0,
            "callExpDateMap": {
                "2024-01-19:30": {
                    "380.0": [
                        {
                            "strikePrice": 380.0,
                            "expirationDate": "2024-01-19",
                            "bid": 5.00,
                            "ask": 5.10,
                            "last": 5.05,
                            "volume": 500,
                            "openInterest": 2000,
                            "delta": 0.50,
                            "gamma": 0.02,
                            "theta": -0.06,
                            "vega": 0.12,
                            "impliedVolatility": 0.22,
                            "inTheMoney": True,
                            "putCall": "CALL",
                            "description": "MSFT Jan 19 2024 380 Call",
                        }
                    ]
                }
            },
            "putExpDateMap": {},
        }

        async def side_effect(ticker, **kwargs):
            if ticker == "AAPL":
                return SAMPLE_CHAIN_RESPONSE
            elif ticker == "MSFT":
                return msft_chain
            return {}

        mock_client = MagicMock()
        mock_client.get_option_chain = AsyncMock(side_effect=side_effect)

        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": ["AAPL", "MSFT"]})

        assert response.status_code == 200
        rows = response.json()["rows"]

        aapl_rows = [r for r in rows if r["ticker"] == "AAPL"]
        msft_rows = [r for r in rows if r["ticker"] == "MSFT"]

        assert len(aapl_rows) == 2
        assert len(msft_rows) == 1

    def test_post_poll_options_empty_tickers(self):
        mock_client = MagicMock()
        mock_client.get_option_chain = AsyncMock(return_value={})

        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": []})

        assert response.status_code == 200
        data = response.json()
        assert data["rows"] == []

    def test_post_poll_options_missing_tickers_field(self):
        mock_client = MagicMock()
        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        response = client.post("/poll/options", json={})

        assert response.status_code == 422

    def test_post_poll_options_schwab_client_called_per_ticker(self):
        mock_client = MagicMock()
        mock_client.get_option_chain = AsyncMock(return_value=SAMPLE_CHAIN_RESPONSE)

        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        client.post("/poll/options", json={"tickers": ["AAPL", "TSLA"]})

        assert mock_client.get_option_chain.call_count == 2
        calls = [call.args[0] for call in mock_client.get_option_chain.call_args_list]
        assert "AAPL" in calls
        assert "TSLA" in calls

    def test_post_poll_options_schwab_error_returns_500(self):
        mock_client = MagicMock()
        mock_client.get_option_chain = AsyncMock(
            side_effect=Exception("Schwab API unavailable")
        )

        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": ["AAPL"]})

        assert response.status_code == 500

    def test_post_poll_options_no_schwab_client_returns_503(self):
        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": ["AAPL"]})

        assert response.status_code == 503

    def test_get_poll_options_not_allowed(self):
        """GET /poll/options is not a supported method; the endpoint is POST-only and internal."""
        mock_client = MagicMock()
        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        response = client.get("/poll/options")

        assert response.status_code == 405

    def test_post_poll_options_empty_chain_response(self):
        mock_client = MagicMock()
        mock_client.get_option_chain = AsyncMock(return_value={})

        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": ["AAPL"]})

        assert response.status_code == 200
        data = response.json()
        assert data["rows"] == []

    def test_post_poll_options_chain_with_no_puts(self):
        chain_no_puts = {
            "symbol": "AAPL",
            "status": "SUCCESS",
            "underlyingPrice": 175.50,
            "callExpDateMap": {
                "2024-01-19:30": {
                    "175.0": [
                        {
                            "strikePrice": 175.0,
                            "expirationDate": "2024-01-19",
                            "bid": 2.50,
                            "ask": 2.55,
                            "last": 2.52,
                            "volume": 1200,
                            "openInterest": 5000,
                            "delta": 0.52,
                            "gamma": 0.03,
                            "theta": -0.05,
                            "vega": 0.10,
                            "impliedVolatility": 0.25,
                            "inTheMoney": True,
                            "putCall": "CALL",
                            "description": "AAPL Jan 19 2024 175 Call",
                        }
                    ]
                }
            },
            "putExpDateMap": {},
        }

        mock_client = MagicMock()
        mock_client.get_option_chain = AsyncMock(return_value=chain_no_puts)

        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": ["AAPL"]})

        assert response.status_code == 200
        rows = response.json()["rows"]
        assert len(rows) == 1
        assert rows[0]["putCall"] == "CALL"

    def test_post_poll_options_row_contains_required_fields(self):
        mock_client = MagicMock()
        mock_client.get_option_chain = AsyncMock(return_value=SAMPLE_CHAIN_RESPONSE)

        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": ["AAPL"]})

        rows = response.json()["rows"]
        required_fields = [
            "ticker",
            "putCall",
            "strikePrice",
            "expirationDate",
            "bid",
            "ask",
            "last",
            "volume",
            "openInterest",
            "delta",
            "gamma",
            "theta",
            "vega",
            "impliedVolatility",
            "inTheMoney",
        ]

        for row in rows:
            for field in required_fields:
                assert field in row, f"Missing field '{field}' in row: {row}"

    def test_post_poll_options_partial_schwab_failure(self):
        """A single ticker failure should propagate as HTTP 500 — partial data is not acceptable."""
        async def side_effect(ticker, **kwargs):
            if ticker == "AAPL":
                return SAMPLE_CHAIN_RESPONSE
            raise Exception("MSFT fetch failed")

        mock_client = MagicMock()
        mock_client.get_option_chain = AsyncMock(side_effect=side_effect)

        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": ["AAPL", "MSFT"]})

        assert response.status_code == 500

    def test_post_poll_options_multiple_expiry_dates(self):
        chain_multi_expiry = {
            "symbol": "AAPL",
            "status": "SUCCESS",
            "underlyingPrice": 175.50,
            "callExpDateMap": {
                "2024-01-19:30": {
                    "175.0": [
                        {
                            "strikePrice": 175.0,
                            "expirationDate": "2024-01-19",
                            "bid": 2.50,
                            "ask": 2.55,
                            "last": 2.52,
                            "volume": 1200,
                            "openInterest": 5000,
                            "delta": 0.52,
                            "gamma": 0.03,
                            "theta": -0.05,
                            "vega": 0.10,
                            "impliedVolatility": 0.25,
                            "inTheMoney": True,
                            "putCall": "CALL",
                            "description": "AAPL Jan 19 2024 175 Call",
                        }
                    ]
                },
                "2024-02-16:60": {
                    "175.0": [
                        {
                            "strikePrice": 175.0,
                            "expirationDate": "2024-02-16",
                            "bid": 4.00,
                            "ask": 4.10,
                            "last": 4.05,
                            "volume": 600,
                            "openInterest": 2500,
                            "delta": 0.53,
                            "gamma": 0.025,
                            "theta": -0.04,
                            "vega": 0.15,
                            "impliedVolatility": 0.26,
                            "inTheMoney": True,
                            "putCall": "CALL",
                            "description": "AAPL Feb 16 2024 175 Call",
                        }
                    ]
                },
            },
            "putExpDateMap": {},
        }

        mock_client = MagicMock()
        mock_client.get_option_chain = AsyncMock(return_value=chain_multi_expiry)

        app = make_app(mock_schwab_client=mock_client)
        client = TestClient(app)

        response = client.post("/poll/options", json={"tickers": ["AAPL"]})

        assert response.status_code == 200
        rows = response.json()["rows"]
        assert len(rows) == 2

        expiry_dates = {r["expirationDate"] for r in rows}
        assert "2024-01-19" in expiry_dates
        assert "2024-02-16" in expiry_dates