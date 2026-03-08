import os


SCHWAB_KEY_VAULT_URL = os.environ.get("KEY_VAULT_URL", "")
SCHWAB_CLIENT_ID_SECRET = os.environ.get("SCHWAB_CLIENT_ID_SECRET_NAME", "schwab-client-id")
SCHWAB_CLIENT_SECRET_SECRET = os.environ.get("SCHWAB_CLIENT_SECRET_SECRET_NAME", "schwab-client-secret")
SCHWAB_TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
SCHWAB_CHAINS_URL = "https://api.schwabapi.com/marketdata/v1/chains"
DELTA_TARGET = 0.30
DELTA_TOLERANCE = 0.05
WEEKLY_EXPIRY_DAYS = 8

# Tradability Index Engine weights
TRADABILITY_WEIGHT_PREMIUM = float(os.environ.get("TRADABILITY_WEIGHT_PREMIUM", "0.35"))
TRADABILITY_WEIGHT_LIQUIDITY = float(os.environ.get("TRADABILITY_WEIGHT_LIQUIDITY", "0.25"))
TRADABILITY_WEIGHT_DELTA = float(os.environ.get("TRADABILITY_WEIGHT_DELTA", "0.20"))
TRADABILITY_WEIGHT_SPREAD = float(os.environ.get("TRADABILITY_WEIGHT_SPREAD", "0.20"))