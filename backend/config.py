import os
from pydantic_settings import BaseSettings
from typing import Optional


SCHWAB_KEY_VAULT_URL = os.environ.get("KEY_VAULT_URL", "")
SCHWAB_CLIENT_ID_SECRET = os.environ.get("SCHWAB_CLIENT_ID_SECRET_NAME", "schwab-client-id")
SCHWAB_CLIENT_SECRET_SECRET = os.environ.get("SCHWAB_CLIENT_SECRET_SECRET_NAME", "schwab-client-secret")
SCHWAB_TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
SCHWAB_CHAINS_URL = "https://api.schwabapi.com/marketdata/v1/chains"
DELTA_TARGET = 0.30
DELTA_TOLERANCE = 0.05
WEEKLY_EXPIRY_DAYS = 8


class Settings(BaseSettings):
    # Tradability Index weights
    weight_volume: float = 0.25
    weight_open_interest: float = 0.25
    weight_bid_ask_spread: float = 0.20
    weight_implied_volatility: float = 0.15
    weight_delta_proximity: float = 0.15

    # Optional overrides for Schwab API config
    key_vault_url: Optional[str] = None
    schwab_client_id_secret_name: Optional[str] = None
    schwab_client_secret_secret_name: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()