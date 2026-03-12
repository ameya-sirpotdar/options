from unittest.mock import patch, MagicMock

from backend.agents.options_data_agent import OptionsDataAgent
from backend.models.options_data import OptionsData


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


def test_options_data_agent_preserves_errors():
    agent = OptionsDataAgent()
    state_with_errors = {
        "ticker": "AAPL",
        "options_data": None,
        "metrics": None,
        "market_sentiment": None,
        "tradability_score": None,
        "errors": ["prior error"],
    }
    result = agent.run(state_with_errors)
    assert result["errors"] == ["prior error"]


def test_does_not_mutate_input_state():
    import copy
    agent = OptionsDataAgent()
    original = {
        "ticker": "AAPL",
        "options_data": None,
        "metrics": None,
        "market_sentiment": None,
        "tradability_score": None,
        "errors": [],
    }
    state_copy = copy.deepcopy(original)
    agent.run(original)
    assert original == state_copy, "Agent must not mutate the input state dict"


# ---------------------------------------------------------------------------
# CCP enrichment integration tests
# ---------------------------------------------------------------------------

def _make_put_options_data(expiration: str = "2025-12-19") -> list[OptionsData]:
    """Return a minimal list of put OptionsData records for testing."""
    return [
        OptionsData(
            ticker="AAPL",
            expiration=expiration,
            strike=150.0,
            option_type="put",
            bid=3.50,
            ask=3.70,
            last=3.60,
            volume=100,
            open_interest=500,
            implied_volatility=0.25,
        ),
        OptionsData(
            ticker="AAPL",
            expiration=expiration,
            strike=145.0,
            option_type="put",
            bid=2.10,
            ask=2.30,
            last=2.20,
            volume=80,
            open_interest=300,
            implied_volatility=0.22,
        ),
    ]


def test_agent_enriches_put_options_with_annualized_roi():
    """Put options returned in state must have annualized_roi populated."""
    agent = OptionsDataAgent()
    put_options = _make_put_options_data()

    with patch(
        "backend.agents.options_data_agent.enrich_put_options_with_roi",
        wraps=lambda opts: [
            opt.model_copy(update={"annualized_roi": 0.15, "days_to_expiration": 90})
            for opt in opts
        ],
    ) as mock_enrich:
        state = {"ticker": "AAPL", "options_data": put_options}
        result = agent.run(state)

        mock_enrich.assert_called_once_with(put_options)
        enriched = result["options_data"]
        assert enriched is not None
        for opt in enriched:
            assert opt.annualized_roi == 0.15
            assert opt.days_to_expiration == 90


def test_agent_calls_enrich_with_put_options_list():
    """enrich_put_options_with_roi must receive the options_data list."""
    agent = OptionsDataAgent()
    put_options = _make_put_options_data()

    with patch(
        "backend.agents.options_data_agent.enrich_put_options_with_roi"
    ) as mock_enrich:
        mock_enrich.return_value = put_options  # return unchanged for simplicity
        state = {"ticker": "AAPL", "options_data": put_options}
        agent.run(state)

        mock_enrich.assert_called_once_with(put_options)


def test_agent_replaces_options_data_with_enriched_list():
    """The state returned must contain the enriched list, not the original."""
    agent = OptionsDataAgent()
    put_options = _make_put_options_data()
    enriched_options = [
        opt.model_copy(update={"annualized_roi": 0.20, "days_to_expiration": 45})
        for opt in put_options
    ]

    with patch(
        "backend.agents.options_data_agent.enrich_put_options_with_roi",
        return_value=enriched_options,
    ):
        state = {"ticker": "AAPL", "options_data": put_options}
        result = agent.run(state)

        assert result["options_data"] is enriched_options


def test_agent_skips_enrichment_when_options_data_is_none():
    """When options_data is None the enrichment function must not be called."""
    agent = OptionsDataAgent()

    with patch(
        "backend.agents.options_data_agent.enrich_put_options_with_roi"
    ) as mock_enrich:
        state = {"ticker": "AAPL", "options_data": None}
        result = agent.run(state)

        mock_enrich.assert_not_called()
        assert result["options_data"] is None


def test_agent_skips_enrichment_when_options_data_missing_from_state():
    """When the key is absent entirely, enrichment must not be called."""
    agent = OptionsDataAgent()

    with patch(
        "backend.agents.options_data_agent.enrich_put_options_with_roi"
    ) as mock_enrich:
        state = {"ticker": "AAPL"}
        agent.run(state)

        mock_enrich.assert_not_called()


def test_agent_skips_enrichment_when_options_data_is_empty_list():
    """An empty list should be passed through without calling enrichment."""
    agent = OptionsDataAgent()

    with patch(
        "backend.agents.options_data_agent.enrich_put_options_with_roi"
    ) as mock_enrich:
        state = {"ticker": "AAPL", "options_data": []}
        result = agent.run(state)

        mock_enrich.assert_not_called()
        assert result["options_data"] == []


def test_agent_enrichment_does_not_affect_other_state_keys():
    """Enrichment must only touch options_data; all other keys stay intact."""
    agent = OptionsDataAgent()
    put_options = _make_put_options_data()
    enriched_options = [
        opt.model_copy(update={"annualized_roi": 0.10, "days_to_expiration": 30})
        for opt in put_options
    ]

    with patch(
        "backend.agents.options_data_agent.enrich_put_options_with_roi",
        return_value=enriched_options,
    ):
        state = {
            "ticker": "AAPL",
            "options_data": put_options,
            "metrics": {"some": "metric"},
            "errors": [],
        }
        result = agent.run(state)

        assert result["ticker"] == "AAPL"
        assert result["metrics"] == {"some": "metric"}
        assert result["errors"] == []


def test_agent_enrichment_preserves_existing_errors():
    """Errors already in state must survive the enrichment step."""
    agent = OptionsDataAgent()
    put_options = _make_put_options_data()

    with patch(
        "backend.agents.options_data_agent.enrich_put_options_with_roi",
        return_value=put_options,
    ):
        state = {
            "ticker": "AAPL",
            "options_data": put_options,
            "errors": ["prior error"],
        }
        result = agent.run(state)

        assert "prior error" in result["errors"]