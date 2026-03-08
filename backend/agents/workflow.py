"""LangGraph StateGraph wiring for the options analysis pipeline."""

from typing import Optional

from langgraph.graph import StateGraph, END

from backend.agents.state import PipelineState
from backend.agents.market_sentiment_agent import MarketSentimentAgent
from backend.agents.metrics_agent import MetricsAgent
from backend.agents.options_data_agent import OptionsDataAgent
from backend.agents.tradability_agent import TradabilityAgent

# Lazy-initialised compiled graph; built on first call to _get_app().
_app = None


def _run_options_data(state: PipelineState) -> PipelineState:
    """Node: fetch options data."""
    return OptionsDataAgent().run(state)


def _run_metrics(state: PipelineState) -> PipelineState:
    """Node: compute metrics."""
    return MetricsAgent().run(state)


def _run_market_sentiment(state: PipelineState) -> PipelineState:
    """Node: assess market sentiment.

    # TODO(#XX): MarketSentimentAgent is scaffolded but not yet wired to a real
    # data source.  It will be connected in a follow-up issue.
    """
    return MarketSentimentAgent().run(state)


def _run_tradability(state: PipelineState) -> PipelineState:
    """Node: evaluate tradability."""
    return TradabilityAgent().run(state)


def _get_app():
    """Return the compiled LangGraph application, building it on first call."""
    global _app
    if _app is None:
        graph = StateGraph(PipelineState)

        graph.add_node("options_data", _run_options_data)
        graph.add_node("metrics", _run_metrics)
        # TODO(#XX): market_sentiment node is stubbed; wire real implementation
        # in the follow-up issue before enabling in production.
        graph.add_node("market_sentiment", _run_market_sentiment)
        graph.add_node("tradability", _run_tradability)

        graph.set_entry_point("options_data")
        graph.add_edge("options_data", "metrics")
        graph.add_edge("metrics", "market_sentiment")
        graph.add_edge("market_sentiment", "tradability")
        graph.add_edge("tradability", END)

        _app = graph.compile()
    return _app


def run_pipeline(
    ticker: str,
    initial_state: Optional[PipelineState] = None,
) -> PipelineState:
    """Run the full options analysis pipeline for *ticker*.

    Parameters
    ----------
    ticker:
        The equity ticker symbol to analyse (e.g. ``"AAPL"``).
    initial_state:
        Optional pre-populated state mapping.  When provided it is used as-is
        (useful for testing or partial re-runs).  When omitted a default blank
        state is constructed from *ticker*.

    Returns
    -------
    PipelineState
        The final pipeline state after all agents have run.  If the graph
        raises an unexpected exception the returned state will have a
        non-empty ``errors`` list describing the failure.
    """
    state: PipelineState = initial_state or {
        "ticker": ticker,
        "options_data": None,
        "metrics": None,
        "market_sentiment": None,
        "tradability_score": None,
        "errors": [],
    }
    try:
        return _get_app().invoke(state)
    except Exception as exc:  # noqa: BLE001
        return {**state, "errors": [str(exc)]}
