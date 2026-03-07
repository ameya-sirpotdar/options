import logging
from typing import Any, Dict, List

from backend.services.schwab_auth import get_access_token
from backend.services.schwab_market_data import fetch_options_chain
from backend.services.schwab_filters import filter_contracts

logger = logging.getLogger(__name__)


def get_filtered_options(tickers: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    For each ticker: authenticate, fetch the options chain, and return filtered contracts.
    Returns a dict mapping ticker → list of filtered put contracts.
    """
    token = get_access_token()
    results: Dict[str, List[Dict[str, Any]]] = {}
    for ticker in tickers:
        try:
            chain = fetch_options_chain(ticker, token)
            results[ticker] = filter_contracts(chain)
        except Exception as exc:
            logger.error("Failed to fetch/filter options for ticker=%s: %s", ticker, exc)
            results[ticker] = []
    return results
