import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_PAYLOAD = {"tickers": ["AAPL", "MSFT", "TSLA"]}


def _mock_poll_success(tickers):
    return {
        "status": "ok",
        "tickers": tickers,
        "results": {t: {"polled": True} for t in tickers},
    }


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_body(self):
        response = client.get("/health")
        data = response.json()
        assert data.get("status") == "ok"


# ---------------------------------------------------------------------------
# POST /poll/options – happy-path
# ---------------------------------------------------------------------------


class TestPollOptionsSuccess:
    @patch("backend.api.poll.run_polling", side_effect=_mock_poll_success)
    def test_returns_200(self, _mock):
        response = client.post("/poll/options", json=VALID_PAYLOAD)
        assert response.status_code == 200

    @patch("backend.api.poll.run_polling", side_effect=_mock_poll_success)
    def test_response_contains_status_ok(self, _mock):
        response = client.post("/poll/options", json=VALID_PAYLOAD)
        assert response.json()["status"] == "ok"

    @patch("backend.api.poll.run_polling", side_effect=_mock_poll_success)
    def test_response_contains_tickers(self, _mock):
        response = client.post("/poll/options", json=VALID_PAYLOAD)
        data = response.json()
        assert set(data["tickers"]) == {"AAPL", "MSFT", "TSLA"}

    @patch("backend.api.poll.run_polling", side_effect=_mock_poll_success)
    def test_response_contains_results(self, _mock):
        response = client.post("/poll/options", json=VALID_PAYLOAD)
        data = response.json()
        assert "results" in data

    @patch("backend.api.poll.run_polling", side_effect=_mock_poll_success)
    def test_run_polling_called_with_normalised_tickers(self, mock_poll):
        payload = {"tickers": ["aapl", "msft"]}
        client.post("/poll/options", json=payload)
        called_tickers = mock_poll.call_args[0][0]
        assert called_tickers == ["AAPL", "MSFT"]

    @patch("backend.api.poll.run_polling", side_effect=_mock_poll_success)
    def test_single_ticker_accepted(self, _mock):
        response = client.post("/poll/options", json={"tickers": ["AAPL"]})
        assert response.status_code == 200

    @patch("backend.api.poll.run_polling", side_effect=_mock_poll_success)
    def test_duplicate_tickers_deduplicated(self, mock_poll):
        payload = {"tickers": ["AAPL", "AAPL", "MSFT"]}
        client.post("/poll/options", json=payload)
        called_tickers = mock_poll.call_args[0][0]
        assert called_tickers.count("AAPL") == 1

    @patch("backend.api.poll.run_polling", side_effect=_mock_poll_success)
    def test_lowercase_tickers_normalised_to_uppercase(self, mock_poll):
        payload = {"tickers": ["tsla", "goog"]}
        client.post("/poll/options", json=payload)
        called_tickers = mock_poll.call_args[0][0]
        for t in called_tickers:
            assert t == t.upper()

    @patch("backend.api.poll.run_polling", side_effect=_mock_poll_success)
    def test_mixed_case_tickers_normalised(self, mock_poll):
        payload = {"tickers": ["ApPl", "mSfT"]}
        client.post("/poll/options", json=payload)
        called_tickers = mock_poll.call_args[0][0]
        assert set(called_tickers) == {"APPL", "MSFT"}

    @patch("backend.api.poll.run_polling", side_effect=_mock_poll_success)
    def test_results_keyed_by_ticker(self, _mock):
        response = client.post("/poll/options", json=VALID_PAYLOAD)
        results = response.json()["results"]
        for ticker in ["AAPL", "MSFT", "TSLA"]:
            assert ticker in results


# ---------------------------------------------------------------------------
# POST /poll/options – validation errors (422)
# ---------------------------------------------------------------------------


class TestPollOptionsValidationErrors:
    def test_missing_tickers_field_returns_422(self):
        response = client.post("/poll/options", json={})
        assert response.status_code == 422

    def test_empty_tickers_list_returns_422(self):
        response = client.post("/poll/options", json={"tickers": []})
        assert response.status_code == 422

    def test_tickers_not_a_list_returns_422(self):
        response = client.post("/poll/options", json={"tickers": "AAPL"})
        assert response.status_code == 422

    def test_tickers_list_of_non_strings_returns_422(self):
        response = client.post("/poll/options", json={"tickers": [123, 456]})
        assert response.status_code == 422

    def test_ticker_too_long_returns_422(self):
        long_ticker = "A" * 11
        response = client.post("/poll/options", json={"tickers": [long_ticker]})
        assert response.status_code == 422

    def test_empty_string_ticker_returns_422(self):
        response = client.post("/poll/options", json={"tickers": [""]})
        assert response.status_code == 422

    def test_none_body_returns_422(self):
        response = client.post("/poll/options", json=None)
        assert response.status_code == 422

    def test_tickers_with_spaces_returns_422(self):
        response = client.post("/poll/options", json={"tickers": ["AP PL"]})
        assert response.status_code == 422

    def test_tickers_with_special_characters_returns_422(self):
        response = client.post("/poll/options", json={"tickers": ["AAPL!", "@MSFT"]})
        assert response.status_code == 422

    def test_too_many_tickers_returns_422(self):
        tickers = [f"TK{i}" for i in range(51)]
        response = client.post("/poll/options", json={"tickers": tickers})
        assert response.status_code == 422

    def test_error_response_contains_detail(self):
        response = client.post("/poll/options", json={"tickers": []})
        data = response.json()
        assert "detail" in data


# ---------------------------------------------------------------------------
# POST /poll/options – agent invocation
# ---------------------------------------------------------------------------


class TestPollOptionsAgentInvocation:
    @patch("backend.api.poll.run_polling", side_effect=_mock_poll_success)
    def test_agent_invoked_once_per_request(self, mock_poll):
        client.post("/poll/options", json=VALID_PAYLOAD)
        mock_poll.assert_called_once()

    @patch("backend.api.poll.run_polling", side_effect=_mock_poll_success)
    def test_agent_receives_list_argument(self, mock_poll):
        client.post("/poll/options", json=VALID_PAYLOAD)
        args, _ = mock_poll.call_args
        assert isinstance(args[0], list)

    @patch("backend.api.poll.run_polling", side_effect=_mock_poll_success)
    def test_agent_receives_correct_number_of_tickers(self, mock_poll):
        client.post("/poll/options", json=VALID_PAYLOAD)
        args, _ = mock_poll.call_args
        assert len(args[0]) == len(set(t.upper() for t in VALID_PAYLOAD["tickers"]))

    @patch(
        "backend.api.poll.run_polling",
        side_effect=Exception("agent failure"),
    )
    def test_agent_exception_returns_500(self, _mock):
        response = client.post("/poll/options", json=VALID_PAYLOAD)
        assert response.status_code == 500

    @patch(
        "backend.api.poll.run_polling",
        side_effect=Exception("agent failure"),
    )
    def test_agent_exception_response_contains_detail(self, _mock):
        response = client.post("/poll/options", json=VALID_PAYLOAD)
        assert "detail" in response.json()


# ---------------------------------------------------------------------------
# POST /poll/options – content-type / method guards
# ---------------------------------------------------------------------------


class TestPollOptionsMethodAndContentType:
    def test_get_method_not_allowed(self):
        response = client.get("/poll/options")
        assert response.status_code == 405

    def test_put_method_not_allowed(self):
        response = client.put("/poll/options", json=VALID_PAYLOAD)
        assert response.status_code == 405

    def test_delete_method_not_allowed(self):
        response = client.delete("/poll/options")
        assert response.status_code == 405

    def test_plain_text_body_returns_422(self):
        response = client.post(
            "/poll/options",
            content="AAPL,MSFT",
            headers={"Content-Type": "text/plain"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Polling service unit tests (isolated)
# ---------------------------------------------------------------------------


class TestPollingService:
    def test_run_polling_returns_dict(self):
        from backend.services.polling_service import run_polling

        with patch(
            "backend.services.polling_service.invoke_options_agent",
            return_value={"AAPL": {"polled": True}},
        ):
            result = run_polling(["AAPL"])
            assert isinstance(result, dict)

    def test_run_polling_status_ok(self):
        from backend.services.polling_service import run_polling

        with patch(
            "backend.services.polling_service.invoke_options_agent",
            return_value={"AAPL": {"polled": True}},
        ):
            result = run_polling(["AAPL"])
            assert result["status"] == "ok"

    def test_run_polling_passes_tickers_to_agent(self):
        from backend.services.polling_service import run_polling

        mock_agent = MagicMock(return_value={"AAPL": {}})
        with patch(
            "backend.services.polling_service.invoke_options_agent", mock_agent
        ):
            run_polling(["AAPL", "MSFT"])
            mock_agent.assert_called_once_with(["AAPL", "MSFT"])

    def test_run_polling_includes_tickers_in_response(self):
        from backend.services.polling_service import run_polling

        with patch(
            "backend.services.polling_service.invoke_options_agent",
            return_value={"TSLA": {}},
        ):
            result = run_polling(["TSLA"])
            assert "TSLA" in result["tickers"]


# ---------------------------------------------------------------------------
# Options agent unit tests (isolated)
# ---------------------------------------------------------------------------


class TestOptionsAgent:
    def test_invoke_returns_dict(self):
        from backend.agents.options_agent import invoke_options_agent

        result = invoke_options_agent(["AAPL"])
        assert isinstance(result, dict)

    def test_invoke_keys_match_tickers(self):
        from backend.agents.options_agent import invoke_options_agent

        tickers = ["AAPL", "MSFT"]
        result = invoke_options_agent(tickers)
        for ticker in tickers:
            assert ticker in result

    def test_invoke_empty_list_returns_empty_dict(self):
        from backend.agents.options_agent import invoke_options_agent

        result = invoke_options_agent([])
        assert result == {}

    def test_invoke_single_ticker(self):
        from backend.agents.options_agent import invoke_options_agent

        result = invoke_options_agent(["TSLA"])
        assert "TSLA" in result


# ---------------------------------------------------------------------------
# Pydantic model unit tests
# ---------------------------------------------------------------------------


class TestPollRequestModel:
    def test_valid_tickers_accepted(self):
        from backend.models.poll import PollRequest

        req = PollRequest(tickers=["AAPL", "MSFT"])
        assert len(req.tickers) == 2

    def test_tickers_normalised_to_uppercase(self):
        from backend.models.poll import PollRequest

        req = PollRequest(tickers=["aapl", "msft"])
        assert all(t == t.upper() for t in req.tickers)

    def test_empty_tickers_raises_validation_error(self):
        from backend.models.poll import PollRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PollRequest(tickers=[])

    def test_ticker_too_long_raises_validation_error(self):
        from backend.models.poll import PollRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PollRequest(tickers=["A" * 11])

    def test_empty_string_ticker_raises_validation_error(self):
        from backend.models.poll import PollRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PollRequest(tickers=[""])

    def test_duplicate_tickers_deduplicated(self):
        from backend.models.poll import PollRequest

        req = PollRequest(tickers=["AAPL", "AAPL", "MSFT"])
        assert req.tickers.count("AAPL") == 1

    def test_ticker_with_special_chars_raises_validation_error(self):
        from backend.models.poll import PollRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PollRequest(tickers=["AAPL!"])

    def test_ticker_with_space_raises_validation_error(self):
        from backend.models.poll import PollRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PollRequest(tickers=["AA PL"])

    def test_too_many_tickers_raises_validation_error(self):
        from backend.models.poll import PollRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PollRequest(tickers=[f"TK{i}" for i in range(51)])


class TestPollResponseModel:
    def test_valid_response_constructed(self):
        from backend.models.poll import PollResponse

        resp = PollResponse(
            status="ok",
            tickers=["AAPL"],
            results={"AAPL": {"polled": True}},
        )
        assert resp.status == "ok"

    def test_response_serialises_to_dict(self):
        from backend.models.poll import PollResponse

        resp = PollResponse(
            status="ok",
            tickers=["AAPL"],
            results={"AAPL": {}},
        )
        data = resp.model_dump()
        assert "status" in data
        assert "tickers" in data
        assert "results" in data