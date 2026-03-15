import asyncio
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.logging_config import configure_logging
from backend.api.middleware import RequestLoggingMiddleware
from backend.api.routers.health import router as health_router
from backend.api.routers.options_chain import router as options_chain_router
from backend.api.routers.trades import router as trades_router
from backend.services.azure_table_service import AzureTableService
from backend.services.schwab_client import SchwabClient
from backend.services.schwab_auth import SchwabAuth

configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI(title="Options Polling API", version="1.0.0")

_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
_allow_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(health_router)
app.include_router(options_chain_router)
app.include_router(trades_router)


@app.on_event("startup")
async def startup_event() -> None:
    # ── AzureTableService ────────────────────────────────────────────────────
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if connection_string:
        try:
            azure_table_service = await asyncio.to_thread(AzureTableService, connection_string=connection_string)
            app.state.azure_table_service = azure_table_service
            logger.info("AzureTableService initialised and attached to app.state")
        except Exception as exc:
            logger.warning(
                "AzureTableService could not be initialised at startup: %s", exc
            )
            app.state.azure_table_service = None
    else:
        logger.warning(
            "AZURE_STORAGE_CONNECTION_STRING not set; "
            "AzureTableService will not be available"
        )
        app.state.azure_table_service = None

    # ── SchwabClient ─────────────────────────────────────────────────────────
    try:
        vault_url = os.getenv("AZURE_KEY_VAULT_URL")  # optional
        schwab_auth = SchwabAuth(vault_url=vault_url)
        schwab_client = SchwabClient(auth=schwab_auth)
        app.state.schwab_client = schwab_client
        logger.info("SchwabClient initialised and attached to app.state")
    except Exception as exc:
        logger.warning(
            "SchwabClient could not be initialised at startup: %s", exc
        )
        app.state.schwab_client = None
