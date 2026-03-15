from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest

from backend.main import app

client = TestClient(app)


MOCK_CANDIDATES = [
    {
        "symbol": "AAPL",
        "expiration": "2024-03-15",
        "strike": 185.0,
        "option_type": "call",
        "delta": 0.45,
        "theta": -0.05,
        "iv": 0.28,
        "premium": 3.50,
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
    },
]


class TestGetTradesEndpoint:
    def test_returns_200_with_best_candidate(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = MOCK_CANDIDATES[2]

            response = client.get("/trades")

            assert response.status_code == 200

    def test_response_contains_symbol(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = MOCK_CANDIDATES[2]

            response = client.get("/trades")
            data = response.json()

            assert "symbol" in data

    def test_response_contains_score(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert "score" in data

    def test_response_symbol_matches_best_candidate(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert data["symbol"] == "MSFT"

    def test_response_contains_strike(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert "strike" in data

    def test_response_contains_option_type(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert "option_type" in data

    def test_response_contains_expiration(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert "expiration" in data

    def test_response_contains_delta(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert "delta" in data

    def test_response_contains_theta(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert "theta" in data

    def test_response_contains_iv(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert "iv" in data

    def test_response_contains_premium(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert "premium" in data

    def test_rank_candidates_called_with_fetched_data(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = dict(MOCK_CANDIDATES[0])

            client.get("/trades")

            mock_rank.assert_called_once_with(MOCK_CANDIDATES)

    def test_fetch_candidates_called_once(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = dict(MOCK_CANDIDATES[0])

            client.get("/trades")

            mock_fetch.assert_called_once()

    def test_returns_404_when_no_candidates(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            mock_fetch.return_value = []
            mock_rank.return_value = None

            response = client.get("/trades")

            assert response.status_code == 404

    def test_404_response_contains_detail(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            mock_fetch.return_value = []
            mock_rank.return_value = None

            response = client.get("/trades")
            data = response.json()

            assert "detail" in data

    def test_score_value_is_float(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[0])
            best["score"] = 0.75
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert isinstance(data["score"], float)

    def test_strike_value_matches_candidate(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert data["strike"] == 375.0

    def test_option_type_matches_candidate(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert data["option_type"] == "call"

    def test_delta_value_matches_candidate(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert data["delta"] == 0.50

    def test_iv_value_matches_candidate(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert data["iv"] == 0.22

    def test_premium_value_matches_candidate(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert data["premium"] == 4.10

    def test_returns_500_on_fetch_exception(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch:
            mock_fetch.side_effect = Exception("Storage connection failed")

            response = client.get("/trades")

            assert response.status_code == 500

    def test_returns_500_on_rank_exception(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.side_effect = Exception("Ranking failed")

            response = client.get("/trades")

            assert response.status_code == 500

    def test_single_candidate_returns_200(self):
        single = [MOCK_CANDIDATES[0]]
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[0])
            best["score"] = 0.65
            mock_fetch.return_value = single
            mock_rank.return_value = best

            response = client.get("/trades")

            assert response.status_code == 200

    def test_single_candidate_symbol_correct(self):
        single = [MOCK_CANDIDATES[0]]
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[0])
            best["score"] = 0.65
            mock_fetch.return_value = single
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert data["symbol"] == "AAPL"

    def test_response_is_json(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[1])
            best["score"] = 0.55
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")

            assert response.headers["content-type"] == "application/json"

    def test_theta_value_matches_candidate(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert data["theta"] == -0.04

    def test_expiration_value_matches_candidate(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades")
            data = response.json()

            assert data["expiration"] == "2024-03-15"


class TestGetBestTradeEndpointLegacy:
    """Tests for the legacy /trades/best endpoint to ensure backward compatibility."""

    def test_returns_200_with_best_candidate(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = MOCK_CANDIDATES[2]

            response = client.get("/trades/best")

            assert response.status_code == 200

    def test_response_contains_symbol(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = MOCK_CANDIDATES[2]

            response = client.get("/trades/best")
            data = response.json()

            assert "symbol" in data

    def test_response_symbol_matches_best_candidate(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            best = dict(MOCK_CANDIDATES[2])
            best["score"] = 0.87
            mock_fetch.return_value = MOCK_CANDIDATES
            mock_rank.return_value = best

            response = client.get("/trades/best")
            data = response.json()

            assert data["symbol"] == "MSFT"

    def test_returns_404_when_no_candidates(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch, patch(
            "backend.api.routers.trades.rank_candidates"
        ) as mock_rank:
            mock_fetch.return_value = []
            mock_rank.return_value = None

            response = client.get("/trades/best")

            assert response.status_code == 404

    def test_returns_500_on_fetch_exception(self):
        with patch(
            "backend.api.routers.trades.fetch_candidates"
        ) as mock_fetch:
            mock_fetch.side_effect = Exception("Storage connection failed")

            response = client.get("/trades/best")

            assert response.status_code == 500