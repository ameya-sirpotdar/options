import logging
from typing import Optional

import httpx
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from backend import config

logger = logging.getLogger(__name__)


def _get_secret(vault_url: str, secret_name: str) -> str:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    secret = client.get_secret(secret_name)
    return secret.value


def get_access_token(vault_url: Optional[str] = None) -> str:
    """Fetch an OAuth2 client_credentials token from Schwab using credentials stored in Key Vault."""
    url = vault_url or config.SCHWAB_KEY_VAULT_URL
    client_id = _get_secret(url, config.SCHWAB_CLIENT_ID_SECRET)
    client_secret = _get_secret(url, config.SCHWAB_CLIENT_SECRET_SECRET)

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
