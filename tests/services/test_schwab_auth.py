from unittest.mock import MagicMock, patch

import pytest

from backend.services.schwab_service import get_access_token


def _mock_secret_client(secrets: dict):
    client = MagicMock()
    client.get_secret.side_effect = lambda name: MagicMock(value=secrets[name])
    return client


@patch("backend.services.schwab_service.httpx.post")
@patch("backend.services.schwab_service.SecretClient")
@patch("backend.services.schwab_service.DefaultAzureCredential")
def test_get_access_token_returns_token(mock_cred, mock_sc, mock_post):
    mock_sc.return_value = _mock_secret_client({
        "schwab-client-id": "test-id",
        "schwab-client-secret": "test-secret",
    })
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {"access_token": "tok123"})

    token = get_access_token(vault_url="https://fake.vault.azure.net")

    assert token == "tok123"


@patch("backend.services.schwab_service.httpx.post")
@patch("backend.services.schwab_service.SecretClient")
@patch("backend.services.schwab_service.DefaultAzureCredential")
def test_get_access_token_calls_token_url(mock_cred, mock_sc, mock_post):
    mock_sc.return_value = _mock_secret_client({
        "schwab-client-id": "id",
        "schwab-client-secret": "secret",
    })
    mock_post.return_value = MagicMock(json=lambda: {"access_token": "t"})

    get_access_token(vault_url="https://fake.vault.azure.net")

    args, kwargs = mock_post.call_args
    assert "schwabapi.com" in args[0]


@patch("backend.services.schwab_service.httpx.post")
@patch("backend.services.schwab_service.SecretClient")
@patch("backend.services.schwab_service.DefaultAzureCredential")
def test_get_access_token_raises_on_http_error(mock_cred, mock_sc, mock_post):
    mock_sc.return_value = _mock_secret_client({
        "schwab-client-id": "id",
        "schwab-client-secret": "secret",
    })
    mock_post.return_value = MagicMock()
    mock_post.return_value.raise_for_status.side_effect = Exception("401 Unauthorized")

    with pytest.raises(Exception, match="401"):
        get_access_token(vault_url="https://fake.vault.azure.net")
