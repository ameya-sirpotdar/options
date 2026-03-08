tests/agents/test_options_data_agent.py
from backend.agents.options_data_agent import OptionsDataAgent


def test_options_data_agent_instantiation():
    agent = OptionsDataAgent()
    assert agent is not None


def test_options_data_agent_has_run_method():
    agent = OptionsDataAgent()
    assert hasattr(agent, "run")
    assert callable(agent.run)


def test_options_data_agent_run_returns_state_unchanged():
    agent = OptionsDataAgent()
    state = {"ticker": "AAPL", "expiration": "2024-01-19"}
    result = agent.run(state)
    assert result == state


def test_options_data_agent_run_with_empty_state():
    agent = OptionsDataAgent()
    state = {}
    result = agent.run(state)
    assert result == {}


def test_options_data_agent_run_preserves_all_keys():
    agent = OptionsDataAgent()
    state = {
        "ticker": "TSLA",
        "expiration": "2024-02-16",
        "strike": 250.0,
        "option_type": "call",
    }
    result = agent.run(state)
    assert set(result.keys()) == set(state.keys())
    for key in state:
        assert result[key] == state[key]