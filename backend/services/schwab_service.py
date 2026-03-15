backend/services/schwab_service.py
from backend.services.schwab_auth import SchwabAuth
from backend.services.schwab_market_data import SchwabMarketData
from backend.services.schwab_filters import SchwabFilters


class SchwabService:
    """
    Consolidated service that composes SchwabAuth, SchwabMarketData, and SchwabFilters
    into a single cohesive interface for interacting with the Schwab API.
    """

    def __init__(self):
        self.auth = SchwabAuth()
        self.market_data = SchwabMarketData(self.auth)
        self.filters = SchwabFilters()

    def get_access_token(self) -> str:
        return self.auth.get_access_token()

    def get_options_chain(self, symbol: str, **kwargs) -> dict:
        return self.market_data.get_options_chain(symbol, **kwargs)

    def filter_options_chain(self, options_chain: dict, **kwargs) -> dict:
        return self.filters.filter_options_chain(options_chain, **kwargs)