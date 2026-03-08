import logging
import os

from fastapi import FastAPI

from backend.api.logging_config import configure_logging
from backend.api.middleware import RequestLoggingMiddleware
from backend.api.poll import router as poll_router
from backend.api.routers.health import router as health_router
from backend.api.routers.trades import router as trades_router
from backend.services.azure_table_service import AzureTableService

configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI(title="Options Polling API", version="1.0.0")

app.add_middleware(RequestLoggingMiddleware)

app.include_router(health_router)
app.include_router(poll_router)
app.include_router(trades_router)


@app.on_event("startup")
async def startup_event() -> None:
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if connection_string:
        try:
            azure_table_service = AzureTableService(connection_string=connection_string)
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
