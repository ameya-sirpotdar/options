"""LangGraph StateGraph wiring for the options analysis pipeline."""

from langgraph.graph import StateGraph, END

from backend.agents.state import PipelineState
from backend.agents.market_sentiment_agent import MarketSentimentAgent
from backend.agents.metrics_agent import MetricsAgent
from backend.agents.options_data_agent import OptionsDataAgent
from backend.agents.tradability_agent import TradabilityAgent

# Instantiate agents once at module level.
_options_data_agent = OptionsDataAgent()
_metrics_agent = MetricsAgent()
_market_sentiment_agent = MarketSentimentAgent()
_tradability_agent = TradabilityAgent()


def _run_options_data(state: PipelineState) -> PipelineState:
    """Node: fetch options data."""
    return _options_data_agent.run(state)


def _run_metrics(state: PipelineState) -> PipelineState:
    """Node: compute metrics."""
    return _metrics_agent.run(state)


def _run_market_sentiment(state: PipelineState) -> PipelineState:
    """Node: assess market sentiment."""
    return _market_sentiment_agent.run(state)


def _run_tradability(state: PipelineState) -> PipelineState:
    """Node: evaluate tradability."""
    return _tradability_agent.run(state)


def _build_graph() -> StateGraph:
    """Assemble and compile the LangGraph StateGraph."""
    graph = StateGraph(PipelineState)

    graph.add_node("options_data", _run_options_data)
    graph.add_node("metrics", _run_metrics)
    graph.add_node("market_sentiment", _run_market_sentiment)
    graph.add_node("tradability", _run_tradability)

    graph.set_entry_point("options_data")
    graph.add_edge("options_data", "metrics")
    graph.add_edge("metrics", "market_sentiment")
    graph.add_edge("market_sentiment", "tradability")
    graph.add_edge("tradability", END)

    return graph.compile()


# Compiled graph, ready for invocation.
_compiled_graph = _build_graph()


def run_pipeline(ticker: str) -> PipelineState:
    """Run the full options analysis pipeline for *ticker*.

    Parameters
    ----------
    ticker:
        The equity ticker symbol to analyse (e.g. ``"AAPL"``).)

    Returns
    -------
    PipelineState
        The final pipeline state after all agents have run.
    """
    initial_state: PipelineState = {
        "ticker": ticker,
        "options_data": None,
        "metrics": None,
        "market_sentiment": None,
        "tradability_score": None,
        "errors": [],
    }
    return _compiled_graph.invoke(initial_state)
