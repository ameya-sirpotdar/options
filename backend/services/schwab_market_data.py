import logging
from typing import Any, Dict

import httpx

from backend import config

logger = logging.getLogger(__name__)


def fetch_options_chain(ticker: str, access_token: str) -> Dict[str, Any]:
    """Fetch the options chain for a single ticker from the Schwab /marketdata/chains endpoint."""
    logger.info("Fetching options chain for ticker=%s", ticker)
    response = httpx.get(
        config.SCHWAB_CHAINS_URL,
        params={"symbol": ticker, "contractType": "PUT"},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    logger.info("Options chain fetched for ticker=%s", ticker)
    return data
