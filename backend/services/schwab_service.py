import os
import base64
import httpx
from typing import Optional
from datetime import datetime, timedelta, timezone

from backend.models.options_chain_request import OptionsChainRequest
from backend.models.options_chain_response import OptionsChainResponse


class SchwabService:
    """
    Consolidated Schwab service that handles authentication, token management,
    and market data retrieval for options chains.
    """

    BASE_URL = "https://api.schwabapi.com/marketdata/v1"
    AUTH_URL = "https://api.schwabapi.com/v1/oauth/token"

    def __init__(self):
        self.client_id = os.getenv("SCHWAB_CLIENT_ID", "")
        self.client_secret = os.getenv("SCHWAB_CLIENT_SECRET", "")
        self.refresh_token = os.getenv("SCHWAB_REFRESH_TOKEN", "")
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Authentication helpers
    # ------------------------------------------------------------------

    def _is_token_valid(self) -> bool:
        """Return True if we have a non-expired access token."""
        if not self._access_token or not self._token_expiry:
            return False
        return datetime.now(timezone.utc) < self._token_expiry

    def _build_auth_header(self) -> str:
        """Build the Basic auth header value from client credentials."""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def authenticate(self) -> str:
        """
        Obtain a new access token using the refresh token grant.
        Stores the token internally and returns it.
        """
        if not self.refresh_token:
            raise ValueError("SCHWAB_REFRESH_TOKEN environment variable is not set.")
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "SCHWAB_CLIENT_ID and SCHWAB_CLIENT_SECRET environment variables must be set."
            )

        headers = {
            "Authorization": self._build_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.AUTH_URL, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()

        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 1800)
        self._token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return self._access_token

    async def get_access_token(self) -> str:
        """Return a valid access token, refreshing if necessary."""
        if not self._is_token_valid():
            await self.authenticate()
        return self._access_token

    # ------------------------------------------------------------------
    # Market data helpers
    # ------------------------------------------------------------------

    def _build_options_chain_params(self, request: OptionsChainRequest) -> dict:
        """Convert an OptionsChainRequest into query parameters for the API."""
        params: dict = {"symbol": request.symbol}

        if request.contract_type:
            params["contractType"] = request.contract_type
        if request.strike_count is not None:
            params["strikeCount"] = request.strike_count
        if request.include_underlying_quote is not None:
            params["includeUnderlyingQuote"] = str(request.include_underlying_quote).lower()
        if request.strategy:
            params["strategy"] = request.strategy
        if request.interval is not None:
            params["interval"] = request.interval
        if request.strike is not None:
            params["strike"] = request.strike
        if request.range:
            params["range"] = request.range
        if request.from_date:
            params["fromDate"] = request.from_date
        if request.to_date:
            params["toDate"] = request.to_date
        if request.volatility is not None:
            params["volatility"] = request.volatility
        if request.underlying_price is not None:
            params["underlyingPrice"] = request.underlying_price
        if request.interest_rate is not None:
            params["interestRate"] = request.interest_rate
        if request.days_to_expiration is not None:
            params["daysToExpiration"] = request.days_to_expiration
        if request.exp_month:
            params["expMonth"] = request.exp_month
        if request.option_type:
            params["optionType"] = request.option_type

        return params

    def _filter_options_chain(self, data: dict) -> dict:
        """
        Filter the raw options chain response to include only standard
        (non-mini, non-non-standard) contracts.
        """
        filtered = dict(data)

        for side in ("callExpDateMap", "putExpDateMap"):
            if side not in data:
                continue
            filtered_side = {}
            for exp_date, strikes in data[side].items():
                filtered_strikes = {}
                for strike_price, contracts in strikes.items():
                    standard_contracts = [
                        c for c in contracts
                        if c.get("optionDeliverablesList") is None
                        or len(c.get("optionDeliverablesList", [])) == 0
                        or all(
                            d.get("deliverableUnits") == 100
                            for d in c.get("optionDeliverablesList", [])
                        )
                    ]
                    if standard_contracts:
                        filtered_strikes[strike_price] = standard_contracts
                if filtered_strikes:
                    filtered_side[exp_date] = filtered_strikes
            filtered[side] = filtered_side

        return filtered

    async def get_options_chain(self, request: OptionsChainRequest) -> OptionsChainResponse:
        """
        Fetch the options chain for the given request from the Schwab API.
        Returns a parsed OptionsChainResponse.
        """
        token = await self.get_access_token()
        params = self._build_options_chain_params(request)

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/chains",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            raw_data = response.json()

        filtered_data = self._filter_options_chain(raw_data)
        return OptionsChainResponse(**filtered_data)

    async def get_quote(self, symbol: str) -> dict:
        """
        Fetch a real-time quote for the given symbol.
        Returns the raw quote dictionary from the Schwab API.
        """
        token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/quotes/{symbol}",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_price_history(
        self,
        symbol: str,
        period_type: str = "day",
        period: int = 10,
        frequency_type: str = "minute",
        frequency: int = 1,
    ) -> dict:
        """
        Fetch historical price data for the given symbol.
        Returns the raw price history dictionary from the Schwab API.
        """
        token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        params = {
            "symbol": symbol,
            "periodType": period_type,
            "period": period,
            "frequencyType": frequency_type,
            "frequency": frequency,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/pricehistory",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()