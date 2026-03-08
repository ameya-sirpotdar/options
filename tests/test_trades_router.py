tests/test_trades_router.py
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest

from backend.main import app
from backend.models.tradability import TradabilityScore

client = TestClient(app)


@pytest.fixture
def mock_tradability_score():
    return TradabilityScore(
        symbol="AAPL",
        score=0.85,
        rank=1,
        liquidity_score=0.90,
        volatility_score=0.80,
        momentum_score=0.85,
        spread_score=0.88,
        volume_score=0.82,
        raw_metrics={
            "avg_volume": 75000000.0,
            "avg_spread_pct": 0.05,
            "volatility_30d": 0.22,
            "momentum_14d": 0.08,
            "bid_ask_ratio": 0.98,
        },
    )


@pytest.fixture
def mock_tradability_scores():
    return [
        TradabilityScore(
            symbol="AAPL",
            score=0.85,
            rank=1,
            liquidity_score=0.90,
            volatility_score=0.80,
            momentum_score=0.85,
            spread_score=0.88,
            volume_score=0.82,
            raw_metrics={
                "avg_volume": 75000000.0,
                "avg_spread_pct": 0.05,
                "volatility_30d": 0.22,
                "momentum_14d": 0.08,
                "bid_ask_ratio": 0.98,
            },
        ),
        TradabilityScore(
            symbol="MSFT",
            score=0.78,
            rank=2,
            liquidity_score=0.82,
            volatility_score=0.75,
            momentum_score=0.78,
            spread_score=0.80,
            volume_score=0.76,
            raw_metrics={
                "avg_volume": 30000000.0,
                "avg_spread_pct": 0.07,
                "volatility_30d": 0.19,
                "momentum_14d": 0.05,
                "bid_ask_ratio": 0.97,
            },
        ),
        TradabilityScore(
            symbol="GOOGL",
            score=0.70,
            rank=3,
            liquidity_score=0.75,
            volatility_score=0.68,
            momentum_score=0.72,
            spread_score=0.70,
            volume_score=0.65,
            raw_metrics={
                "avg_volume": 20000000.0,
                "avg_spread_pct": 0.10,
                "volatility_30d": 0.25,
                "momentum_14d": 0.03,
                "bid_ask_ratio": 0.96,
            },
        ),
    ]


class TestGetBestTrade:
    def test_get_best_trade_success(self, mock_tradability_score, mock_tradability_scores):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.return_value = (
                mock_tradability_score,
                mock_tradability_scores,
            )

            response = client.get("/trades/best")

            assert response.status_code == 200
            data = response.json()
            assert "best_trade" in data
            assert "all_scores" in data
            assert data["best_trade"]["symbol"] == "AAPL"
            assert data["best_trade"]["score"] == pytest.approx(0.85, rel=1e-3)
            assert data["best_trade"]["rank"] == 1
            assert len(data["all_scores"]) == 3

    def test_get_best_trade_response_structure(self, mock_tradability_score, mock_tradability_scores):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.return_value = (
                mock_tradability_score,
                mock_tradability_scores,
            )

            response = client.get("/trades/best")

            assert response.status_code == 200
            data = response.json()
            best = data["best_trade"]

            assert "symbol" in best
            assert "score" in best
            assert "rank" in best
            assert "liquidity_score" in best
            assert "volatility_score" in best
            assert "momentum_score" in best
            assert "spread_score" in best
            assert "volume_score" in best
            assert "raw_metrics" in best

    def test_get_best_trade_all_scores_ordered(self, mock_tradability_score, mock_tradability_scores):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.return_value = (
                mock_tradability_score,
                mock_tradability_scores,
            )

            response = client.get("/trades/best")

            assert response.status_code == 200
            data = response.json()
            scores = data["all_scores"]

            assert scores[0]["symbol"] == "AAPL"
            assert scores[1]["symbol"] == "MSFT"
            assert scores[2]["symbol"] == "GOOGL"
            assert scores[0]["rank"] == 1
            assert scores[1]["rank"] == 2
            assert scores[2]["rank"] == 3

    def test_get_best_trade_scores_descending(self, mock_tradability_score, mock_tradability_scores):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.return_value = (
                mock_tradability_score,
                mock_tradability_scores,
            )

            response = client.get("/trades/best")

            assert response.status_code == 200
            data = response.json()
            scores = data["all_scores"]

            for i in range(len(scores) - 1):
                assert scores[i]["score"] >= scores[i + 1]["score"]

    def test_get_best_trade_no_candidates(self):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.side_effect = ValueError(
                "No candidates available"
            )

            response = client.get("/trades/best")

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    def test_get_best_trade_service_error(self):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.side_effect = RuntimeError(
                "Data fetch failed"
            )

            response = client.get("/trades/best")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_get_best_trade_with_symbol_filter(self, mock_tradability_score, mock_tradability_scores):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.return_value = (
                mock_tradability_score,
                mock_tradability_scores,
            )

            response = client.get("/trades/best?symbols=AAPL,MSFT,GOOGL")

            assert response.status_code == 200
            mock_service_instance.get_best_trade.assert_called_once()

    def test_get_best_trade_with_top_n(self, mock_tradability_score, mock_tradability_scores):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.return_value = (
                mock_tradability_score,
                mock_tradability_scores,
            )

            response = client.get("/trades/best?top_n=3")

            assert response.status_code == 200
            mock_service_instance.get_best_trade.assert_called_once()

    def test_get_best_trade_invalid_top_n(self):
        response = client.get("/trades/best?top_n=-1")
        assert response.status_code == 422

    def test_get_best_trade_invalid_top_n_zero(self):
        response = client.get("/trades/best?top_n=0")
        assert response.status_code == 422

    def test_get_best_trade_raw_metrics_present(self, mock_tradability_score, mock_tradability_scores):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.return_value = (
                mock_tradability_score,
                mock_tradability_scores,
            )

            response = client.get("/trades/best")

            assert response.status_code == 200
            data = response.json()
            best = data["best_trade"]
            raw = best["raw_metrics"]

            assert "avg_volume" in raw
            assert "avg_spread_pct" in raw
            assert "volatility_30d" in raw
            assert "momentum_14d" in raw
            assert "bid_ask_ratio" in raw

    def test_get_best_trade_score_bounds(self, mock_tradability_score, mock_tradability_scores):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.return_value = (
                mock_tradability_score,
                mock_tradability_scores,
            )

            response = client.get("/trades/best")

            assert response.status_code == 200
            data = response.json()

            for score_entry in data["all_scores"]:
                assert 0.0 <= score_entry["score"] <= 1.0
                assert 0.0 <= score_entry["liquidity_score"] <= 1.0
                assert 0.0 <= score_entry["volatility_score"] <= 1.0
                assert 0.0 <= score_entry["momentum_score"] <= 1.0
                assert 0.0 <= score_entry["spread_score"] <= 1.0
                assert 0.0 <= score_entry["volume_score"] <= 1.0

    def test_get_best_trade_best_is_first_in_all_scores(self, mock_tradability_score, mock_tradability_scores):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.return_value = (
                mock_tradability_score,
                mock_tradability_scores,
            )

            response = client.get("/trades/best")

            assert response.status_code == 200
            data = response.json()
            best_symbol = data["best_trade"]["symbol"]
            first_in_all = data["all_scores"][0]["symbol"]

            assert best_symbol == first_in_all

    def test_get_best_trade_single_candidate(self):
        single_score = TradabilityScore(
            symbol="TSLA",
            score=0.60,
            rank=1,
            liquidity_score=0.65,
            volatility_score=0.55,
            momentum_score=0.62,
            spread_score=0.60,
            volume_score=0.58,
            raw_metrics={
                "avg_volume": 10000000.0,
                "avg_spread_pct": 0.15,
                "volatility_30d": 0.40,
                "momentum_14d": 0.02,
                "bid_ask_ratio": 0.95,
            },
        )

        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.return_value = (
                single_score,
                [single_score],
            )

            response = client.get("/trades/best")

            assert response.status_code == 200
            data = response.json()
            assert data["best_trade"]["symbol"] == "TSLA"
            assert len(data["all_scores"]) == 1

    def test_get_best_trade_content_type(self, mock_tradability_score, mock_tradability_scores):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.return_value = (
                mock_tradability_score,
                mock_tradability_scores,
            )

            response = client.get("/trades/best")

            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]

    def test_get_best_trade_method_not_allowed(self):
        response = client.post("/trades/best")
        assert response.status_code == 405

    def test_get_best_trade_calls_service_once(self, mock_tradability_score, mock_tradability_scores):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.return_value = (
                mock_tradability_score,
                mock_tradability_scores,
            )

            client.get("/trades/best")

            mock_service_instance.get_best_trade.assert_called_once()

    def test_get_best_trade_empty_symbols_list(self):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.side_effect = ValueError(
                "Symbols list cannot be empty"
            )

            response = client.get("/trades/best?symbols=")

            assert response.status_code in (404, 422)

    def test_get_best_trade_numeric_score_types(self, mock_tradability_score, mock_tradability_scores):
        with patch(
            "backend.api.routers.trades.TradabilityService"
        ) as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.get_best_trade.return_value = (
                mock_tradability_score,
                mock_tradability_scores,
            )

            response = client.get("/trades/best")

            assert response.status_code == 200
            data = response.json()
            best = data["best_trade"]

            assert isinstance(best["score"], float)
            assert isinstance(best["rank"], int)
            assert isinstance(best["liquidity_score"], float)
            assert isinstance(best["volatility_score"], float)
            assert isinstance(best["momentum_score"], float)
            assert isinstance(best["spread_score"], float)
            assert isinstance(best["volume_score"], float)