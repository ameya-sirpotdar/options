from typing import Any, Dict, Optional

from backend.services.schwab_auth import get_access_token
from backend.services.schwab_market_data import fetch_options_chain


class SchwabClient:
    """Thin wrapper that combines auth + options chain fetch into a single callable."""

    def __init__(self, auth=None, vault_url: Optional[str] = None):
        self._auth = auth
        self._vault_url = vault_url
        self._token: str = ""

    def _ensure_token(self) -> None:
        if not self._token:
            if self._auth is not None:
                self._token = self._auth.get_access_token()
            else:
                self._token = get_access_token(vault_url=self._vault_url)

    async def get_option_chain(self, ticker: str) -> Dict[str, Any]:
        self._ensure_token()
        return fetch_options_chain(ticker, self._token)
