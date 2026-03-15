backend/services/schwab_service.py
import base64
import httpx
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Auth helpers (formerly schwab_auth.py)
# ---------------------------------------------------------------------------

SCHWAB_TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"


def _basic_auth_header(client_id: str, client_secret: str) -> str:
    credentials = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    """Exchange a refresh token for a new access token."""
    headers = {
        "Authorization": _basic_auth_header(client_id, client_secret),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    response = httpx.post(SCHWAB_TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


# ---------------------------------------------------------------------------
# Market data helpers (formerly schwab_market_data.py)
# ---------------------------------------------------------------------------

SCHWAB_MARKET_DATA_BASE = "https://api.schwabapi.com/marketdata/v1"


def get_options_chain(
    access_token: str,
    symbol: str,
    contract_type: str = "ALL",
    strike_count: int = 10,
    include_underlying_quote: bool = True,
    strategy: str = "SINGLE",
    interval: float | None = None,
    strike: float | None = None,
    range_: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    volatility: float | None = None,
    underlying_price: float | None = None,
    interest_rate: float | None = None,
    days_to_expiration: int | None = None,
    exp_month: str | None = None,
    option_type: str | None = None,
    entitlement: str | None = None,
) -> dict[str, Any]:
    """Fetch the options chain for a given symbol from Schwab."""
    headers = {"Authorization": f"Bearer {access_token}"}
    params: dict[str, Any] = {
        "symbol": symbol,
        "contractType": contract_type,
        "strikeCount": strike_count,
        "includeUnderlyingQuote": str(include_underlying_quote).lower(),
        "strategy": strategy,
    }
    optional = {
        "interval": interval,
        "strike": strike,
        "range": range_,
        "fromDate": from_date,
        "toDate": to_date,
        "volatility": volatility,
        "underlyingPrice": underlying_price,
        "interestRate": interest_rate,
        "daysToExpiration": days_to_expiration,
        "expMonth": exp_month,
        "optionType": option_type,
        "entitlement": entitlement,
    }
    for key, value in optional.items():
        if value is not None:
            params[key] = value

    url = f"{SCHWAB_MARKET_DATA_BASE}/chains"
    response = httpx.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def get_quote(access_token: str, symbol: str) -> dict[str, Any]:
    """Fetch a real-time quote for a symbol."""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{SCHWAB_MARKET_DATA_BASE}/{symbol}/quotes"
    response = httpx.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Filters (formerly schwab_filters.py)
# ---------------------------------------------------------------------------


def filter_options_by_delta(
    options: list[dict[str, Any]],
    min_delta: float,
    max_delta: float,
) -> list[dict[str, Any]]:
    """Return options whose absolute delta falls within [min_delta, max_delta]."""
    result = []
    for opt in options:
        delta = opt.get("delta")
        if delta is None:
            continue
        if min_delta <= abs(delta) <= max_delta:
            result.append(opt)
    return result


def filter_options_by_dte(
    options: list[dict[str, Any]],
    min_dte: int,
    max_dte: int,
) -> list[dict[str, Any]]:
    """Return options whose days-to-expiration falls within [min_dte, max_dte]."""
    result = []
    for opt in options:
        dte = opt.get("daysToExpiration")
        if dte is None:
            continue
        if min_dte <= dte <= max_dte:
            result.append(opt)
    return result


def filter_options_by_open_interest(
    options: list[dict[str, Any]],
    min_open_interest: int,
) -> list[dict[str, Any]]:
    """Return options with open interest >= min_open_interest."""
    result = []
    for opt in options:
        oi = opt.get("openInterest")
        if oi is None:
            continue
        if oi >= min_open_interest:
            result.append(opt)
    return result


def filter_options_by_volume(
    options: list[dict[str, Any]],
    min_volume: int,
) -> list[dict[str, Any]]:
    """Return options with volume >= min_volume."""
    result = []
    for opt in options:
        volume = opt.get("totalVolume")
        if volume is None:
            continue
        if volume >= min_volume:
            result.append(opt)
    return result


def filter_options_by_bid_ask_spread(
    options: list[dict[str, Any]],
    max_spread: float,
) -> list[dict[str, Any]]:
    """Return options whose bid-ask spread <= max_spread."""
    result = []
    for opt in options:
        bid = opt.get("bid")
        ask = opt.get("ask")
        if bid is None or ask is None:
            continue
        spread = ask - bid
        if spread <= max_spread:
            result.append(opt)
    return result


# ---------------------------------------------------------------------------
# CCP Calculator (formerly ccp_calculator.py)
# ---------------------------------------------------------------------------


def calculate_ccp(
    option: dict[str, Any],
    underlying_price: float,
) -> float | None:
    """
    Calculate the Capital-at-risk / Credit-received Percentage (CCP).

    CCP = credit_received / capital_at_risk * 100

    For a short put:
        credit_received  = bid price (premium collected)
        capital_at_risk  = strike - credit_received

    Returns None when the calculation is not possible.
    """
    strike = option.get("strikePrice")
    bid = option.get("bid")
    if strike is None or bid is None:
        return None
    if bid <= 0:
        return None
    capital_at_risk = strike - bid
    if capital_at_risk <= 0:
        return None
    return round((bid / capital_at_risk) * 100, 4)


def calculate_annualised_ccp(
    option: dict[str, Any],
    underlying_price: float,
) -> float | None:
    """
    Annualise the CCP based on days-to-expiration.

    annualised_ccp = ccp / dte * 365
    """
    ccp = calculate_ccp(option, underlying_price)
    if ccp is None:
        return None
    dte = option.get("daysToExpiration")
    if not dte or dte <= 0:
        return None
    return round(ccp / dte * 365, 4)


# ---------------------------------------------------------------------------
# SchwabService class (formerly market_data_service.py)
# ---------------------------------------------------------------------------


class SchwabService:
    """
    High-level service that wraps Schwab API authentication and market data
    retrieval.  Handles token refresh automatically.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        self.client_id = client_id or os.environ.get("SCHWAB_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("SCHWAB_CLIENT_SECRET", "")
        self.refresh_token = refresh_token or os.environ.get("SCHWAB_REFRESH_TOKEN", "")
        self._access_token: str | None = None
        self._token_expiry: float = 0.0

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _is_token_valid(self) -> bool:
        return self._access_token is not None and time.time() < self._token_expiry

    def _refresh_access_token(self) -> None:
        logger.debug("Refreshing Schwab access token.")
        self._access_token = get_access_token(
            self.client_id, self.client_secret, self.refresh_token
        )
        # Schwab access tokens are valid for 30 minutes; refresh after 25.
        self._token_expiry = time.time() + 25 * 60

    def _ensure_token(self) -> str:
        if not self._is_token_valid():
            self._refresh_access_token()
        assert self._access_token is not None
        return self._access_token

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_options_chain(
        self,
        symbol: str,
        contract_type: str = "ALL",
        strike_count: int = 10,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Fetch the options chain for *symbol*."""
        token = self._ensure_token()
        return get_options_chain(
            access_token=token,
            symbol=symbol,
            contract_type=contract_type,
            strike_count=strike_count,
            **kwargs,
        )

    def fetch_quote(self, symbol: str) -> dict[str, Any]:
        """Fetch a real-time quote for *symbol*."""
        token = self._ensure_token()
        return get_quote(access_token=token, symbol=symbol)

    def fetch_filtered_options(
        self,
        symbol: str,
        contract_type: str = "PUT",
        strike_count: int = 20,
        min_delta: float = 0.1,
        max_delta: float = 0.4,
        min_dte: int = 7,
        max_dte: int = 60,
        min_open_interest: int = 100,
        min_volume: int = 10,
        max_bid_ask_spread: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Fetch options chain and apply standard filters, returning a flat list
        of option contracts that pass all filters.
        """
        chain = self.fetch_options_chain(
            symbol=symbol,
            contract_type=contract_type,
            strike_count=strike_count,
        )

        options = _flatten_options_chain(chain, contract_type)

        options = filter_options_by_delta(options, min_delta, max_delta)
        options = filter_options_by_dte(options, min_dte, max_dte)
        options = filter_options_by_open_interest(options, min_open_interest)
        options = filter_options_by_volume(options, min_volume)
        options = filter_options_by_bid_ask_spread(options, max_bid_ask_spread)

        return options

    def enrich_with_ccp(
        self,
        options: list[dict[str, Any]],
        underlying_price: float,
    ) -> list[dict[str, Any]]:
        """Add *ccp* and *annualisedCcp* fields to each option dict."""
        enriched = []
        for opt in options:
            opt = dict(opt)
            opt["ccp"] = calculate_ccp(opt, underlying_price)
            opt["annualisedCcp"] = calculate_annualised_ccp(opt, underlying_price)
            enriched.append(opt)
        return enriched


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _flatten_options_chain(
    chain: dict[str, Any],
    contract_type: str,
) -> list[dict[str, Any]]:
    """
    Flatten the nested Schwab options chain response into a list of individual
    option contract dicts.

    The Schwab response has the structure:
        {
          "putExpDateMap": {
            "2024-01-19:30": {
              "150.0": [ { ...contract... } ],
              ...
            },
            ...
          },
          "callExpDateMap": { ... }
        }
    """
    result: list[dict[str, Any]] = []

    maps_to_process: list[str] = []
    ct = contract_type.upper()
    if ct in ("PUT", "ALL"):
        maps_to_process.append("putExpDateMap")
    if ct in ("CALL", "ALL"):
        maps_to_process.append("callExpDateMap")

    for map_key in maps_to_process:
        exp_date_map = chain.get(map_key, {})
        for exp_date_str, strikes in exp_date_map.items():
            for strike_str, contracts in strikes.items():
                for contract in contracts:
                    contract = dict(contract)
                    # Ensure expiration date and strike are present on the contract.
                    if "expirationDate" not in contract:
                        contract["expirationDate"] = exp_date_str.split(":")[0]
                    if "strikePrice" not in contract:
                        try:
                            contract["strikePrice"] = float(strike_str)
                        except ValueError:
                            pass
                    result.append(contract)

    return result