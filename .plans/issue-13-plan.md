# Implementation Plan: Issue #13 — On-Demand Options Polling Endpoint

## Approach Overview

We will build a FastAPI application in the `backend/` directory with a single `POST /poll/options` endpoint. The endpoint will:
1. Accept and validate a JSON body containing a list of ticker symbols
2. Invoke the LangGraph options agent workflow with those tickers
3. Return a 200 response confirming the poll was initiated

Since the LangGraph agent workflow does not yet appear to be implemented (only `__init__.py` stubs exist), we will create a minimal agent stub that can be wired up in future stories, while ensuring the endpoint correctly invokes it.

---

## Files to Create

### `backend/main.py`
FastAPI application entry point. Registers routers and configures the app.

### `backend/api/poll.py`
Defines the `POST /poll/options` route. Handles request parsing, input validation, calls the agent workflow, and returns the response.

### `backend/models/poll.py`
Pydantic models for request and response schemas:
- `PollOptionsRequest`: contains `tickers: List[str]` with validation (non-empty list, non-empty strings, reasonable length)
- `PollOptionsResponse`: contains `status: str` and `message: str`

### `backend/agents/options_agent.py`
LangGraph options agent workflow stub. Exposes a `run_options_poll(tickers: List[str])` function. Initially a stub that can be replaced with the real LangGraph graph in a future story.

### `backend/services/polling_service.py`
Service layer that mediates between the API route and the agent. Calls `run_options_poll` and handles any agent-level exceptions.

### `tests/test_poll_options.py`
Unit and integration tests for the endpoint.

---

## Files to Modify

### `backend/api/__init__.py`
Export or register the poll router.

### `backend/agents/__init__.py`
Export `run_options_poll` from `options_agent`.

### `backend/models/__init__.py`
Export `PollOptionsRequest` and `PollOptionsResponse`.

### `backend/services/__init__.py`
Export `PollingService` or the polling service function.

### `backend/requirements.txt`
Add dependencies: `fastapi`, `uvicorn`, `pydantic`, `langgraph` (or a placeholder if not yet available).

---

## Implementation Steps

### Step 1: Define Pydantic Models (`backend/models/poll.py`)
```python
from pydantic import BaseModel, validator
from typing import List

class PollOptionsRequest(BaseModel):
    tickers: List[str]

    @validator('tickers')
    def tickers_must_be_non_empty(cls, v):
        if not v:
            raise ValueError('tickers list must not be empty')
        for ticker in v:
            if not ticker or not ticker.strip():
                raise ValueError('each ticker must be a non-empty string')
            if len(ticker) > 10:
                raise ValueError(f'ticker symbol too long: {ticker}')
        return [t.upper().strip() for t in v]

class PollOptionsResponse(BaseModel):
    status: str
    message: str
    tickers: List[str]
```

### Step 2: Create Agent Stub (`backend/agents/options_agent.py`)
```python
from typing import List

def run_options_poll(tickers: List[str]) -> dict:
    """
    Stub for the LangGraph options agent workflow.
    Replace with actual LangGraph graph invocation in Story 2.x.
    """
    # TODO: Replace with LangGraph workflow invocation
    # e.g.: graph = build_options_graph()
    #        result = graph.invoke({"tickers": tickers})
    return {"initiated": True, "tickers": tickers}
```

### Step 3: Create Polling Service (`backend/services/polling_service.py`)
```python
from typing import List
from backend.agents.options_agent import run_options_poll

class PollingService:
    def initiate_poll(self, tickers: List[str]) -> dict:
        result = run_options_poll(tickers)
        return result
```

### Step 4: Create API Route (`backend/api/poll.py`)
```python
from fastapi import APIRouter, HTTPException
from backend.models.poll import PollOptionsRequest, PollOptionsResponse
from backend.services.polling_service import PollingService

router = APIRouter()
polling_service = PollingService()

@router.post("/poll/options", response_model=PollOptionsResponse, status_code=200)
def poll_options(request: PollOptionsRequest):
    try:
        result = polling_service.initiate_poll(request.tickers)
        return PollOptionsResponse(
            status="initiated",
            message=f"Options poll initiated for {len(request.tickers)} ticker(s).",
            tickers=result["tickers"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 5: Create FastAPI App (`backend/main.py`)
```python
from fastapi import FastAPI
from backend.api.poll import router as poll_router

app = FastAPI(title="Options Agent API", version="0.1.0")
app.include_router(poll_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

### Step 6: Update `backend/requirements.txt`
Add:
```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
pydantic>=2.0.0
httpx>=0.27.0  # for TestClient
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

### Step 7: Write Tests (`tests/test_poll_options.py`)
See Test Strategy section below.

---

## Test Strategy

### Unit Tests
- `PollOptionsRequest` validation: empty list, empty string ticker, oversized ticker, valid input normalization (uppercase, strip)
- `PollingService.initiate_poll`: mock `run_options_poll`, verify it is called with correct tickers
- `run_options_poll` stub: verify it returns expected dict shape

### Integration Tests (via FastAPI TestClient)
- `POST /poll/options` with valid body `{"tickers": ["NVDA", "AAPL"]}` → 200, correct response shape
- `POST /poll/options` with empty tickers list `{"tickers": []}` → 422 Unprocessable Entity
- `POST /poll/options` with missing `tickers` field → 422
- `POST /poll/options` with non-string ticker values → 422
- `POST /poll/options` with mixed-case tickers → 200, tickers normalized to uppercase
- `GET /health` → 200 `{"status": "ok"}`

### Edge Cases
- Single ticker in list
- Large list of tickers (e.g. 50+)
- Tickers with whitespace (should be stripped)
- Agent raises an exception → endpoint returns 500

---

## Edge Cases to Handle

1. **Empty tickers list** — return 422 with clear validation error
2. **Blank/whitespace-only ticker strings** — reject with 422
3. **Ticker normalization** — uppercase and strip whitespace before passing to agent
4. **Agent failure** — catch exceptions in service layer, surface as 500
5. **Duplicate tickers** — optionally deduplicate before passing to agent (log a warning)
6. **Very long ticker symbols** — reject symbols > 10 characters
