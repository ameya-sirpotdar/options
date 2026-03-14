import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from backend.api.routers.options_chain import router


def make_app(mock_schwab_service=None):
    app = FastAPI()
    app.include_router(router)
    if mock_schwab_service is not None:
        app.state.schwab_service = mock_schwab_service
    return app


SAMPLE_CHAIN = {
    "symbol": "QQQ",
    "status": "SUCCESS",
    "underlyingPrice": 450.0,
    "callExpDateMap": {
        "2024-03-15:30": {
            "450.0": [
                {
                    "strikePrice": 450.0,
                    "expirationDate": "2024-03-15",
                    "bid": 3.00,
                    "ask": 3.10,
                    "last": 3.05,
                    "volume": 1000,
                    "openInterest": 4000,
                    "delta": 0.31,
                    "gamma": 0.02,
                    "theta": -0.04,
                    "vega": 0.11,
                    "impliedVolatility": 0.20,
                    "inTheMoney": True,
                    "putCall": "CALL",
                }
            ]
        }
    },
    "putExpDateMap": {
        "2024-03-15:30": {
            "450.0": [
                {
                    "strikePrice": 450.0,
                    "expirationDate": "2024-03-15",
                    "bid": 2.80,
                    "ask": 2.90,
                    "last": 2.85,
                    "volume": 800,
                    "openInterest": 3000,
                    "delta": -0.29,
                    "gamma": 0.02,
                    "theta": -0.03,
                    "vega": 0.10,
                    "impliedVolatility": 0.21,
                    "inTheMoney": False,
                    "putCall": "PUT",
                }
            ]
        }
    },
}

# A chain where the only row has delta 0.80 — far outside default tolerance
CHAIN_HIGH_DELTA = {
    "callExpDateMap": {
        "2024-03-15:30": {
            "450.0": [
                {
                    "strikePrice": 450.0,
                    "expirationDate": "2024-03-15",
                    "bid": 10.0,
                    "ask": 10.5,
                    "last": 10.2,
                    "volume": 500,
                    "openInterest": 2000,
                    "delta": 0.80,
                    "gamma": 0.01,
                    "theta": -0.06,
                    "vega": 0.08,
                    "impliedVolatility": 0.18,
                    "inTheMoney": True,
                    "putCall": "CALL",
                }
            ]
        }
    },
    "putExpDateMap": {},
}


class TestGetOptionsChainEndpoint:
    def test_returns_200_with_rows_and_vix(self):
        mock_service = MagicMock()
        mock_service.get_option_chain = AsyncMock(return_value=SAMPLE_CHAIN)
        client = TestClient(make_app(mock_service))

        response = client.get("/options-chain?tickers=QQQ")

        assert response.status_code == 200
        data = response.json()
        assert "rows" in data
        assert "vix" in data
        assert data["vix"] is None

    def test_row_field_names_normalized(self):
        mock_service = MagicMock()
        mock_service.get_option_chain = AsyncMock(return_value=SAMPLE_CHAIN)
        client = TestClient(make_app(mock_service))

        response = client.get("/options-chain?tickers=QQQ")
        rows = response.json()["rows"]
        assert len(rows) > 0
        row = rows[0]
        assert "strike" in row
        assert "expiry" in row
        assert "type" in row
        assert "iv" in row
        assert "open_interest" in row
        assert "mid" in row
        # Schwab raw names must NOT appear
        assert "strikePrice" not in row
        assert "expirationDate" not in row
        assert "putCall" not in row
        assert "impliedVolatility" not in row
        assert "openInterest" not in row

    def test_mid_computed_correctly(self):
        mock_service = MagicMock()
        mock_service.get_option_chain = AsyncMock(return_value=SAMPLE_CHAIN)
        client = TestClient(make_app(mock_service))

        response = client.get("/options-chain?tickers=QQQ")
        call_row = next(r for r in response.json()["rows"] if r["type"] == "call")
        assert call_row["mid"] == round((3.00 + 3.10) / 2, 4)

    def test_type_field_is_lowercased(self):
        mock_service = MagicMock()
        mock_service.get_option_chain = AsyncMock(return_value=SAMPLE_CHAIN)
        client = TestClient(make_app(mock_service))

        response = client.get("/options-chain?tickers=QQQ")
        types = {r["type"] for r in response.json()["rows"]}
        assert "call" in types
        assert "put" in types
        assert "CALL" not in types
        assert "PUT" not in types

    def test_delta_filter_excludes_out_of_range(self):
        mock_service = MagicMock()
        mock_service.get_option_chain = AsyncMock(return_value=CHAIN_HIGH_DELTA)
        client = TestClient(make_app(mock_service))

        response = client.get("/options-chain?tickers=QQQ&delta=0.30")
        assert response.status_code == 200
        assert response.json()["rows"] == []

    def test_delta_filter_includes_in_range(self):
        mock_service = MagicMock()
        mock_service.get_option_chain = AsyncMock(return_value=SAMPLE_CHAIN)
        client = TestClient(make_app(mock_service))

        # delta=0.30 with tolerance 0.05 — both rows (0.31 and -0.29) should pass
        response = client.get("/options-chain?tickers=QQQ&delta=0.30")
        assert len(response.json()["rows"]) == 2

    def test_missing_tickers_returns_422(self):
        mock_service = MagicMock()
        client = TestClient(make_app(mock_service))
        response = client.get("/options-chain")
        assert response.status_code == 422

    def test_no_schwab_service_returns_503(self):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.get("/options-chain?tickers=QQQ")
        assert response.status_code == 503

    def test_schwab_error_returns_500(self):
        mock_service = MagicMock()
        mock_service.get_option_chain = AsyncMock(side_effect=Exception("API down"))
        client = TestClient(make_app(mock_service))
        response = client.get("/options-chain?tickers=QQQ")
        assert response.status_code == 500

    def test_multiple_tickers_serialized(self):
        mock_service = MagicMock()
        mock_service.get_option_chain = AsyncMock(return_value=SAMPLE_CHAIN)
        client = TestClient(make_app(mock_service))

        response = client.get("/options-chain?tickers=QQQ&tickers=SPY")
        assert response.status_code == 200
        assert mock_service.get_option_chain.call_count == 2

    def test_expiry_param_passed_to_service(self):
        mock_service = MagicMock()
        mock_service.get_option_chain = AsyncMock(return_value=SAMPLE_CHAIN)
        client = TestClient(make_app(mock_service))

        client.get("/options-chain?tickers=QQQ&expiry=2024-03-15")
        call_kwargs = mock_service.get_option_chain.call_args
        assert call_kwargs.kwargs.get("from_date") == "2024-03-15"
        assert call_kwargs.kwargs.get("to_date") == "2024-03-15"
