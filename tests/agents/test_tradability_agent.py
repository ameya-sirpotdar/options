tests/agents/test_tradability_agent.py
from backend.agents.tradability_agent import TradabilityAgent


def test_tradability_agent_instantiation():
    agent = TradabilityAgent()
    assert agent is not None


def test_tradability_agent_has_run_method():
    agent = TradabilityAgent()
    assert hasattr(agent, "run")
    assert callable(agent.run)


def test_tradability_agent_run_returns_state_unchanged():
    agent = TradabilityAgent()
    state = {
        "ticker": "AAPL",
        "metrics": {"iv_rank": 45.0, "delta": 0.3},
        "tradability_score": None,
    }
    result = agent.run(state)
    assert result == state


def test_tradability_agent_run_returns_dict():
    agent = TradabilityAgent()
    state = {"ticker": "TSLA"}
    result = agent.run(state)
    assert isinstance(result, dict)


def test_tradability_agent_run_does_not_mutate_state():
    agent = TradabilityAgent()
    state = {"ticker": "MSFT", "tradability_score": None}
    original_state = state.copy()
    agent.run(state)
    assert state == original_state


def test_tradability_agent_run_with_empty_state():
    agent = TradabilityAgent()
    state = {}
    result = agent.run(state)
    assert result == {}


def test_tradability_agent_run_preserves_all_keys():
    agent = TradabilityAgent()
    state = {
        "ticker": "NVDA",
        "sentiment": "bullish",
        "options_data": {"calls": [], "puts": []},
        "metrics": {"iv_rank": 60.0},
        "tradability_score": None,
        "recommendation": None,
    }
    result = agent.run(state)
    for key in state:
        assert key in result