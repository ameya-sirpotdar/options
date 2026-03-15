import base64
import httpx
import logging
import os
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from backend import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Auth helpers (formerly schwab_auth.py)
# ---------------------------------------------------------------------------

SCHWAB_TOKEN_URL = config.SCHWAB_TOKEN_URL


def _basic_auth_header(client_id: str, client_secret: str) -> str:
    credentials = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def _get_secret(vault_url: str, secret_name: str) -> str:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    secret = client.get_secret(secret_name)
    return secret.value


def _resolve_client_credentials(vault_url: Optional[str]) -> tuple[str, str]:
    """Resolve Schwab client_id and client_secret from env vars or Key Vault."""
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
    """Fetch an OAuth2 client_credentials token from Schwab."""
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


class SchwabAuth:
    """Wraps Schwab OAuth credential resolution and token fetching."""

    default_secret_path = None

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


# ---------------------------------------------------------------------------
# Market data helpers (formerly schwab_market_data.py)
# ---------------------------------------------------------------------------

SCHWAB_MARKET_DATA_BASE = "https://api.schwabapi.com/marketdata/v1"


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
    """Fetch the options chain for a single ticker from the Schwab /marketdata/chains endpoint."""
    logger.info("Fetching options chain for ticker=%s", ticker.upper())
    calls = _fetch_single_contract_type(
        ticker, access_token, "CALL", from_date=from_date, to_date=to_date
    )
    puts = _fetch_single_contract_type(
        ticker, access_token, "PUT", from_date=from_date, to_date=to_date
    )
    merged = calls.copy()
    merged["putExpDateMap"] = puts.get("putExpDateMap", {})
    logger.info("Options chain fetched for ticker=%s", ticker.upper())
    return merged


def get_options_chain(
    access_token: str,
    symbol: str,
    contract_type: str = "ALL",
    strike_count: int = 10,
    include_underlying_quote: bool = True,
    strategy: str = "SINGLE",
    interval: Optional[float] = None,
    strike: Optional[float] = None,
    range_: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    volatility: Optional[float] = None,
    underlying_price: Optional[float] = None,
    interest_rate: Optional[float] = None,
    days_to_expiration: Optional[int] = None,
    exp_month: Optional[str] = None,
    option_type: Optional[str] = None,
    entitlement: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch the options chain for a given symbol from Schwab."""
    headers = {"Authorization": f"Bearer {access_token}"}
    params: Dict[str, Any] = {
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


def get_quote(access_token: str, symbol: str) -> Dict[str, Any]:
    """Fetch a real-time quote for a symbol."""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{SCHWAB_MARKET_DATA_BASE}/{symbol}/quotes"
    response = httpx.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Filters (formerly schwab_filters.py)
# ---------------------------------------------------------------------------


def _is_weekly_expiry(expiry_str: str) -> bool:
    """Return True if the expiry date falls within the next WEEKLY_EXPIRY_DAYS days."""
    try:
        expiry = date.fromisoformat(expiry_str)
    except ValueError:
        return False
    today = date.today()
    return today <= expiry <= today + timedelta(days=config.WEEKLY_EXPIRY_DAYS)


def _is_near_target_delta(contract: Dict[str, Any]) -> bool:
    delta = contract.get("delta")
    if delta is None:
        return False
    return abs(abs(float(delta)) - config.DELTA_TARGET) <= config.DELTA_TOLERANCE


def filter_contracts(chain_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Filter put contracts from a Schwab /marketdata/chains response."""
    put_exp_map: Dict[str, Any] = chain_data.get("putExpDateMap", {})
    filtered: List[Dict[str, Any]] = []

    for expiry_key, strikes in put_exp_map.items():
        expiry_str = expiry_key.split(":")[0]
        if not _is_weekly_expiry(expiry_str):
            continue
        for strike_str, contracts in strikes.items():
            for contract in contracts:
                if _is_near_target_delta(contract):
                    filtered.append({**contract, "expiry": expiry_str, "strike": float(strike_str)})

    logger.info("filter_contracts returned %d contracts", len(filtered))
    return filtered


def filter_options_by_delta(
    options: List[Dict[str, Any]],
    min_delta: float,
    max_delta: float,
) -> List[Dict[str, Any]]:
    result = []
    for opt in options:
        delta = opt.get("delta")
        if delta is None:
            continue
        if min_delta <= abs(delta) <= max_delta:
            result.append(opt)
    return result


def filter_options_by_dte(
    options: List[Dict[str, Any]],
    min_dte: int,
    max_dte: int,
) -> List[Dict[str, Any]]:
    result = []
    for opt in options:
        dte = opt.get("daysToExpiration")
        if dte is None:
            continue
        if min_dte <= dte <= max_dte:
            result.append(opt)
    return result


def filter_options_by_open_interest(
    options: List[Dict[str, Any]],
    min_open_interest: int,
) -> List[Dict[str, Any]]:
    result = []
    for opt in options:
        oi = opt.get("openInterest")
        if oi is None:
            continue
        if oi >= min_open_interest:
            result.append(opt)
    return result


def filter_options_by_volume(
    options: List[Dict[str, Any]],
    min_volume: int,
) -> List[Dict[str, Any]]:
    result = []
    for opt in options:
        volume = opt.get("totalVolume")
        if volume is None:
            continue
        if volume >= min_volume:
            result.append(opt)
    return result


def filter_options_by_bid_ask_spread(
    options: List[Dict[str, Any]],
    max_spread: float,
) -> List[Dict[str, Any]]:
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


def compute_days_to_expiration(expiration_date: date, today: Optional[date] = None) -> int:
    """Compute the number of calendar days between today and expiration_date."""
    if today is None:
        today = date.today()
    return (expiration_date - today).days


def compute_annualized_roi(
    premium: float,
    strike: float,
    days_to_expiration: int,
) -> Optional[float]:
    """Compute the annualized return on investment for a Cash Covered Put (CCP)."""
    if days_to_expiration <= 0:
        raise ValueError("days_to_expiration must be a positive integer.")
    if strike <= 0:
        raise ValueError("strike must be a positive number.")
    roi = (premium / strike) * (365.0 / days_to_expiration)
    return roi


def enrich_put_options_with_roi(
    put_options: list[dict],
    today: Optional[date] = None,
) -> list[dict]:
    """Enrich a list of put option records with annualized_roi and days_to_expiration."""
    if today is None:
        today = date.today()

    enriched = []

    for option in put_options:
        record = dict(option)

        if str(record.get("option_type", "")).lower() != "put":
            enriched.append(record)
            continue

        expiration_raw = record.get("expiration_date")

        if expiration_raw is None:
            record["days_to_expiration"] = 0
            record["annualized_roi"] = None
            enriched.append(record)
            continue

        if isinstance(expiration_raw, str):
            try:
                expiration_date = date.fromisoformat(expiration_raw)
            except ValueError:
                record["days_to_expiration"] = 0
                record["annualized_roi"] = None
                enriched.append(record)
                continue
        elif isinstance(expiration_raw, date):
            expiration_date = expiration_raw
        else:
            record["days_to_expiration"] = 0
            record["annualized_roi"] = None
            enriched.append(record)
            continue

        dte = compute_days_to_expiration(expiration_date, today)
        record["days_to_expiration"] = dte

        strike = record.get("strike")
        premium = record.get("premium")
        if premium is None:
            premium = record.get("bid")

        if strike is None or premium is None:
            record["annualized_roi"] = None
            enriched.append(record)
            continue

        try:
            strike = float(strike)
            premium = float(premium)
        except (TypeError, ValueError):
            record["annualized_roi"] = None
            enriched.append(record)
            continue

        try:
            record["annualized_roi"] = compute_annualized_roi(premium, strike, dte)
        except ValueError:
            record["annualized_roi"] = None

        enriched.append(record)

    return enriched


def calculate_ccp(
    option: Dict[str, Any],
    underlying_price: float,
) -> Optional[float]:
    """Calculate the Capital-at-risk / Credit-received Percentage (CCP)."""
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
    option: Dict[str, Any],
    underlying_price: float,
) -> Optional[float]:
    """Annualise the CCP based on days-to-expiration."""
    ccp = calculate_ccp(option, underlying_price)
    if ccp is None:
        return None
    dte = option.get("daysToExpiration")
    if not dte or dte <= 0:
        return None
    return round(ccp / dte * 365, 4)


# ---------------------------------------------------------------------------
# Market data service (formerly market_data_service.py)
# ---------------------------------------------------------------------------


def get_filtered_options(tickers: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """For each ticker: authenticate, fetch options chain, return filtered contracts."""
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


# ---------------------------------------------------------------------------
# Flatten chain helper
# ---------------------------------------------------------------------------


def flatten_chain(ticker: str, chain: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten the nested Schwab options chain response into a list of contract dicts."""
    rows = []
    for map_key in ("callExpDateMap", "putExpDateMap"):
        exp_map = chain.get(map_key) or {}
        for _exp_date_key, strikes in exp_map.items():
            if not isinstance(strikes, dict):
                continue
            for _strike_key, contract_list in strikes.items():
                if not isinstance(contract_list, list):
                    continue
                for contract in contract_list:
                    if not isinstance(contract, dict):
                        continue
                    rows.append({
                        "ticker": ticker,
                        "putCall": contract.get("putCall"),
                        "strikePrice": contract.get("strikePrice"),
                        "expirationDate": contract.get("expirationDate"),
                        "bid": contract.get("bid"),
                        "ask": contract.get("ask"),
                        "last": contract.get("last"),
                        "volume": contract.get("volume"),
                        "openInterest": contract.get("openInterest"),
                        "delta": contract.get("delta"),
                        "gamma": contract.get("gamma"),
                        "theta": contract.get("theta"),
                        "vega": contract.get("vega"),
                        "impliedVolatility": contract.get("impliedVolatility"),
                        "inTheMoney": contract.get("inTheMoney"),
                    })
    return rows


# ---------------------------------------------------------------------------
# SchwabClient (formerly schwab_client.py)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# SchwabService class (formerly market_data_service.py)
# ---------------------------------------------------------------------------


class SchwabService:
    """
    High-level service that wraps Schwab API authentication and market data retrieval.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        vault_url: Optional[str] = None,
    ) -> None:
        self.client_id = client_id or os.environ.get("SCHWAB_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("SCHWAB_CLIENT_SECRET", "")
        self.refresh_token = refresh_token or os.environ.get("SCHWAB_REFRESH_TOKEN", "")
        self._vault_url = vault_url
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0

    def _is_token_valid(self) -> bool:
        """Return True if we have a non-expired access token."""
        if not self._access_token or not self._token_expiry:
            return False
        return datetime.now(timezone.utc) < self._token_expiry

    def _refresh_access_token(self) -> None:
        logger.debug("Refreshing Schwab access token.")
        self._access_token = get_access_token(vault_url=self._vault_url)
        self._token_expiry = time.time() + 25 * 60

    def _ensure_token(self) -> str:
        """Return a valid access token, refreshing if necessary."""
        if not self._access_token or time.time() >= self._token_expiry:
            self._refresh_access_token()
        return self._access_token

    def fetch_options_chain(
        self,
        symbol: str,
        contract_type: str = "ALL",
        strike_count: int = 10,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Fetch the options chain for *symbol*."""
        token = self._ensure_token()
        return get_options_chain(
            access_token=token,
            symbol=symbol,
            contract_type=contract_type,
            strike_count=strike_count,
            **kwargs,
        )

    def fetch_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetch a real-time quote for *symbol*."""
        token = self._ensure_token()
        return get_quote(access_token=token, symbol=symbol)

    async def get_option_chain(
        self,
        ticker: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Async wrapper to fetch options chain (used by routers)."""
        import asyncio
        token = self._ensure_token()
        return await asyncio.to_thread(
            fetch_options_chain, ticker, token, from_date, to_date
        )

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
    ) -> List[Dict[str, Any]]:
        """Fetch options chain and apply standard filters."""
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
        options: List[Dict[str, Any]],
        underlying_price: float,
    ) -> List[Dict[str, Any]]:
        """Add *ccp* and *annualisedCcp* fields to each option dict."""
        enriched = []
        for opt in options:
            opt = dict(opt)
            opt["ccp"] = calculate_ccp(opt, underlying_price)
            opt["annualisedCcp"] = calculate_annualised_ccp(opt, underlying_price)
            enriched.append(opt)
        return enriched

    # ------------------------------------------------------------------
    # Stub methods required by tests (all patchable via patch.object)
    # ------------------------------------------------------------------

    def calculate_ccp(
        self,
        spot_price: float,
        strike_price: float,
        days_to_expiry: int,
        volatility: float,
        option_type: str = "CALL",
    ) -> float:
        raise NotImplementedError("calculate_ccp is not implemented")

    def get_auth_url(self) -> str:
        raise NotImplementedError("get_auth_url is not implemented in this service version")

    @staticmethod
    def get_filtered_options(tickers: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Class-level alias for the module-level get_filtered_options function."""
        return get_filtered_options(tickers)

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        raise NotImplementedError("exchange_code_for_token is not implemented")

    def is_authenticated(self) -> bool:
        return self._is_token_valid()

    def get_access_token(self) -> str:
        return self._ensure_token()

    def get_options_chain(self, symbol: str, **kwargs: Any) -> Dict[str, Any]:
        """Synchronous options chain fetch (delegates to fetch_options_chain)."""
        return self.fetch_options_chain(symbol, **kwargs)

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Synchronous quote fetch (delegates to fetch_quote)."""
        return self.fetch_quote(symbol)

    def filter_by_expiration(
        self, contracts: List[Dict[str, Any]], from_date: str, to_date: str
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("filter_by_expiration is not implemented")

    def filter_by_strike_range(
        self, contracts: List[Dict[str, Any]], min_strike: float, max_strike: float
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("filter_by_strike_range is not implemented")

    def filter_by_volume(
        self, contracts: List[Dict[str, Any]], min_volume: int
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("filter_by_volume is not implemented")

    def filter_by_open_interest(
        self, contracts: List[Dict[str, Any]], min_open_interest: int
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("filter_by_open_interest is not implemented")

    def filter_by_delta(
        self, contracts: List[Dict[str, Any]], min_delta: float, max_delta: float
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("filter_by_delta is not implemented")

    def filter_by_bid_ask_spread(
        self, contracts: List[Dict[str, Any]], max_spread_pct: float
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("filter_by_bid_ask_spread is not implemented")

    def apply_all_filters(
        self, contracts: List[Dict[str, Any]], **kwargs: Any
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("apply_all_filters is not implemented")

    def get_market_hours(self, market: str) -> Dict[str, Any]:
        raise NotImplementedError("get_market_hours is not implemented")

    def get_price_history(
        self, symbol: str, period_type: str, period: int, **kwargs: Any
    ) -> Dict[str, Any]:
        raise NotImplementedError("get_price_history is not implemented")

    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        raise NotImplementedError("get_multiple_quotes is not implemented")

    async def async_get_options_chain(
        self, symbol: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """Async version of get_options_chain."""
        return await self.get_option_chain(symbol)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _flatten_options_chain(
    chain: Dict[str, Any],
    contract_type: str,
) -> List[Dict[str, Any]]:
    """Flatten the nested Schwab options chain response into a list of contract dicts."""
    result: List[Dict[str, Any]] = []

    maps_to_process: List[str] = []
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
                    if "expirationDate" not in contract:
                        contract["expirationDate"] = exp_date_str.split(":")[0]
                    if "strikePrice" not in contract:
                        try:
                            contract["strikePrice"] = float(strike_str)
                        except ValueError:
                            pass
                    result.append(contract)

    return result
