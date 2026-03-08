# Implementation Plan: Epic 6 — LangGraph Agent Workflow Placeholders

## Approach

Create four agent stub modules under `backend/agents/`, each implementing a consistent interface compatible with LangGraph's node pattern. Wire them together in a `workflow.py` module that defines the pipeline graph:

```
poll trigger → OptionsDataAgent → MetricsAgent → TradabilityAgent → result
```

`MarketSentimentAgent` is scaffolded as a standalone node (referenced in the epic but not in the main flow — likely feeds into MetricsAgent or TradabilityAgent in a follow-up). Each agent will accept a shared state dict and return an updated state dict, following LangGraph conventions.

---

## Files to Create

### `backend/agents/market_sentiment_agent.py`
Placeholder for the MarketSentimentAgent. Accepts pipeline state, returns state with a `market_sentiment` key stubbed as `None`.

### `backend/agents/options_data_agent.py`
Placeholder for the OptionsDataAgent. First node in the main pipeline. Accepts pipeline state, returns state with an `options_data` key stubbed as `None`.

### `backend/agents/metrics_agent.py`
Placeholder for the MetricsAgent. Second node in the main pipeline. Accepts pipeline state, returns state with a `metrics` key stubbed as `None`.

### `backend/agents/tradability_agent.py`
Placeholder for the TradabilityAgent. Third/final node in the main pipeline. Accepts pipeline state, returns state with a `tradability_score` key stubbed as `None`.

### `backend/agents/workflow.py`
Defines the LangGraph `StateGraph` wiring the four agents together. Exports a compiled `app` graph and a `PipelineState` TypedDict. Includes a `run_pipeline(initial_state)` helper for external callers.

### `backend/agents/state.py`
Defines the shared `PipelineState` TypedDict used across all agents. Fields: `ticker`, `options_data`, `metrics`, `market_sentiment`, `tradability_score`, `errors`.

### `tests/agents/__init__.py`
Empty init for the agents test package.

### `tests/agents/test_agent_placeholders.py`
Unit tests verifying each agent stub is callable, accepts state, and returns the expected state shape.

### `tests/agents/test_workflow.py`
Integration test verifying the compiled LangGraph workflow can be invoked end-to-end with a minimal state and returns a result without raising.

---

## Files to Modify

### `backend/agents/__init__.py`
Export the four agent classes and the `run_pipeline` helper so they are importable from `backend.agents`.

### `backend/requirements.txt`
Add `langgraph` (and `langchain-core` if not already present) as dependencies.

---

## Implementation Steps

1. **Add dependencies** — Add `langgraph>=0.1.0` and `langchain-core>=0.1.0` to `backend/requirements.txt`.

2. **Create `backend/agents/state.py`** — Define `PipelineState` as a `TypedDict` with keys: `ticker: str`, `options_data: Optional[Any]`, `metrics: Optional[Any]`, `market_sentiment: Optional[Any]`, `tradability_score: Optional[Any]`, `errors: list[str]`.

3. **Create each agent module** — Each agent follows this pattern:
   ```python
   from backend.agents.state import PipelineState

   class OptionsDataAgent:
       """Fetches raw options chain data for the given ticker.
       Logic to be implemented in a follow-up story.
       """

       def run(self, state: PipelineState) -> PipelineState:
           """Placeholder: returns state unchanged with options_data=None."""
           return {**state, "options_data": None}

       def __call__(self, state: PipelineState) -> PipelineState:
           return self.run(state)
   ```

4. **Create `backend/agents/workflow.py`** — Build the LangGraph `StateGraph`:
   ```python
   from langgraph.graph import StateGraph, END
   from backend.agents.state import PipelineState
   from backend.agents.options_data_agent import OptionsDataAgent
   from backend.agents.metrics_agent import MetricsAgent
   from backend.agents.tradability_agent import TradabilityAgent

   options_data_agent = OptionsDataAgent()
   metrics_agent = MetricsAgent()
   tradability_agent = TradabilityAgent()

   graph = StateGraph(PipelineState)
   graph.add_node("options_data", options_data_agent)
   graph.add_node("metrics", metrics_agent)
   graph.add_node("tradability", tradability_agent)

   graph.set_entry_point("options_data")
   graph.add_edge("options_data", "metrics")
   graph.add_edge("metrics", "tradability")
   graph.add_edge("tradability", END)

   app = graph.compile()

   def run_pipeline(ticker: str) -> PipelineState:
       initial_state: PipelineState = {
           "ticker": ticker,
           "options_data": None,
           "metrics": None,
           "market_sentiment": None,
           "tradability_score": None,
           "errors": [],
       }
       return app.invoke(initial_state)
   ```

5. **Update `backend/agents/__init__.py`** — Export all four agent classes and `run_pipeline`.

6. **Write tests** — See test strategy below.

---

## Test Strategy

### Unit Tests (`tests/agents/test_agent_placeholders.py`)
- Each agent can be instantiated without error.
- Each agent's `run()` method accepts a valid `PipelineState` and returns a dict.
- Each agent returns the expected stub key (e.g., `options_data=None`) without mutating other state keys.
- Each agent is callable (i.e., `__call__` delegates to `run`).

### Integration Tests (`tests/agents/test_workflow.py`)
- `run_pipeline("AAPL")` completes without raising an exception.
- The returned state contains all expected keys: `ticker`, `options_data`, `metrics`, `market_sentiment`, `tradability_score`, `errors`.
- The `ticker` value is preserved through the pipeline.
- The compiled `app` graph is not `None`.

---

## Edge Cases to Handle

- `MarketSentimentAgent` is not in the main pipeline flow — scaffold it as a standalone node but do not wire it into the graph yet. Add a TODO comment indicating it will be integrated in a follow-up.
- Ensure `PipelineState` uses `Optional` types so downstream agents can safely check for `None` values from upstream stubs.
- The `errors` field should default to an empty list to allow agents to append errors non-destructively in future implementations.
