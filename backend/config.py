import os


# Azure Key Vault (optional — omit or leave blank to use direct env-var credentials)
SCHWAB_KEY_VAULT_URL = os.environ.get("KEY_VAULT_URL", "") or None

# Key Vault secret names (used only when SCHWAB_KEY_VAULT_URL is set)
SCHWAB_CLIENT_ID_SECRET = os.environ.get("SCHWAB_CLIENT_ID_SECRET_NAME", "schwab-client-id")
SCHWAB_CLIENT_SECRET_SECRET = os.environ.get("SCHWAB_CLIENT_SECRET_SECRET_NAME", "schwab-client-secret")

# Direct env-var credentials (fallback when Key Vault is not configured)
SCHWAB_CLIENT_ID = os.environ.get("SCHWAB_CLIENT_ID", "")
SCHWAB_CLIENT_SECRET = os.environ.get("SCHWAB_CLIENT_SECRET", "")

SCHWAB_TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
SCHWAB_CHAINS_URL = "https://api.schwabapi.com/marketdata/v1/chains"
DELTA_TARGET = 0.30
DELTA_TOLERANCE = 0.05
WEEKLY_EXPIRY_DAYS = 8

# Tradability Index Engine weights (Epic 5)
TRADABILITY_WEIGHT_VOLUME = float(os.environ.get("TRADABILITY_WEIGHT_VOLUME", "0.25"))
TRADABILITY_WEIGHT_OPEN_INTEREST = float(os.environ.get("TRADABILITY_WEIGHT_OPEN_INTEREST", "0.25"))
TRADABILITY_WEIGHT_BID_ASK_SPREAD = float(os.environ.get("TRADABILITY_WEIGHT_BID_ASK_SPREAD", "0.25"))
TRADABILITY_WEIGHT_IMPLIED_VOLATILITY = float(os.environ.get("TRADABILITY_WEIGHT_IMPLIED_VOLATILITY", "0.25"))