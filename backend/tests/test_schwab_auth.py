import os
import pytest
from unittest.mock import MagicMock, patch

from backend.services.schwab_auth import SchwabAuth, _resolve_client_credentials


class TestSchwabAuthEnvVarFallback:
    """Tests for credential resolution in SchwabAuth."""

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
            os.environ.pop("SCHWAB_CLIENT_ID", None)
            os.environ.pop("SCHWAB_CLIENT_SECRET", None)
            os.environ.pop("KEY_VAULT_URL", None)

            auth = SchwabAuth(vault_url=None)

            with pytest.raises((ValueError, Exception)):
                auth.get_credentials()

    def test_raises_when_no_vault_and_missing_client_secret(self):
        env_vars = {"SCHWAB_CLIENT_ID": "only_id"}
        with patch.dict(os.environ, env_vars, clear=True):
            os.environ.pop("SCHWAB_CLIENT_SECRET", None)
            os.environ.pop("KEY_VAULT_URL", None)

            auth = SchwabAuth(vault_url=None)

            with pytest.raises((ValueError, Exception)):
                auth.get_credentials()

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

    def test_loads_credentials_from_azure_keyvault_when_vault_url_provided(self):
        mock_secret = MagicMock()
        mock_secret.value = "vault_value"

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SCHWAB_CLIENT_ID", None)
            os.environ.pop("SCHWAB_CLIENT_SECRET", None)

            with patch("backend.services.schwab_auth.SecretClient") as mock_sc_cls, \
                 patch("backend.services.schwab_auth.DefaultAzureCredential"):
                mock_sc_instance = MagicMock()
                mock_sc_cls.return_value = mock_sc_instance
                mock_sc_instance.get_secret.return_value = mock_secret

                auth = SchwabAuth(vault_url="https://myvault.vault.azure.net/")
                creds = auth.get_credentials()

        assert creds["client_id"] == "vault_value"
        assert creds["client_secret"] == "vault_value"

    def test_vault_client_initialized_with_correct_url(self):
        mock_secret = MagicMock()
        mock_secret.value = "vault_value"

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SCHWAB_CLIENT_ID", None)
            os.environ.pop("SCHWAB_CLIENT_SECRET", None)

            with patch("backend.services.schwab_auth.SecretClient") as mock_sc_cls, \
                 patch("backend.services.schwab_auth.DefaultAzureCredential"):
                mock_sc_instance = MagicMock()
                mock_sc_cls.return_value = mock_sc_instance
                mock_sc_instance.get_secret.return_value = mock_secret

                auth = SchwabAuth(vault_url="https://myvault.vault.azure.net/")
                auth.get_credentials()

        assert mock_sc_cls.call_args.kwargs.get("vault_url") == "https://myvault.vault.azure.net/" \
            or mock_sc_cls.call_args.args[0] == "https://myvault.vault.azure.net/"

    def test_vault_error_propagates_as_exception(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SCHWAB_CLIENT_ID", None)
            os.environ.pop("SCHWAB_CLIENT_SECRET", None)

            with patch("backend.services.schwab_auth.SecretClient") as mock_sc_cls, \
                 patch("backend.services.schwab_auth.DefaultAzureCredential"):
                mock_sc_instance = MagicMock()
                mock_sc_cls.return_value = mock_sc_instance
                mock_sc_instance.get_secret.side_effect = Exception("Vault connection refused")

                auth = SchwabAuth(vault_url="https://myvault.vault.azure.net/")

                with pytest.raises(Exception, match="Vault connection refused"):
                    auth.get_credentials()

    def test_env_var_path_does_not_call_azure_keyvault(self):
        env_vars = {
            "SCHWAB_CLIENT_ID": "env_id",
            "SCHWAB_CLIENT_SECRET": "env_secret",
        }
        with patch("backend.services.schwab_auth.SecretClient") as mock_sc_cls, \
             patch.dict(os.environ, env_vars):
            auth = SchwabAuth(vault_url=None)
            auth.get_credentials()

        mock_sc_cls.assert_not_called()

    def test_vault_secret_path_is_configurable(self):
        mock_secret = MagicMock()
        mock_secret.value = "vault_value"

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SCHWAB_CLIENT_ID", None)
            os.environ.pop("SCHWAB_CLIENT_SECRET", None)

            with patch("backend.services.schwab_auth.SecretClient") as mock_sc_cls, \
                 patch("backend.services.schwab_auth.DefaultAzureCredential"):
                mock_sc_instance = MagicMock()
                mock_sc_cls.return_value = mock_sc_instance
                mock_sc_instance.get_secret.return_value = mock_secret

                auth = SchwabAuth(
                    vault_url="https://myvault.vault.azure.net/",
                    secret_path="custom/path",
                )
                auth.get_credentials()

        assert mock_sc_instance.get_secret.called

    def test_default_secret_path_is_used_when_not_specified(self):
        mock_secret = MagicMock()
        mock_secret.value = "vault_value"

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SCHWAB_CLIENT_ID", None)
            os.environ.pop("SCHWAB_CLIENT_SECRET", None)

            with patch("backend.services.schwab_auth.SecretClient") as mock_sc_cls, \
                 patch("backend.services.schwab_auth.DefaultAzureCredential"):
                mock_sc_instance = MagicMock()
                mock_sc_cls.return_value = mock_sc_instance
                mock_sc_instance.get_secret.return_value = mock_secret

                auth = SchwabAuth(vault_url="https://myvault.vault.azure.net/")
                auth.get_credentials()

        assert mock_sc_instance.get_secret.called
