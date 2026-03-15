from unittest.mock import MagicMock, patch

import pytest

from backend.services.schwab_service import fetch_options_chain


@patch("backend.services.schwab_service.httpx.get")
def test_fetch_options_chain_returns_json(mock_get):
    mock_get.return_value = MagicMock(json=lambda: {"symbol": "AAPL", "putExpDateMap": {}})
    result = fetch_options_chain("AAPL", "token123")
    assert result["symbol"] == "AAPL"


@patch("backend.services.schwab_service.httpx.get")
def test_fetch_options_chain_sends_bearer_auth(mock_get):
    mock_get.return_value = MagicMock(json=lambda: {})
    fetch_options_chain("NVDA", "mytoken")
    _, kwargs = mock_get.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer mytoken"


@patch("backend.services.schwab_service.httpx.get")
def test_fetch_options_chain_sends_put_contract_type(mock_get):
    mock_get.return_value = MagicMock(json=lambda: {})
    fetch_options_chain("MSFT", "tok")
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["contractType"] == "PUT"


@patch("backend.services.schwab_service.httpx.get")
def test_fetch_options_chain_raises_on_http_error(mock_get):
    mock_get.return_value = MagicMock()
    mock_get.return_value.raise_for_status.side_effect = Exception("404 Not Found")
    with pytest.raises(Exception, match="404"):
        fetch_options_chain("FAKE", "tok")
