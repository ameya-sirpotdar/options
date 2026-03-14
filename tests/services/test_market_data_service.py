from unittest.mock import patch, MagicMock

from backend.services.schwab_service import SchwabService


@patch.object(SchwabService, "filter_contracts")
@patch.object(SchwabService, "fetch_options_chain")
@patch.object(SchwabService, "get_access_token")
def test_get_filtered_options_returns_per_ticker(mock_token, mock_fetch, mock_filter):
    mock_token.return_value = "tok"
    mock_fetch.return_value = {"putExpDateMap": {}}
    mock_filter.return_value = [{"strike": 820.0}]

    service = SchwabService()
    result = service.get_filtered_options(["NVDA", "AAPL"])

    assert "NVDA" in result
    assert "AAPL" in result
    assert result["NVDA"] == [{"strike": 820.0}]


@patch.object(SchwabService, "filter_contracts")
@patch.object(SchwabService, "fetch_options_chain")
@patch.object(SchwabService, "get_access_token")
def test_get_filtered_options_calls_token_once(mock_token, mock_fetch, mock_filter):
    mock_token.return_value = "tok"
    mock_fetch.return_value = {}
    mock_filter.return_value = []

    service = SchwabService()
    service.get_filtered_options(["NVDA", "AAPL", "MSFT"])

    mock_token.assert_called_once()


@patch.object(SchwabService, "filter_contracts")
@patch.object(SchwabService, "fetch_options_chain")
@patch.object(SchwabService, "get_access_token")
def test_get_filtered_options_empty_on_fetch_error(mock_token, mock_fetch, mock_filter):
    mock_token.return_value = "tok"
    mock_fetch.side_effect = Exception("network error")

    service = SchwabService()
    result = service.get_filtered_options(["NVDA"])

    assert result["NVDA"] == []


@patch.object(SchwabService, "filter_contracts")
@patch.object(SchwabService, "fetch_options_chain")
@patch.object(SchwabService, "get_access_token")
def test_get_filtered_options_continues_after_single_ticker_error(mock_token, mock_fetch, mock_filter):
    mock_token.return_value = "tok"
    mock_fetch.side_effect = [Exception("fail"), MagicMock()]
    mock_filter.return_value = [{"strike": 100.0}]

    service = SchwabService()
    result = service.get_filtered_options(["NVDA", "AAPL"])

    assert result["NVDA"] == []
    assert result["AAPL"] == [{"strike": 100.0}]
