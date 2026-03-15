from backend.agents.metrics_agent import MetricsAgent


def test_metrics_agent_instantiation():
    agent = MetricsAgent()
    assert agent is not None


def test_metrics_agent_has_run_method():
    agent = MetricsAgent()
    assert hasattr(agent, "run")
    assert callable(agent.run)


def test_metrics_agent_run_returns_state_unchanged():
    agent = MetricsAgent()
    state = {"ticker": "AAPL", "expiration": "2024-01-19", "metrics": {}}
    result = agent.run(state)
    assert result == state


def test_metrics_agent_run_returns_same_object():
    agent = MetricsAgent()
    state = {"ticker": "TSLA"}
    result = agent.run(state)
    assert result is state


def test_metrics_agent_run_with_empty_state():
    agent = MetricsAgent()
    state = {}
    result = agent.run(state)
    assert result == {"metrics": None}


def test_metrics_agent_run_with_complex_state():
    agent = MetricsAgent()
    state = {
        "ticker": "SPY",
        "expiration": "2024-03-15",
        "options_chain": [{"strike": 450, "iv": 0.25}],
        "metrics": {"iv_rank": None, "iv_percentile": None},
        "sentiment": "bullish",
    }
    result = agent.run(state)
    assert result == state