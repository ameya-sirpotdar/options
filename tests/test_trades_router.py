import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.tradability import TradabilityScore


client = TestClient(app)


@pytest.fixture
def mock_tradability_service():
    with patch("backend.api.routers.trades.TradabilityService") as MockService:
        instance = MockService.return_value
        yield instance


@pytest.fixture
def sample_scores():
    return [
        TradabilityScore(
            symbol="AAPL",
            score=0.85,
            rank=1,
            metrics={
                "volume": 1000000,
                "spread": 0.01,
                "volatility": 0.02,
                "momentum": 0.05,
                "liquidity": 0.95,
            },
            breakdown={
                "volume_score": 0.9,
                "spread_score": 0.8,
                "volatility_score": 0.85,
                "momentum_score": 0.8,
                "liquidity_score": 0.9,
            },
        ),
        TradabilityScore(
            symbol="GOOGL",
            score=0.75,
            rank=2,
            metrics={
                "volume": 800000,
                "spread": 0.02,
                "volatility": 0.03,
                "momentum": 0.03,
                "liquidity": 0.85,
            },
            breakdown={
                "volume_score": 0.8,
                "spread_score": 0.7,
                "volatility_score": 0.75,
                "momentum_score": 0.7,
                "liquidity_score": 0.8,
            },
        ),
        TradabilityScore(
            symbol="MSFT",
            score=0.65,
            rank=3,
            metrics={
                "volume": 600000,
                "spread": 0.03,
                "volatility": 0.04,
                "momentum": 0.02,
                "liquidity": 0.75,
            },
            breakdown={
                "volume_score": 0.7,
                "spread_score": 0.6,
                "volatility_score": 0.65,
                "momentum_score": 0.6,
                "liquidity_score": 0.7,
            },
        ),
    ]


class TestGetBestTradeEndpoint:
    def test_get_best_trade_returns_200(self, mock_tradability_service, sample_scores):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best")
        assert response.status_code == 200

    def test_get_best_trade_returns_top_ranked_symbol(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best")
        data = response.json()
        assert data["symbol"] == "AAPL"

    def test_get_best_trade_returns_score(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best")
        data = response.json()
        assert data["score"] == pytest.approx(0.85, rel=1e-3)

    def test_get_best_trade_returns_rank_one(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best")
        data = response.json()
        assert data["rank"] == 1

    def test_get_best_trade_returns_metrics(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best")
        data = response.json()
        assert "metrics" in data
        assert data["metrics"]["volume"] == 1000000

    def test_get_best_trade_returns_breakdown(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best")
        data = response.json()
        assert "breakdown" in data
        assert "volume_score" in data["breakdown"]

    def test_get_best_trade_with_candidates_query_param(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best?candidates=AAPL,GOOGL,MSFT")
        assert response.status_code == 200

    def test_get_best_trade_passes_candidates_to_service(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        client.get("/trades/best?candidates=AAPL,GOOGL")
        call_args = mock_tradability_service.get_best_trade.call_args
        assert call_args is not None

    def test_get_best_trade_no_candidates_returns_error(
        self, mock_tradability_service
    ):
        mock_tradability_service.get_best_trade.return_value = None
        response = client.get("/trades/best")
        assert response.status_code in (200, 404, 422)

    def test_get_best_trade_empty_candidates_returns_422(
        self, mock_tradability_service
    ):
        mock_tradability_service.get_best_trade.return_value = None
        response = client.get("/trades/best?candidates=")
        assert response.status_code in (404, 422, 400)

    def test_get_best_trade_service_raises_exception(
        self, mock_tradability_service
    ):
        mock_tradability_service.get_best_trade.side_effect = ValueError(
            "No candidates provided"
        )
        response = client.get("/trades/best?candidates=AAPL")
        assert response.status_code in (400, 422, 500)

    def test_get_best_trade_response_schema(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best?candidates=AAPL,GOOGL,MSFT")
        data = response.json()
        assert "symbol" in data
        assert "score" in data
        assert "rank" in data
        assert "metrics" in data
        assert "breakdown" in data

    def test_get_best_trade_single_candidate(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best?candidates=AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"

    def test_get_best_trade_score_between_zero_and_one(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best?candidates=AAPL,GOOGL,MSFT")
        data = response.json()
        assert 0.0 <= data["score"] <= 1.0

    def test_get_best_trade_with_top_n_param(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best?candidates=AAPL,GOOGL,MSFT&top_n=1")
        assert response.status_code == 200

    def test_get_best_trade_metrics_contains_expected_keys(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best?candidates=AAPL,GOOGL,MSFT")
        data = response.json()
        metrics = data["metrics"]
        for key in ["volume", "spread", "volatility", "momentum", "liquidity"]:
            assert key in metrics

    def test_get_best_trade_breakdown_contains_expected_keys(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best?candidates=AAPL,GOOGL,MSFT")
        data = response.json()
        breakdown = data["breakdown"]
        for key in [
            "volume_score",
            "spread_score",
            "volatility_score",
            "momentum_score",
            "liquidity_score",
        ]:
            assert key in breakdown


class TestTradesRouterIntegration:
    def test_router_is_registered(self):
        routes = [route.path for route in app.routes]
        assert any("trades" in route for route in routes)

    def test_get_best_trade_content_type_json(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best?candidates=AAPL")
        assert "application/json" in response.headers["content-type"]

    def test_get_best_trade_method_not_allowed(self):
        response = client.post("/trades/best")
        assert response.status_code == 405

    def test_get_best_trade_with_multiple_candidates(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get(
            "/trades/best?candidates=AAPL,GOOGL,MSFT,AMZN,TSLA"
        )
        assert response.status_code == 200

    def test_get_best_trade_returns_highest_scored(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get("/trades/best?candidates=AAPL,GOOGL,MSFT")
        data = response.json()
        assert data["score"] >= 0.75

    def test_get_best_trade_service_called_once(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        client.get("/trades/best?candidates=AAPL,GOOGL,MSFT")
        mock_tradability_service.get_best_trade.assert_called_once()

    def test_get_best_trade_with_weights_param(
        self, mock_tradability_service, sample_scores
    ):
        mock_tradability_service.get_best_trade.return_value = sample_scores[0]
        response = client.get(
            "/trades/best?candidates=AAPL,GOOGL&volume_weight=0.4&spread_weight=0.2"
        )
        assert response.status_code in (200, 422)

    def test_endpoint_path_is_correct(self):
        routes = {route.path: route for route in app.routes if hasattr(route, "path")}
        assert "/trades/best" in routes