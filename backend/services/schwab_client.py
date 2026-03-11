from typing import Any, Dict

from backend.services.schwab_auth import get_access_token
from backend.services.schwab_market_data import fetch_options_chain


class SchwabClient:
    """Thin wrapper that combines auth + options chain fetch into a single callable."""

    def __init__(self, vault_url: str | None = None):
        self._vault_url = vault_url
        self._token: str = ""

    def _ensure_token(self) -> None:
        if not self._token:
            self._token = get_access_token(vault_url=self._vault_url)

    def get_options_chain(self, ticker: str) -> Dict[str, Any]:
        self._ensure_token()
        return fetch_options_chain(ticker, self._token)
