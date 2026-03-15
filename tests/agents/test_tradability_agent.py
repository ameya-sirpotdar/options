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


def test_tradability_agent_preserves_other_state_keys():
    agent = TradabilityAgent()
    sample_state = {
        "ticker": "AAPL",
        "options_data": {"calls": [], "puts": []},
        "metrics": {"iv_rank": 45.0, "delta": 0.3},
        "market_sentiment": None,
        "tradability_score": None,
        "errors": [],
    }
    result = agent.run(sample_state)
    assert result["ticker"] == sample_state["ticker"]
    assert result["options_data"] == sample_state["options_data"]
    assert result["metrics"] == sample_state["metrics"]
    assert result["market_sentiment"] == sample_state["market_sentiment"]
    assert result["errors"] == sample_state["errors"]


BASE_STATE = {
    "ticker": "AAPL",
    "options_data": {"calls": [], "puts": []},
    "metrics": {"iv_rank": 45.0, "delta": 0.3},
    "market_sentiment": None,
    "tradability_score": None,
    "errors": [],
}


def test_preserves_existing_errors():
    agent = TradabilityAgent()
    state = {**BASE_STATE, "errors": ["upstream error"]}
    result = agent.run(state)
    assert "upstream error" in result["errors"], "Agent must not clear pre-existing errors"