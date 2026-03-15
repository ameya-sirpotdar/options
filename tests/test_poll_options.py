import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from backend.main import app

# Set up a module-level mock schwab_client so the endpoint doesn't return 503.
# The startup event does NOT run for a module-level TestClient, so we set it manually.
_mock_schwab_client = MagicMock()
app.state.schwab_client = _mock_schwab_client

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_query_params(tickers):
    return [("tickers", ticker) for ticker in tickers]


def make_sample_chain(ticker):
    """Return a minimal Schwab-format options chain for a ticker."""
    return {
        "symbol": ticker,
        "underlyingPrice": 100.0,
        "callExpDateMap": {
            "2024-12-20:30": {
                "100.0": [
                    {
                        "strikePrice": 100.0,
                        "expirationDate": "2024-12-20",
                        "bid": 2.5,
                        "ask": 2.6,
                        "last": 2.55,
                        "volume": 500,
                        "openInterest": 2000,
                        "delta": 0.5,
                        "gamma": 0.02,
                        "theta": -0.04,
                        "vega": 0.1,
                        "impliedVolatility": 0.25,
                        "inTheMoney": True,
                        "putCall": "CALL",
                    }
                ]
            }
        },
        "putExpDateMap": {
            "2024-12-20:30": {
                "95.0": [
                    {
                        "strikePrice": 95.0,
                        "expirationDate": "2024-12-20",
                        "bid": 1.8,
                        "ask": 1.9,
                        "last": 1.85,
                        "volume": 300,
                        "openInterest": 1500,
                        "delta": -0.3,
                        "gamma": 0.02,
                        "theta": -0.03,
                        "vega": 0.08,
                        "impliedVolatility": 0.22,
                        "inTheMoney": False,
                        "putCall": "PUT",
                    }
                ]
            }
        },
    }


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    def test_health_response_has_expected_keys(self):
        response = client.get("/health")
        data = response.json()
        assert "status" in data


# ---------------------------------------------------------------------------
# Happy path – GET /options-chain
# ---------------------------------------------------------------------------

class TestPollOptionsHappyPath:
    def test_single_ticker_returns_200(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        assert response.status_code == 200

    def test_single_ticker_response_contains_rows(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        data = response.json()
        assert "rows" in data

    def test_single_ticker_response_contains_vix(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        data = response.json()
        assert "vix" in data

    def test_single_ticker_rows_not_empty(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        data = response.json()
        assert len(data["rows"]) > 0

    def test_multiple_tickers_all_present_in_rows(self):
        tickers = ["AAPL", "MSFT"]

        async def mock_chain(ticker, **kwargs):
            return make_sample_chain(ticker)

        _mock_schwab_client.get_option_chain = mock_chain
        response = client.get("/options-chain", params=make_query_params(tickers))
        data = response.json()
        row_tickers = {r["ticker"] for r in data["rows"]}
        for ticker in tickers:
            assert ticker in row_tickers

    def test_ten_tickers_accepted(self):
        tickers = ["T" + str(i) for i in range(10)]

        async def mock_chain(ticker, **kwargs):
            return make_sample_chain(ticker)

        _mock_schwab_client.get_option_chain = mock_chain
        response = client.get("/options-chain", params=make_query_params(tickers))
        assert response.status_code == 200

    def test_client_called_for_each_ticker(self):
        tickers = ["AAPL", "MSFT"]
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        client.get("/options-chain", params=make_query_params(tickers))
        assert _mock_schwab_client.get_option_chain.call_count == 2


# ---------------------------------------------------------------------------
# Uppercase normalisation
# ---------------------------------------------------------------------------

class TestUppercaseNormalisation:
    def test_lowercase_ticker_normalised_to_uppercase(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("MSFT"))
        response = client.get("/options-chain", params=make_query_params(["msft"]))
        data = response.json()
        assert any(r["ticker"] == "MSFT" for r in data["rows"])

    def test_mixed_case_ticker_normalised(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("GOOG"))
        response = client.get("/options-chain", params=make_query_params(["GoOg"]))
        data = response.json()
        assert any(r["ticker"] == "GOOG" for r in data["rows"])

    def test_already_uppercase_ticker_unchanged(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("TSLA"))
        response = client.get("/options-chain", params=make_query_params(["TSLA"]))
        data = response.json()
        assert any(r["ticker"] == "TSLA" for r in data["rows"])

    def test_normalised_ticker_passed_to_client(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("NVDA"))
        client.get("/options-chain", params=make_query_params(["nvda"]))
        call_args = _mock_schwab_client.get_option_chain.call_args[0][0]
        assert call_args == "NVDA"


# ---------------------------------------------------------------------------
# Whitespace handling
# ---------------------------------------------------------------------------

class TestWhitespaceHandling:
    def test_ticker_with_leading_whitespace_stripped(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["  AAPL"]))
        assert response.status_code == 200

    def test_ticker_with_trailing_whitespace_stripped(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL  "]))
        assert response.status_code == 200

    def test_stripped_ticker_present_in_rows(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["  AAPL  "]))
        data = response.json()
        assert any(r["ticker"] == "AAPL" for r in data["rows"])

    def test_ticker_that_is_only_whitespace_rejected(self):
        response = client.get("/options-chain", params=make_query_params(["   "]))
        assert response.status_code == 422

    def test_ticker_that_is_empty_string_rejected(self):
        response = client.get("/options-chain", params=make_query_params([""]))
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Duplicate tickers
# ---------------------------------------------------------------------------

class TestDuplicateTickers:
    def test_duplicate_tickers_deduplicated(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        client.get("/options-chain", params=make_query_params(["AAPL", "AAPL"]))
        assert _mock_schwab_client.get_option_chain.call_count == 1

    def test_duplicate_case_insensitive_deduplicated(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        client.get("/options-chain", params=make_query_params(["AAPL", "aapl"]))
        assert _mock_schwab_client.get_option_chain.call_count == 1

    def test_duplicates_do_not_cause_error(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL", "AAPL", "AAPL"]))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

class TestValidationErrors:
    def test_empty_tickers_list_rejected(self):
        response = client.get("/options-chain")
        assert response.status_code == 422

    def test_ticker_exceeding_max_length_rejected(self):
        long_ticker = "A" * 11
        response = client.get("/options-chain", params=make_query_params([long_ticker]))
        assert response.status_code == 422

    def test_ticker_at_max_length_accepted(self):
        ticker_10 = "A" * 10
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain(ticker_10))
        response = client.get("/options-chain", params=make_query_params([ticker_10]))
        assert response.status_code == 200

    def test_validation_error_response_has_detail_field(self):
        response = client.get("/options-chain")
        data = response.json()
        assert "detail" in data

    def test_eleven_tickers_rejected(self):
        tickers = ["T" + str(i) for i in range(11)]
        response = client.get("/options-chain", params=make_query_params(tickers))
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Schwab service failure
# ---------------------------------------------------------------------------

class TestSchwabFailure:
    def test_schwab_exception_returns_500(self):
        _mock_schwab_client.get_option_chain = AsyncMock(side_effect=Exception("API down"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        assert response.status_code == 500

    def test_schwab_exception_response_has_detail(self):
        _mock_schwab_client.get_option_chain = AsyncMock(side_effect=Exception("API down"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        data = response.json()
        assert "detail" in data

    def test_schwab_returns_empty_chain_returns_empty_rows(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value={})
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        assert response.status_code == 200
        assert response.json()["rows"] == []

    def test_partial_tickers_still_return_200(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Response structure
# ---------------------------------------------------------------------------

class TestResponseStructure:
    def test_response_is_json(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        assert response.headers["content-type"].startswith("application/json")

    def test_rows_field_is_list(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        data = response.json()
        assert isinstance(data["rows"], list)

    def test_vix_field_is_present(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        data = response.json()
        assert "vix" in data

    def test_row_has_strike_field(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        data = response.json()
        assert "strike" in data["rows"][0]

    def test_row_has_expiry_field(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        data = response.json()
        assert "expiry" in data["rows"][0]

    def test_row_has_type_field(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        data = response.json()
        assert "type" in data["rows"][0]

    def test_row_has_mid_field(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        data = response.json()
        assert "mid" in data["rows"][0]

    def test_top_level_keys_are_expected(self):
        _mock_schwab_client.get_option_chain = AsyncMock(return_value=make_sample_chain("AAPL"))
        response = client.get("/options-chain", params=make_query_params(["AAPL"]))
        data = response.json()
        expected_keys = {"rows", "vix"}
        assert expected_keys.issubset(data.keys())
