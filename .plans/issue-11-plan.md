# Implementation Plan: FastAPI Backend Service with Health Endpoint and Logging

## Approach

Create a minimal but production-ready FastAPI application under `backend/api/`. The app will expose a `GET /health` endpoint, configure structured application-level logging, and add middleware for per-request logging. All dependencies will be pinned in `backend/requirements.txt`. A test module will verify the health endpoint returns HTTP 200 with the expected payload.

---

## Files to Create

### `backend/api/main.py`
Entry point for the FastAPI application. Configures logging, registers middleware, and mounts routers.

### `backend/api/routers/__init__.py`
Makes `routers` a Python package.

### `backend/api/routers/health.py`
Defines the `GET /health` router returning service status.

### `backend/api/logging_config.py`
Centralised logging configuration (structured JSON logging via `python-json-logger` or stdlib `logging.config.dictConfig`).

### `backend/api/middleware.py`
Starlette/FastAPI middleware that logs each incoming request (method, path, status code, duration).

### `tests/test_health.py`
Unit/integration test using `httpx` + `TestClient` to assert `GET /health` returns 200 and correct JSON body.

---

## Files to Modify

### `backend/requirements.txt`
Add (with pinned versions):
```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
python-json-logger>=2.0.7
httpx>=0.27.0
pytest>=8.1.0
pytest-asyncio>=0.23.0
```

### `backend/api/__init__.py`
Optionally expose the `app` object for import convenience (can remain minimal).

---

## Implementation Steps

### Step 1 — Dependencies
Update `backend/requirements.txt` with FastAPI, Uvicorn, python-json-logger, httpx, pytest, and pytest-asyncio.

### Step 2 — Logging Configuration (`backend/api/logging_config.py`)
```python
import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}


def setup_logging() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)
```

### Step 3 — Request Logging Middleware (`backend/api/middleware.py`)
```python
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        return response
```

### Step 4 — Health Router (`backend/api/routers/health.py`)
```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="backend-api")
```

### Step 5 — Application Entry Point (`backend/api/main.py`)
```python
from fastapi import FastAPI
from backend.api.logging_config import setup_logging
from backend.api.middleware import RequestLoggingMiddleware
from backend.api.routers import health

setup_logging()

app = FastAPI(title="Backend API", version="0.1.0")
app.add_middleware(RequestLoggingMiddleware)
app.include_router(health.router)
```

### Step 6 — Tests (`tests/test_health.py`)
```python
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_body():
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "backend-api"
```

### Step 7 — Verify Uvicorn Start
Confirm the service starts cleanly:
```bash
uvicorn backend.api.main:app --reload
```

---

## Test Strategy

- **Unit tests**: `TestClient` against the FastAPI app — health endpoint status code and body.
- **Smoke test**: Manual `uvicorn` start + `curl http://localhost:8000/health`.
- **Logging verification**: Confirm JSON log lines appear in stdout during test run.

---

## Edge Cases to Handle

- `python-json-logger` import path differs between versions (`pythonjsonlogger.jsonlogger` vs `pythonjsonlogger`). Pin version and use correct import.
- Ensure `backend/` is on `PYTHONPATH` when running tests (add `pytest.ini` or `pyproject.toml` `pythonpath` setting if needed).
- Middleware must call `call_next` and return the response even if logging fails — wrap logger call in try/except if needed.
- Health endpoint should not depend on any external service so it always returns 200 in baseline state.
