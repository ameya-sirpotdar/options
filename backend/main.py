from fastapi import FastAPI

from backend.api.logging_config import configure_logging
from backend.api.middleware import RequestLoggingMiddleware
from backend.api.poll import router as poll_router
from backend.api.routers.health import router as health_router

configure_logging()

app = FastAPI(title="Options Polling API", version="1.0.0")

app.add_middleware(RequestLoggingMiddleware)

app.include_router(health_router)
app.include_router(poll_router)
