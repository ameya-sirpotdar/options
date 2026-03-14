backend/services/schwab_service.py
import base64
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class SchwabService:
    """
    Consolidated Schwab service handling authentication, token management,
    market data retrieval, and options chain filtering.
    """

    BASE_URL = "https://api.schwabapi.com/marketdata/v1"
    AUTH_URL = "https://api.schwabapi.com/v1/oauth/authorize"
    TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        refresh_token: Optional[str] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.refresh_token = refresh_token

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    # -------------------------------------------------------------------------
    # Auth helpers
    # -------------------------------------------------------------------------

    def get_authorization_url(self) -> str:
        """Return the OAuth2 authorization URL for the user to visit."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def _basic_auth_header(self) -> str:
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def exchange_code_for_tokens(self, code: str) -> dict:
        """Exchange an authorization code for access + refresh tokens."""
        headers = {
            "Authorization": self._basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()

        self._access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 1800)
        self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        logger.info("Exchanged authorization code for tokens successfully.")
        return token_data

    async def refresh_access_token(self) -> str:
        """Use the stored refresh token to obtain a new access token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available. Re-authorization required.")

        headers = {
            "Authorization": self._basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()

        self._access_token = token_data.get("access_token")
        new_refresh = token_data.get("refresh_token")
        if new_refresh:
            self.refresh_token = new_refresh
        expires_in = token_data.get("expires_in", 1800)
        self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        logger.info("Access token refreshed successfully.")
        return self._access_token

    def _is_token_expired(self) -> bool:
        if self._token_expires_at is None:
            return True
        return datetime.utcnow() >= self._token_expires_at - timedelta(seconds=60)

    async def get_valid_access_token(self) -> str:
        """Return a valid access token, refreshing if necessary."""
        if self._access_token is None or self._is_token_expired():
            await self.refresh_access_token()
        return self._access_token

    # -------------------------------------------------------------------------
    # Market data
    # -------------------------------------------------------------------------

    async def get_quote(self, symbol: str) -> dict:
        """Fetch a real-time quote for the given symbol."""
        token = await self.get_valid_access_token()
        url = f"{self.BASE_URL}/quotes/{symbol.upper()}"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

        data = response.json()
        logger.debug("Fetched quote for %s", symbol)
        return data

    async def get_options_chain(
        self,
        symbol: str,
        contract_type: str = "ALL",
        strike_count: int = 10,
        include_underlying_quote: bool = True,
        strategy: str = "SINGLE",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> dict:
        """
        Fetch the options chain for a given symbol.

        Parameters
        ----------
        symbol:
            Underlying ticker symbol.
        contract_type:
            ``"CALL"``, ``"PUT"``, or ``"ALL"``.
        strike_count:
            Number of strikes to return above/below the at-the-money price.
        include_underlying_quote:
            Whether to embed the underlying quote in the response.
        strategy:
            Options strategy type (e.g. ``"SINGLE"``, ``"COVERED"``).
        from_date:
            Earliest expiration date in ``YYYY-MM-DD`` format.
        to_date:
            Latest expiration date in ``YYYY-MM-DD`` format.
        """
        token = await self.get_valid_access_token()
        url = f"{self.BASE_URL}/chains"
        headers = {"Authorization": f"Bearer {token}"}
        params: dict = {
            "symbol": symbol.upper(),
            "contractType": contract_type,
            "strikeCount": strike_count,
            "includeUnderlyingQuote": str(include_underlying_quote).lower(),
            "strategy": strategy,
        }
        if from_date:
            params["fromDate"] = from_date
        if to_date:
            params["toDate"] = to_date

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()

        data = response.json()
        logger.debug(
            "Fetched options chain for %s (%s contracts)", symbol, contract_type
        )
        return data

    # -------------------------------------------------------------------------
    # Options chain filtering helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def extract_contracts(options_chain: dict, contract_type: str = "ALL") -> list[dict]:
        """
        Flatten an options chain response into a list of individual contracts.

        Parameters
        ----------
        options_chain:
            Raw response from :meth:`get_options_chain`.
        contract_type:
            ``"CALL"``, ``"PUT"``, or ``"ALL"`` to filter by side.
        """
        contracts: list[dict] = []

        sides = []
        if contract_type in ("CALL", "ALL"):
            sides.append(("callExpDateMap", "CALL"))
        if contract_type in ("PUT", "ALL"):
            sides.append(("putExpDateMap", "PUT"))

        for map_key, side_label in sides:
            exp_map = options_chain.get(map_key, {})
            for expiration_key, strikes in exp_map.items():
                for strike_price, contract_list in strikes.items():
                    for contract in contract_list:
                        contract["_contractType"] = side_label
                        contract["_expirationKey"] = expiration_key
                        contract["_strikePrice"] = float(strike_price)
                        contracts.append(contract)

        return contracts

    @staticmethod
    def filter_by_delta(
        contracts: list[dict],
        min_delta: float = 0.20,
        max_delta: float = 0.80,
    ) -> list[dict]:
        """
        Filter contracts to those whose absolute delta falls within the given range.
        """
        filtered = []
        for c in contracts:
            delta = c.get("delta")
            if delta is None:
                continue
            if min_delta <= abs(delta) <= max_delta:
                filtered.append(c)
        return filtered

    @staticmethod
    def filter_by_open_interest(
        contracts: list[dict], min_open_interest: int = 100
    ) -> list[dict]:
        """Filter contracts to those with at least *min_open_interest* open contracts."""
        return [
            c for c in contracts if (c.get("openInterest") or 0) >= min_open_interest
        ]

    @staticmethod
    def filter_by_volume(
        contracts: list[dict], min_volume: int = 10
    ) -> list[dict]:
        """Filter contracts to those with at least *min_volume* volume today."""
        return [c for c in contracts if (c.get("totalVolume") or 0) >= min_volume]

    @staticmethod
    def filter_by_bid_ask_spread(
        contracts: list[dict], max_spread_pct: float = 0.10
    ) -> list[dict]:
        """
        Filter contracts where the bid-ask spread as a fraction of the mid-price
        does not exceed *max_spread_pct*.
        """
        filtered = []
        for c in contracts:
            bid = c.get("bid") or 0.0
            ask = c.get("ask") or 0.0
            if ask <= 0:
                continue
            mid = (bid + ask) / 2
            if mid <= 0:
                continue
            spread_pct = (ask - bid) / mid
            if spread_pct <= max_spread_pct:
                filtered.append(c)
        return filtered

    @staticmethod
    def filter_by_days_to_expiration(
        contracts: list[dict],
        min_dte: int = 1,
        max_dte: int = 60,
    ) -> list[dict]:
        """Filter contracts by days to expiration (DTE)."""
        filtered = []
        for c in contracts:
            dte = c.get("daysToExpiration")
            if dte is None:
                continue
            if min_dte <= dte <= max_dte:
                filtered.append(c)
        return filtered

    def apply_standard_filters(
        self,
        contracts: list[dict],
        min_delta: float = 0.20,
        max_delta: float = 0.80,
        min_open_interest: int = 100,
        min_volume: int = 10,
        max_spread_pct: float = 0.10,
        min_dte: int = 1,
        max_dte: int = 60,
    ) -> list[dict]:
        """
        Apply the full standard filter pipeline to a list of contracts.

        Filters are applied in order:
        1. Delta range
        2. Open interest
        3. Volume
        4. Bid-ask spread
        5. Days to expiration
        """
        contracts = self.filter_by_delta(contracts, min_delta, max_delta)
        contracts = self.filter_by_open_interest(contracts, min_open_interest)
        contracts = self.filter_by_volume(contracts, min_volume)
        contracts = self.filter_by_bid_ask_spread(contracts, max_spread_pct)
        contracts = self.filter_by_days_to_expiration(contracts, min_dte, max_dte)
        return contracts