import pytest
from backend.agents.tradability_agent import TradabilityAgent
from backend.services.trades_comparison_service import TradesComparisonService


# ---------------------------------------------------------------------------
# Instantiation & interface
# ---------------------------------------------------------------------------

def test_tradability_agent_instantiation():
    agent = TradabilityAgent()
    assert agent is not None


def test_tradability_agent_has_run_method():
    agent = TradabilityAgent()
    assert hasattr(agent, "run")
    assert callable(agent.run)


# ---------------------------------------------------------------------------
# Return type & key presence
# ---------------------------------------------------------------------------

def test_tradability_agent_run_returns_dict():
    agent = TradabilityAgent()
    state = {"ticker": "TSLA", "trades": []}
    result = agent.run(state)
    assert isinstance(result, dict)


def test_tradability_agent_run_with_empty_state():
    agent = TradabilityAgent()
    state = {}
    result = agent.run(state)
    assert isinstance(result, dict)


def test_tradability_agent_run_preserves_all_input_keys():
    agent = TradabilityAgent()
    state = {
        "ticker": "NVDA",
        "sentiment": "bullish",
        "trades": [],
        "errors": [],
    }
    result = agent.run(state)
    for key in state:
        assert key in result


# ---------------------------------------------------------------------------
# Tradability score population
# ---------------------------------------------------------------------------

def test_tradability_agent_populates_tradability_score():
    """Agent must write a tradability_score into the state."""
    agent = TradabilityAgent()
    state = {
        "ticker": "AAPL",
        "trades": [
            {
                "symbol": "AAPL",
                "strike": 150.0,
                "expiration": "2025-01-17",
                "option_type": "call",
                "bid": 2.5,
                "ask": 2.7,
                "delta": 0.45,
                "iv": 0.30,
            }
        ],
        "errors": [],
    }
    result = agent.run(state)
    assert "tradability_score" in result


def test_tradability_agent_score_is_numeric_or_none():
    """tradability_score must be a float/int or None — never an unexpected type."""
    agent = TradabilityAgent()
    state = {
        "ticker": "MSFT",
        "trades": [
            {
                "symbol": "MSFT",
                "strike": 300.0,
                "expiration": "2025-02-21",
                "option_type": "put",
                "bid": 3.0,
                "ask": 3.2,
                "delta": -0.35,
                "iv": 0.25,
            }
        ],
        "errors": [],
    }
    result = agent.run(state)
    score = result.get("tradability_score")
    assert score is None or isinstance(score, (int, float))


def test_tradability_agent_score_with_no_trades():
    """When trades list is empty the agent should still return a valid state."""
    agent = TradabilityAgent()
    state = {"ticker": "GOOG", "trades": [], "errors": []}
    result = agent.run(state)
    assert "tradability_score" in result


# ---------------------------------------------------------------------------
# State immutability
# ---------------------------------------------------------------------------

def test_tradability_agent_run_does_not_mutate_input_state():
    agent = TradabilityAgent()
    state = {"ticker": "MSFT", "trades": [], "tradability_score": None}
    original_state = state.copy()
    agent.run(state)
    assert state == original_state


# ---------------------------------------------------------------------------
# Error preservation
# ---------------------------------------------------------------------------

BASE_STATE = {
    "ticker": "AAPL",
    "trades": [],
    "errors": [],
}


def test_tradability_agent_preserves_other_state_keys():
    agent = TradabilityAgent()
    sample_state = {
        **BASE_STATE,
        "market_sentiment": None,
        "tradability_score": None,
    }
    result = agent.run(sample_state)
    assert result["ticker"] == sample_state["ticker"]
    assert result["trades"] == sample_state["trades"]
    assert result["market_sentiment"] == sample_state["market_sentiment"]


def test_preserves_existing_errors():
    agent = TradabilityAgent()
    state = {**BASE_STATE, "errors": ["upstream error"]}
    result = agent.run(state)
    assert "upstream error" in result["errors"], "Agent must not clear pre-existing errors"


# ---------------------------------------------------------------------------
# Integration with TradesComparisonService
# ---------------------------------------------------------------------------

def test_tradability_agent_uses_trades_comparison_service(monkeypatch):
    """TradabilityAgent must delegate scoring to TradesComparisonService."""
    called_with = {}

    def fake_score(self, trades):
        called_with["trades"] = trades
        return 0.75

    monkeypatch.setattr(TradesComparisonService, "compute_tradability_score", fake_score)

    agent = TradabilityAgent()
    trade = {
        "symbol": "AAPL",
        "strike": 150.0,
        "expiration": "2025-01-17",
        "option_type": "call",
        "bid": 2.5,
        "ask": 2.7,
        "delta": 0.45,
        "iv": 0.30,
    }
    state = {"ticker": "AAPL", "trades": [trade], "errors": []}
    result = agent.run(state)

    assert called_with.get("trades") == [trade], (
        "TradabilityAgent must pass trades to TradesComparisonService.compute_tradability_score"
    )
    assert result["tradability_score"] == 0.75