import logging
from typing import Any, Dict, Optional

import httpx

from backend import config

logger = logging.getLogger(__name__)


def _fetch_single_contract_type(
    ticker: str,
    access_token: str,
    contract_type: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    strike_count: int = 30,
) -> Dict[str, Any]:
    """Fetch one contract type (PUT or CALL) to avoid Schwab 502 body overflow."""
    params: Dict[str, Any] = {
        "symbol": ticker.upper(),
        "contractType": contract_type,
        "strikeCount": strike_count,
    }
    if from_date:
        params["fromDate"] = from_date
    if to_date:
        params["toDate"] = to_date
    response = httpx.get(
        config.SCHWAB_CHAINS_URL,
        params=params,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def fetch_options_chain(
    ticker: str,
    access_token: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch the options chain for a single ticker from the Schwab /marketdata/chains endpoint.

    Fetches PUTs and CALLs separately to avoid Schwab's 502 "Body buffer overflow"
    error that occurs when contractType=ALL returns too much data.
    """
    logger.info("Fetching options chain for ticker=%s", ticker.upper())
    calls = _fetch_single_contract_type(
        ticker, access_token, "CALL", from_date=from_date, to_date=to_date
    )
    puts = _fetch_single_contract_type(
        ticker, access_token, "PUT", from_date=from_date, to_date=to_date
    )

    # Merge: use calls as the base, add putExpDateMap from puts
    merged = calls.copy()
    merged["putExpDateMap"] = puts.get("putExpDateMap", {})
    logger.info("Options chain fetched for ticker=%s", ticker.upper())
    return merged
