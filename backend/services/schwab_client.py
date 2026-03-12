import logging
from typing import Any, Dict, Optional

import httpx

from backend.services.schwab_auth import get_access_token
from backend.services.schwab_market_data import fetch_options_chain

logger = logging.getLogger(__name__)


class SchwabClient:
    """Thin wrapper that combines auth + options chain fetch into a single callable."""

    def __init__(self, auth=None, vault_url: Optional[str] = None):
        self._auth = auth
        self._vault_url = vault_url
        self._token: str = ""

    def _refresh_token(self) -> None:
        if self._auth is not None:
            self._token = self._auth.get_access_token()
        else:
            self._token = get_access_token(vault_url=self._vault_url)

    def _ensure_token(self) -> None:
        if not self._token:
            self._refresh_token()

    async def get_option_chain(
        self,
        ticker: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._ensure_token()
        try:
            return fetch_options_chain(ticker, self._token, from_date=from_date, to_date=to_date)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                logger.info("Schwab token expired, refreshing")
                self._refresh_token()
                return fetch_options_chain(ticker, self._token, from_date=from_date, to_date=to_date)
            raise
