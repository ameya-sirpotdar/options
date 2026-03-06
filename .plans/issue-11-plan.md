# Implementation Plan: FastAPI Backend Service (Issue #11)

## Approach

Create a minimal but production-ready FastAPI application under `backend/api/`. The app will expose a `GET /health` endpoint, configure Python's standard `logging` module for application-level logs, and use a middleware or event hook to log each incoming request. A `main.py` entry point will allow `uvicorn backend.api.main:app` to start the service cleanly.

---

## Files to Create

### `backend/api/main.py`
The FastAPI application factory. Responsibilities:
- Instantiate the `FastAPI` app with title/version metadata.
- Configure logging (format, level) at startup via a `lifespan` context manager or `@app.on_event("startup")`.
- Register a middleware that logs method, path, status code, and response time for every request.
- Include the health router.

### `backend/api/routers/__init__.py`
Empty init to make `routers` a package.

### `backend/api/routers/health.py`
Defines the `GET /health` route:
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": "options-agent-api"}
```

### `backend/api/logging_config.py`
Centralised logging configuration:
- Sets up a `logging.basicConfig` or `dictConfig` with a structured format: `%(asctime)s | %(levelname)s | %(name)s | %(message)s`.
- Exposes a `configure_logging(level: str = "INFO")` function called at app startup.

### `tests/test_health.py`
FastAPI `TestClient` tests for the health endpoint and basic logging smoke test.

---

## Files to Modify

### `backend/requirements.txt`
Add (if not already present):
```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
httpx>=0.27.0   # required by TestClient
```

### `backend/api/__init__.py`
No functional change required; may optionally expose `app` for convenience imports.

---

## Implementation Steps

1. **Update `backend/requirements.txt`** — add `fastapi`, `uvicorn[standard]`, and `httpx`.

2. **Create `backend/api/logging_config.py`** — implement `configure_logging()` using `logging.basicConfig` with a timestamped format and configurable log level (default `INFO`).

3. **Create `backend/api/routers/__init__.py`** — empty file.

4. **Create `backend/api/routers/health.py`** — define `APIRouter` with `GET /health` returning `{"status": "ok", "service": "options-agent-api"}`.

5. **Create `backend/api/main.py`**:
   - Call `configure_logging()` at module level (so it applies when uvicorn imports the module).
   - Instantiate `app = FastAPI(title="Options Agent API", version="0.1.0")`.
   - Add a `@app.middleware("http")` that records start time, awaits the response, then logs `method path → status_code (elapsed ms)`.
   - Include the health router: `app.include_router(health.router)`.
   - Add an `if __name__ == "__main__":` block calling `uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)`.

6. **Create `tests/test_health.py`** — use `fastapi.testclient.TestClient` to assert:
   - `GET /health` returns HTTP 200.
   - Response JSON contains `{"status": "ok"}`.

7. **Verify** the service starts: `uvicorn backend.api.main:app --reload` from the repo root.

---

## Test Strategy

- **Unit / integration (pytest + TestClient):** `tests/test_health.py` covers the health endpoint response code and body.
- **Logging smoke test:** Capture log output with `caplog` fixture and assert a request log line is emitted after a test request.
- **Manual / CI:** `uvicorn backend.api.main:app` starts without import errors; `curl http://localhost:8000/health` returns `200 OK`.

---

## Edge Cases

- If `backend/requirements.txt` already contains `fastapi` or `uvicorn`, avoid duplicating entries.
- Logging must not crash when the app is imported by pytest (no file-handler side effects).
- The middleware must call `await call_next(request)` inside a try/finally so response time is always logged even on exceptions.
- `httpx` is needed as a transitive dependency for `TestClient` in newer FastAPI versions — pin it explicitly.
