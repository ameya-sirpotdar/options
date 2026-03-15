import asyncio
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.logging_config import configure_logging
from backend.api.middleware import RequestLoggingMiddleware
from backend.api.poll import router as poll_router
from backend.api.routers.health import router as health_router
from backend.api.routers.options_chain import router as options_chain_router
from backend.api.routers.trades import router as trades_router
from backend.services.azure_table_service import AzureTableService
from backend.services.schwab_service import SchwabService

configure_logging()

logger = logging.getLogger(__name__)

# Module-level references (updated during startup; exposed so tests can patch them)
azure_table_service = None
schwab_service = None

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
    global azure_table_service, schwab_service

    # ── AzureTableService ────────────────────────────────────────────────────
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if connection_string:
        try:
            _ats = await asyncio.to_thread(AzureTableService, connection_string=connection_string)
            azure_table_service = _ats
            app.state.azure_table_service = _ats
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

    # ── SchwabService ─────────────────────────────────────────────────────────
    try:
        vault_url = os.getenv("AZURE_KEY_VAULT_URL")  # optional
        _svc = SchwabService(vault_url=vault_url)
        schwab_service = _svc
        app.state.schwab_client = _svc
        app.state.schwab_service = _svc
        logger.info("SchwabService initialised and attached to app.state")
    except Exception as exc:
        logger.warning(
            "SchwabService could not be initialised at startup: %s", exc
        )
        app.state.schwab_client = None
        app.state.schwab_service = None
