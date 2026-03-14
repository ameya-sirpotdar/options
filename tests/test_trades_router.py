from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest

from backend.main import app

client = TestClient(app)


MOCK_TRADES = [
    {
        "symbol": "AAPL",
        "expiration": "2024-03-15",
        "strike": 185.0,
        "option_type": "call",
        "delta": 0.45,
        "theta": -0.05,
        "iv": 0.28,
        "premium": 3.50,
        "tradability_score": 0.72,
    },
    {
        "symbol": "TSLA",
        "expiration": "2024-03-15",
        "strike": 220.0,
        "option_type": "put",
        "delta": -0.40,
        "theta": -0.07,
        "iv": 0.45,
        "premium": 5.20,
        "tradability_score": 0.55,
    },
    {
        "symbol": "MSFT",
        "expiration": "2024-03-15",
        "strike": 375.0,
        "option_type": "call",
        "delta": 0.50,
        "theta": -0.04,
        "iv": 0.22,
        "premium": 4.10,
        "tradability_score": 0.87,
    },
]


class TestGetTradesEndpoint:
    def test_returns_200_with_trades_list(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")

            assert response.status_code == 200

    def test_response_is_list(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            assert isinstance(data, list)

    def test_response_list_length_matches(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            assert len(data) == 3

    def test_each_item_contains_symbol(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            for item in data:
                assert "symbol" in item

    def test_each_item_contains_tradability_score(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            for item in data:
                assert "tradability_score" in item

    def test_each_item_contains_strike(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            for item in data:
                assert "strike" in item

    def test_each_item_contains_option_type(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            for item in data:
                assert "option_type" in item

    def test_each_item_contains_expiration(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            for item in data:
                assert "expiration" in item

    def test_each_item_contains_delta(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            for item in data:
                assert "delta" in item

    def test_each_item_contains_theta(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            for item in data:
                assert "theta" in item

    def test_each_item_contains_iv(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            for item in data:
                assert "iv" in item

    def test_each_item_contains_premium(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            for item in data:
                assert "premium" in item

    def test_first_item_symbol_matches(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            assert data[0]["symbol"] == "AAPL"

    def test_tradability_score_is_float(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            for item in data:
                assert isinstance(item["tradability_score"], float)

    def test_returns_empty_list_when_no_trades(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = []

            response = client.get("/trades")
            data = response.json()

            assert response.status_code == 200
            assert data == []

    def test_service_called_once(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            client.get("/trades")

            mock_service.get_trades_with_scores.assert_called_once()

    def test_returns_500_on_service_exception(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.side_effect = Exception("Service failure")

            response = client.get("/trades")

            assert response.status_code == 500

    def test_response_is_json(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")

            assert "application/json" in response.headers["content-type"]

    def test_strike_value_matches(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            assert data[2]["strike"] == 375.0

    def test_option_type_matches(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            assert data[2]["option_type"] == "call"

    def test_delta_value_matches(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            assert data[2]["delta"] == 0.50

    def test_iv_value_matches(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            assert data[2]["iv"] == 0.22

    def test_premium_value_matches(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            assert data[2]["premium"] == 4.10

    def test_theta_value_matches(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            assert data[2]["theta"] == -0.04

    def test_expiration_value_matches(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            assert data[2]["expiration"] == "2024-03-15"

    def test_tradability_score_value_matches(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            assert data[2]["tradability_score"] == 0.87

    def test_second_item_symbol_matches(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            assert data[1]["symbol"] == "TSLA"

    def test_third_item_symbol_matches(self):
        with patch(
            "backend.api.routers.trades.TradesComparisonService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_trades_with_scores.return_value = MOCK_TRADES

            response = client.get("/trades")
            data = response.json()

            assert data[2]["symbol"] == "MSFT"