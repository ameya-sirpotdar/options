from backend.agents.market_sentiment_agent import MarketSentimentAgent


def test_instantiation():
    agent = MarketSentimentAgent()
    assert isinstance(agent, MarketSentimentAgent)


def test_has_run_method():
    agent = MarketSentimentAgent()
    assert hasattr(agent, "run")
    assert callable(agent.run)


def test_run_returns_state_unchanged():
    agent = MarketSentimentAgent()
    state = {"ticker": "AAPL", "sentiment": None}
    result = agent.run(state)
    assert result == state


def test_run_returns_same_object():
    agent = MarketSentimentAgent()
    state = {"ticker": "TSLA"}
    result = agent.run(state)
    assert result is state


def test_run_with_empty_state():
    agent = MarketSentimentAgent()
    state = {}
    result = agent.run(state)
    assert result == {"market_sentiment": None}


def test_run_with_complex_state():
    agent = MarketSentimentAgent()
    state = {
        "ticker": "NVDA",
        "sentiment": {"score": 0.8, "label": "bullish"},
        "timestamp": "2024-01-01T00:00:00Z",
    }
    result = agent.run(state)
    assert result == state