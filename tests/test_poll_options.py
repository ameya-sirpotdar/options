import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_payload(tickers):
    return {"tickers": tickers}


def mock_agent_result(tickers):
    return {
        ticker: {
            "ticker": ticker,
            "calls": [{"strike": 100.0, "expiry": "2024-12-20", "premium": 2.5}],
            "puts": [{"strike": 95.0, "expiry": "2024-12-20", "premium": 1.8}],
        }
        for ticker in tickers
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
# Happy path – POST /poll/options
# ---------------------------------------------------------------------------

class TestPollOptionsHappyPath:
    @patch("backend.services.polling_service.run_options_poll")
    def test_single_ticker_returns_200(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        assert response.status_code == 200

    @patch("backend.services.polling_service.run_options_poll")
    def test_single_ticker_response_contains_results(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert "results" in data

    @patch("backend.services.polling_service.run_options_poll")
    def test_single_ticker_result_key_matches_ticker(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert "AAPL" in data["results"]

    @patch("backend.services.polling_service.run_options_poll")
    def test_multiple_tickers_all_present_in_results(self, mock_run):
        tickers = ["AAPL", "MSFT", "GOOG"]
        mock_run.return_value = mock_agent_result(tickers)
        response = client.post("/poll/options", json=make_payload(tickers))
        data = response.json()
        for ticker in tickers:
            assert ticker in data["results"]

    @patch("backend.services.polling_service.run_options_poll")
    def test_response_includes_tickers_field(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert "tickers" in data

    @patch("backend.services.polling_service.run_options_poll")
    def test_response_tickers_field_matches_input(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert "AAPL" in data["tickers"]

    @patch("backend.services.polling_service.run_options_poll")
    def test_agent_called_with_normalised_tickers(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        client.post("/poll/options", json=make_payload(["aapl"]))
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "AAPL" in call_args

    @patch("backend.services.polling_service.run_options_poll")
    def test_ten_tickers_accepted(self, mock_run):
        tickers = ["T" + str(i) for i in range(10)]
        mock_run.return_value = mock_agent_result(tickers)
        response = client.post("/poll/options", json=make_payload(tickers))
        assert response.status_code == 200

    @patch("backend.services.polling_service.run_options_poll")
    def test_response_includes_run_id(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert "run_id" in data

    @patch("backend.services.polling_service.run_options_poll")
    def test_run_id_is_string(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert isinstance(data["run_id"], str)

    @patch("backend.services.polling_service.run_options_poll")
    def test_run_id_is_non_empty(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert len(data["run_id"]) > 0

    @patch("backend.services.polling_service.run_options_poll")
    def test_two_requests_produce_different_run_ids(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        r1 = client.post("/poll/options", json=make_payload(["AAPL"]))
        r2 = client.post("/poll/options", json=make_payload(["AAPL"]))
        assert r1.json()["run_id"] != r2.json()["run_id"]


# ---------------------------------------------------------------------------
# Uppercase normalisation
# ---------------------------------------------------------------------------

class TestUppercaseNormalisation:
    @patch("backend.services.polling_service.run_options_poll")
    def test_lowercase_ticker_normalised_to_uppercase(self, mock_run):
        mock_run.return_value = mock_agent_result(["MSFT"])
        response = client.post("/poll/options", json=make_payload(["msft"]))
        data = response.json()
        assert "MSFT" in data["results"]

    @patch("backend.services.polling_service.run_options_poll")
    def test_mixed_case_ticker_normalised(self, mock_run):
        mock_run.return_value = mock_agent_result(["GOOG"])
        response = client.post("/poll/options", json=make_payload(["GoOg"]))
        data = response.json()
        assert "GOOG" in data["results"]

    @patch("backend.services.polling_service.run_options_poll")
    def test_already_uppercase_ticker_unchanged(self, mock_run):
        mock_run.return_value = mock_agent_result(["TSLA"])
        response = client.post("/poll/options", json=make_payload(["TSLA"]))
        data = response.json()
        assert "TSLA" in data["results"]

    @patch("backend.services.polling_service.run_options_poll")
    def test_normalised_ticker_passed_to_agent(self, mock_run):
        mock_run.return_value = mock_agent_result(["NVDA"])
        client.post("/poll/options", json=make_payload(["nvda"]))
        call_args = mock_run.call_args[0][0]
        assert "NVDA" in call_args
        assert "nvda" not in call_args


# ---------------------------------------------------------------------------
# Whitespace handling
# ---------------------------------------------------------------------------

class TestWhitespaceHandling:
    @patch("backend.services.polling_service.run_options_poll")
    def test_ticker_with_leading_whitespace_stripped(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["  AAPL"]))
        assert response.status_code == 200

    @patch("backend.services.polling_service.run_options_poll")
    def test_ticker_with_trailing_whitespace_stripped(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL  "]))
        assert response.status_code == 200

    @patch("backend.services.polling_service.run_options_poll")
    def test_stripped_ticker_present_in_results(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["  AAPL  "]))
        data = response.json()
        assert "AAPL" in data["results"]

    def test_ticker_that_is_only_whitespace_rejected(self):
        response = client.post("/poll/options", json=make_payload(["   "]))
        assert response.status_code == 422

    def test_ticker_that_is_empty_string_rejected(self):
        response = client.post("/poll/options", json=make_payload([""]))
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Duplicate tickers
# ---------------------------------------------------------------------------

class TestDuplicateTickers:
    @patch("backend.services.polling_service.run_options_poll")
    def test_duplicate_tickers_deduplicated(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        client.post("/poll/options", json=make_payload(["AAPL", "AAPL"]))
        call_args = mock_run.call_args[0][0]
        assert call_args.count("AAPL") == 1

    @patch("backend.services.polling_service.run_options_poll")
    def test_duplicate_case_insensitive_deduplicated(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        client.post("/poll/options", json=make_payload(["AAPL", "aapl"]))
        call_args = mock_run.call_args[0][0]
        assert len(call_args) == 1

    @patch("backend.services.polling_service.run_options_poll")
    def test_duplicates_do_not_cause_error(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL", "AAPL", "AAPL"]))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Validation errors – empty / missing tickers
# ---------------------------------------------------------------------------

class TestValidationErrors:
    def test_empty_tickers_list_rejected(self):
        response = client.post("/poll/options", json=make_payload([]))
        assert response.status_code == 422

    def test_missing_tickers_field_rejected(self):
        response = client.post("/poll/options", json={})
        assert response.status_code == 422

    def test_null_tickers_field_rejected(self):
        response = client.post("/poll/options", json={"tickers": None})
        assert response.status_code == 422

    def test_non_list_tickers_rejected(self):
        response = client.post("/poll/options", json={"tickers": "AAPL"})
        assert response.status_code == 422

    def test_integer_ticker_rejected(self):
        response = client.post("/poll/options", json={"tickers": [123]})
        assert response.status_code == 422

    def test_ticker_exceeding_max_length_rejected(self):
        long_ticker = "A" * 11
        response = client.post("/poll/options", json=make_payload([long_ticker]))
        assert response.status_code == 422

    def test_ticker_at_max_length_accepted(self):
        ticker_10 = "A" * 10
        with patch("backend.services.polling_service.run_options_poll") as mock_run:
            mock_run.return_value = mock_agent_result([ticker_10])
            response = client.post("/poll/options", json=make_payload([ticker_10]))
        assert response.status_code == 200

    def test_validation_error_response_has_detail_field(self):
        response = client.post("/poll/options", json=make_payload([]))
        data = response.json()
        assert "detail" in data

    def test_eleven_tickers_rejected(self):
        tickers = ["T" + str(i) for i in range(11)]
        response = client.post("/poll/options", json=make_payload(tickers))
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Agent / service failure
# ---------------------------------------------------------------------------

class TestAgentFailure:
    @patch("backend.services.polling_service.run_options_poll")
    def test_agent_exception_returns_500(self, mock_run):
        mock_run.side_effect = Exception("agent exploded")
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        assert response.status_code == 500

    @patch("backend.services.polling_service.run_options_poll")
    def test_agent_exception_response_has_detail(self, mock_run):
        mock_run.side_effect = Exception("agent exploded")
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert "detail" in data

    @patch("backend.services.polling_service.run_options_poll")
    def test_agent_returns_empty_dict_handled_gracefully(self, mock_run):
        mock_run.return_value = {}
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        assert response.status_code == 200

    @patch("backend.services.polling_service.run_options_poll")
    def test_agent_returns_partial_results(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL", "MSFT"]))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Persistence – AzureTableService integration
# ---------------------------------------------------------------------------

class TestPersistenceIntegration:
    @patch("backend.services.polling_service.run_options_poll")
    def test_persistence_failure_does_not_crash_poll(self, mock_run):
        """Storage errors must be swallowed; the HTTP response must still be 200."""
        mock_run.return_value = mock_agent_result(["AAPL"])
        with patch("backend.main.azure_table_service") as mock_svc:
            mock_svc.upsert_options_contracts.side_effect = Exception("storage unavailable")
            mock_svc.upsert_run_log.side_effect = Exception("storage unavailable")
            response = client.post("/poll/options", json=make_payload(["AAPL"]))
        assert response.status_code == 200

    @patch("backend.services.polling_service.run_options_poll")
    def test_persistence_failure_still_returns_results(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        with patch("backend.main.azure_table_service") as mock_svc:
            mock_svc.upsert_options_contracts.side_effect = Exception("storage unavailable")
            mock_svc.upsert_run_log.side_effect = Exception("storage unavailable")
            response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert "results" in data
        assert "AAPL" in data["results"]

    @patch("backend.services.polling_service.run_options_poll")
    def test_persistence_failure_still_returns_run_id(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        with patch("backend.main.azure_table_service") as mock_svc:
            mock_svc.upsert_options_contracts.side_effect = Exception("storage unavailable")
            mock_svc.upsert_run_log.side_effect = Exception("storage unavailable")
            response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert "run_id" in data

    @patch("backend.services.polling_service.run_options_poll")
    def test_none_azure_service_does_not_crash_poll(self, mock_run):
        """If azure_table_service is None (not configured), poll must still succeed."""
        mock_run.return_value = mock_agent_result(["AAPL"])
        with patch("backend.main.azure_table_service", None):
            response = client.post("/poll/options", json=make_payload(["AAPL"]))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Response structure
# ---------------------------------------------------------------------------

class TestResponseStructure:
    @patch("backend.services.polling_service.run_options_poll")
    def test_response_is_json(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        assert response.headers["content-type"].startswith("application/json")

    @patch("backend.services.polling_service.run_options_poll")
    def test_result_entry_has_ticker_field(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert "ticker" in data["results"]["AAPL"]

    @patch("backend.services.polling_service.run_options_poll")
    def test_result_entry_has_calls_field(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert "calls" in data["results"]["AAPL"]

    @patch("backend.services.polling_service.run_options_poll")
    def test_result_entry_has_puts_field(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert "puts" in data["results"]["AAPL"]

    @patch("backend.services.polling_service.run_options_poll")
    def test_tickers_field_is_list(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert isinstance(data["tickers"], list)

    @patch("backend.services.polling_service.run_options_poll")
    def test_results_field_is_dict(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert isinstance(data["results"], dict)

    @patch("backend.services.polling_service.run_options_poll")
    def test_calls_is_a_list(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert isinstance(data["results"]["AAPL"]["calls"], list)

    @patch("backend.services.polling_service.run_options_poll")
    def test_puts_is_a_list(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        assert isinstance(data["results"]["AAPL"]["puts"], list)

    @patch("backend.services.polling_service.run_options_poll")
    def test_top_level_keys_are_expected(self, mock_run):
        mock_run.return_value = mock_agent_result(["AAPL"])
        response = client.post("/poll/options", json=make_payload(["AAPL"]))
        data = response.json()
        expected_keys = {"run_id", "tickers", "results"}
        assert expected_keys.issubset(data.keys())