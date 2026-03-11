import pytest
from unittest.mock import patch, MagicMock
import os

from backend.services.schwab_auth import SchwabAuth



class TestSchwabAuthEnvVarFallback:
    """Tests for env-var credential fallback in SchwabAuth."""

    def test_loads_credentials_from_vault_when_vault_url_provided(self):
        mock_secret = {
            "client_id": "vault_client_id",
            "client_secret": "vault_client_secret",
        }
        with patch("backend.services.schwab_auth.hvac.Client") as mock_hvac:
            mock_client = MagicMock()
            mock_hvac.return_value = mock_client
            mock_client.secrets.kv.v2.read_secret_version.return_value = {
                "data": {"data": mock_secret}
            }

            auth = SchwabAuth(vault_url="http://vault:8200", vault_token="test-token")
            creds = auth.get_credentials()

        assert creds["client_id"] == "vault_client_id"
        assert creds["client_secret"] == "vault_client_secret"

    def test_falls_back_to_env_vars_when_no_vault_url(self):
        env_vars = {
            "SCHWAB_CLIENT_ID": "env_client_id",
            "SCHWAB_CLIENT_SECRET": "env_client_secret",
        }
        with patch.dict(os.environ, env_vars):
            auth = SchwabAuth(vault_url=None)
            creds = auth.get_credentials()

        assert creds["client_id"] == "env_client_id"
        assert creds["client_secret"] == "env_client_secret"

    def test_falls_back_to_env_vars_when_vault_url_is_empty_string(self):
        env_vars = {
            "SCHWAB_CLIENT_ID": "env_client_id_2",
            "SCHWAB_CLIENT_SECRET": "env_client_secret_2",
        }
        with patch.dict(os.environ, env_vars):
            auth = SchwabAuth(vault_url="")
            creds = auth.get_credentials()

        assert creds["client_id"] == "env_client_id_2"
        assert creds["client_secret"] == "env_client_secret_2"

    def test_raises_when_no_vault_and_missing_env_vars(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove Schwab env vars if present
            os.environ.pop("SCHWAB_CLIENT_ID", None)
            os.environ.pop("SCHWAB_CLIENT_SECRET", None)

            auth = SchwabAuth(vault_url=None)

            with pytest.raises(EnvironmentError, match="SCHWAB_CLIENT_ID"):
                auth.get_credentials()

    def test_raises_when_no_vault_and_missing_client_secret(self):
        env_vars = {
            "SCHWAB_CLIENT_ID": "only_id",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            os.environ.pop("SCHWAB_CLIENT_SECRET", None)

            auth = SchwabAuth(vault_url=None)

            with pytest.raises(EnvironmentError, match="SCHWAB_CLIENT_SECRET"):
                auth.get_credentials()

    def test_vault_client_initialized_with_correct_url_and_token(self):
        mock_secret = {
            "client_id": "vault_client_id",
            "client_secret": "vault_client_secret",
        }
        with patch("backend.services.schwab_auth.hvac.Client") as mock_hvac:
            mock_client = MagicMock()
            mock_hvac.return_value = mock_client
            mock_client.secrets.kv.v2.read_secret_version.return_value = {
                "data": {"data": mock_secret}
            }

            auth = SchwabAuth(vault_url="http://vault:8200", vault_token="my-token")
            auth.get_credentials()

            mock_hvac.assert_called_once_with(
                url="http://vault:8200", token="my-token"
            )

    def test_vault_secret_path_is_configurable(self):
        mock_secret = {
            "client_id": "vault_client_id",
            "client_secret": "vault_client_secret",
        }
        with patch("backend.services.schwab_auth.hvac.Client") as mock_hvac:
            mock_client = MagicMock()
            mock_hvac.return_value = mock_client
            mock_client.secrets.kv.v2.read_secret_version.return_value = {
                "data": {"data": mock_secret}
            }

            auth = SchwabAuth(
                vault_url="http://vault:8200",
                vault_token="my-token",
                secret_path="custom/secret/path",
            )
            auth.get_credentials()

            mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
                path="custom/secret/path", mount_point=auth.vault_mount
            )

    def test_default_secret_path_is_used_when_not_specified(self):
        mock_secret = {
            "client_id": "vault_client_id",
            "client_secret": "vault_client_secret",
        }
        with patch("backend.services.schwab_auth.hvac.Client") as mock_hvac:
            mock_client = MagicMock()
            mock_hvac.return_value = mock_client
            mock_client.secrets.kv.v2.read_secret_version.return_value = {
                "data": {"data": mock_secret}
            }

            auth = SchwabAuth(vault_url="http://vault:8200", vault_token="my-token")
            auth.get_credentials()

            mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
                path=auth.default_secret_path, mount_point=auth.vault_mount
            )

    def test_get_credentials_returns_dict_with_expected_keys(self):
        env_vars = {
            "SCHWAB_CLIENT_ID": "test_id",
            "SCHWAB_CLIENT_SECRET": "test_secret",
        }
        with patch.dict(os.environ, env_vars):
            auth = SchwabAuth(vault_url=None)
            creds = auth.get_credentials()

        assert isinstance(creds, dict)
        assert "client_id" in creds
        assert "client_secret" in creds

    def test_vault_error_propagates_as_exception(self):
        with patch("backend.services.schwab_auth.hvac.Client") as mock_hvac:
            mock_client = MagicMock()
            mock_hvac.return_value = mock_client
            mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
                "Vault connection refused"
            )

            auth = SchwabAuth(vault_url="http://vault:8200", vault_token="bad-token")

            with pytest.raises(Exception, match="Vault connection refused"):
                auth.get_credentials()

    def test_env_var_fallback_does_not_call_vault(self):
        env_vars = {
            "SCHWAB_CLIENT_ID": "env_id",
            "SCHWAB_CLIENT_SECRET": "env_secret",
        }
        with patch("backend.services.schwab_auth.hvac.Client") as mock_hvac:
            with patch.dict(os.environ, env_vars):
                auth = SchwabAuth(vault_url=None)
                auth.get_credentials()

            mock_hvac.assert_not_called()