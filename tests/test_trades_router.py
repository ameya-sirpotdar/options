import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app
from backend.models.tradability import ScoredTrade

client = TestClient(app)


@pytest.fixture
def sample_scored_trades():
    return [
        ScoredTrade(
            trade_id="trade_001",
            symbol="AAPL",
            score=0.92,
            rank=1,
            metrics={
                "liquidity": 0.95,
                "volatility": 0.88,
                "spread": 0.93,
                "volume": 0.91,
                "momentum": 0.85,
            },
        ),
        ScoredTrade(
            trade_id="trade_002",
            symbol="MSFT",
            score=0.87,
            rank=2,
            metrics={
                "liquidity": 0.90,
                "volatility": 0.82,
                "spread": 0.88,
                "volume": 0.86,
                "momentum": 0.80,
            },
        ),
        ScoredTrade(
            trade_id="trade_003",
            symbol="GOOGL",
            score=0.81,
            rank=3,
            metrics={
                "liquidity": 0.85,
                "volatility": 0.78,
                "spread": 0.82,
                "volume": 0.80,
                "momentum": 0.75,
            },
        ),
    ]


@pytest.fixture
def single_scored_trade():
    return [
        ScoredTrade(
            trade_id="trade_001",
            symbol="AAPL",
            score=0.92,
            rank=1,
            metrics={
                "liquidity": 0.95,
                "volatility": 0.88,
                "spread": 0.93,
                "volume": 0.91,
                "momentum": 0.85,
            },
        )
    ]


class TestGetBestTradesEndpoint:
    def test_get_best_trades_returns_200(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            assert response.status_code == 200

    def test_get_best_trades_returns_list(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert isinstance(data, list)

    def test_get_best_trades_returns_correct_count(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert len(data) == 3

    def test_get_best_trades_default_top_n(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ) as mock_service:
            response = client.get("/trades/best")
            assert response.status_code == 200
            mock_service.assert_called_once()

    def test_get_best_trades_with_top_n_param(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades[:2],
        ) as mock_service:
            response = client.get("/trades/best?top_n=2")
            assert response.status_code == 200
            mock_service.assert_called_once_with(top_n=2)

    def test_get_best_trades_top_n_one(self, single_scored_trade):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=single_scored_trade,
        ):
            response = client.get("/trades/best?top_n=1")
            data = response.json()
            assert len(data) == 1

    def test_get_best_trades_response_contains_trade_id(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert "trade_id" in data[0]

    def test_get_best_trades_response_contains_symbol(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert "symbol" in data[0]

    def test_get_best_trades_response_contains_score(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert "score" in data[0]

    def test_get_best_trades_response_contains_rank(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert "rank" in data[0]

    def test_get_best_trades_response_contains_metrics(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert "metrics" in data[0]

    def test_get_best_trades_trade_id_value(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert data[0]["trade_id"] == "trade_001"

    def test_get_best_trades_symbol_value(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert data[0]["symbol"] == "AAPL"

    def test_get_best_trades_score_value(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert data[0]["score"] == pytest.approx(0.92)

    def test_get_best_trades_rank_value(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert data[0]["rank"] == 1

    def test_get_best_trades_ranks_are_ordered(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            ranks = [item["rank"] for item in data]
            assert ranks == sorted(ranks)

    def test_get_best_trades_scores_are_descending(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            scores = [item["score"] for item in data]
            assert scores == sorted(scores, reverse=True)

    def test_get_best_trades_metrics_is_dict(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert isinstance(data[0]["metrics"], dict)

    def test_get_best_trades_metrics_contains_liquidity(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert "liquidity" in data[0]["metrics"]

    def test_get_best_trades_metrics_contains_volatility(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert "volatility" in data[0]["metrics"]

    def test_get_best_trades_metrics_contains_spread(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert "spread" in data[0]["metrics"]

    def test_get_best_trades_metrics_contains_volume(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert "volume" in data[0]["metrics"]

    def test_get_best_trades_metrics_contains_momentum(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert "momentum" in data[0]["metrics"]

    def test_get_best_trades_empty_result(self):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=[],
        ):
            response = client.get("/trades/best")
            assert response.status_code == 200
            assert response.json() == []

    def test_get_best_trades_invalid_top_n_string(self):
        response = client.get("/trades/best?top_n=abc")
        assert response.status_code == 422

    def test_get_best_trades_invalid_top_n_negative(self):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            side_effect=ValueError("top_n must be positive"),
        ):
            response = client.get("/trades/best?top_n=-1")
            assert response.status_code in (400, 422, 500)

    def test_get_best_trades_invalid_top_n_zero(self):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            side_effect=ValueError("top_n must be positive"),
        ):
            response = client.get("/trades/best?top_n=0")
            assert response.status_code in (400, 422, 500)

    def test_get_best_trades_content_type_json(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            assert "application/json" in response.headers["content-type"]

    def test_get_best_trades_second_trade_symbol(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert data[1]["symbol"] == "MSFT"

    def test_get_best_trades_third_trade_symbol(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert data[2]["symbol"] == "GOOGL"

    def test_get_best_trades_second_trade_rank(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert data[1]["rank"] == 2

    def test_get_best_trades_third_trade_rank(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert data[2]["rank"] == 3

    def test_get_best_trades_score_is_float(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert isinstance(data[0]["score"], float)

    def test_get_best_trades_rank_is_int(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert isinstance(data[0]["rank"], int)

    def test_get_best_trades_trade_id_is_string(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert isinstance(data[0]["trade_id"], str)

    def test_get_best_trades_symbol_is_string(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert isinstance(data[0]["symbol"], str)

    def test_get_best_trades_service_called_with_correct_top_n(
        self, sample_scored_trades
    ):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ) as mock_service:
            client.get("/trades/best?top_n=5")
            mock_service.assert_called_once_with(top_n=5)

    def test_get_best_trades_large_top_n(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ) as mock_service:
            response = client.get("/trades/best?top_n=100")
            assert response.status_code == 200
            mock_service.assert_called_once_with(top_n=100)

    def test_get_best_trades_metrics_liquidity_value(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert data[0]["metrics"]["liquidity"] == pytest.approx(0.95)

    def test_get_best_trades_metrics_volatility_value(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert data[0]["metrics"]["volatility"] == pytest.approx(0.88)

    def test_get_best_trades_all_trades_have_required_fields(
        self, sample_scored_trades
    ):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            required_fields = {"trade_id", "symbol", "score", "rank", "metrics"}
            for trade in data:
                assert required_fields.issubset(set(trade.keys()))

    def test_get_best_trades_endpoint_path(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            assert response.status_code == 200

    def test_get_best_trades_post_method_not_allowed(self):
        response = client.post("/trades/best")
        assert response.status_code == 405

    def test_get_best_trades_put_method_not_allowed(self):
        response = client.put("/trades/best")
        assert response.status_code == 405

    def test_get_best_trades_delete_method_not_allowed(self):
        response = client.delete("/trades/best")
        assert response.status_code == 405

    def test_get_best_trades_service_exception_returns_500(self):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            side_effect=Exception("Internal error"),
        ):
            response = client.get("/trades/best")
            assert response.status_code == 500

    def test_get_best_trades_top_n_float_invalid(self):
        response = client.get("/trades/best?top_n=2.5")
        assert response.status_code == 422

    def test_get_best_trades_multiple_calls_consistent(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response1 = client.get("/trades/best")
            response2 = client.get("/trades/best")
            assert response1.json() == response2.json()

    def test_get_best_trades_second_trade_score(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert data[1]["score"] == pytest.approx(0.87)

    def test_get_best_trades_third_trade_score(self, sample_scored_trades):
        with patch(
            "backend.api.routers.trades.tradability_service.get_best_trades",
            return_value=sample_scored_trades,
        ):
            response = client.get("/trades/best")
            data = response.json()
            assert data[2]["score"] == pytest.approx(0.81)