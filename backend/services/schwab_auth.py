import logging
import os
from typing import Optional

import httpx
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from backend import config

logger = logging.getLogger(__name__)


class SchwabAuth:
    """Wraps Schwab OAuth credential resolution and token fetching."""

    default_secret_path = None  # reserved for future use

    def __init__(
        self,
        vault_url: Optional[str] = None,
        vault_token: Optional[str] = None,
        secret_path: Optional[str] = None,
        vault_mount: Optional[str] = None,
    ) -> None:
        self.vault_url = vault_url
        self.vault_token = vault_token
        self.secret_path = secret_path
        self.vault_mount = vault_mount

    def get_credentials(self) -> dict:
        """Resolve and return Schwab client credentials as a dict."""
        client_id, client_secret = _resolve_client_credentials(self.vault_url)
        return {"client_id": client_id, "client_secret": client_secret}

    def get_access_token(self) -> str:
        """Fetch an OAuth2 client_credentials token from Schwab."""
        return get_access_token(vault_url=self.vault_url)


def _get_secret(vault_url: str, secret_name: str) -> str:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    secret = client.get_secret(secret_name)
    return secret.value


def _resolve_client_credentials(vault_url: Optional[str]) -> tuple[str, str]:
    """Resolve Schwab client_id and client_secret from env vars or Key Vault.

    Env vars take precedence so that local development and CI work without
    a live Azure Key Vault.  Falls back to Key Vault when the env vars are
    absent.
    """
    env_client_id = os.environ.get("SCHWAB_CLIENT_ID")
    env_client_secret = os.environ.get("SCHWAB_CLIENT_SECRET")

    if env_client_id and env_client_secret:
        logger.debug("Using Schwab credentials from environment variables")
        return env_client_id, env_client_secret

    url = vault_url or config.SCHWAB_KEY_VAULT_URL
    if not url:
        raise ValueError(
            "Schwab credentials not found in environment variables and "
            "SCHWAB_KEY_VAULT_URL is not configured."
        )

    logger.debug("Fetching Schwab credentials from Key Vault: %s", url)
    client_id = _get_secret(url, config.SCHWAB_CLIENT_ID_SECRET)
    client_secret = _get_secret(url, config.SCHWAB_CLIENT_SECRET_SECRET)
    return client_id, client_secret


def get_access_token(vault_url: Optional[str] = None) -> str:
    """Fetch an OAuth2 client_credentials token from Schwab.

    Credentials are resolved first from the ``SCHWAB_CLIENT_ID`` /
    ``SCHWAB_CLIENT_SECRET`` environment variables and, when those are absent,
    from Azure Key Vault.
    """
    client_id, client_secret = _resolve_client_credentials(vault_url)

    logger.info("Requesting Schwab OAuth token")
    response = httpx.post(
        config.SCHWAB_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        timeout=10,
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    logger.info("Schwab OAuth token obtained successfully")
    return token
