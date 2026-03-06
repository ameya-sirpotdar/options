from __future__ import annotations

import logging
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    tickers: list[str]
    results: dict[str, Any]
    errors: dict[str, str]


def _fetch_options_node(state: AgentState) -> AgentState:
    """
    Stub node that simulates fetching options data for each ticker.

    In production this node would call a market-data provider (e.g. CBOE,
    Polygon, Yahoo Finance) and store structured options chains in
    ``state["results"]``.
    """
    tickers = state.get("tickers", [])
    results: dict[str, Any] = {}
    errors: dict[str, str] = {}

    for ticker in tickers:
        try:
            logger.debug("Fetching options data for ticker: %s", ticker)
            # TODO: replace stub with real market-data call
            results[ticker] = {
                "ticker": ticker,
                "status": "ok",
                "options_chain": [],
            }
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to fetch options for %s", ticker)
            errors[ticker] = str(exc)

    return AgentState(
        tickers=tickers,
        results=results,
        errors=errors,
    )


def _analyse_options_node(state: AgentState) -> AgentState:
    """
    Stub node that would run quantitative analysis (Greeks, IV surface, etc.)
    over the fetched options chains.
    """
    results = state.get("results", {})
    errors = state.get("errors", {})

    for ticker, payload in results.items():
        try:
            logger.debug("Analysing options data for ticker: %s", ticker)
            # TODO: replace stub with real analysis logic
            payload["analysis"] = {"iv_rank": None, "put_call_ratio": None}
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to analyse options for %s", ticker)
            errors[ticker] = str(exc)

    return AgentState(
        tickers=state["tickers"],
        results=results,
        errors=errors,
    )


def build_options_agent() -> StateGraph:
    """
    Construct and compile the LangGraph options-polling agent.

    Graph topology
    --------------
    fetch_options --> analyse_options --> END
    """
    graph = StateGraph(AgentState)

    graph.add_node("fetch_options", _fetch_options_node)
    graph.add_node("analyse_options", _analyse_options_node)

    graph.set_entry_point("fetch_options")
    graph.add_edge("fetch_options", "analyse_options")
    graph.add_edge("analyse_options", END)

    return graph.compile()


def run_options_agent(tickers: list[str]) -> dict[str, Any]:
    """
    Execute the options agent for the given list of tickers and return the
    final state.

    Parameters
    ----------
    tickers:
        Normalised (upper-cased, stripped) ticker symbols.

    Returns
    -------
    dict
        The final ``AgentState`` as a plain dictionary, containing:
        - ``tickers``  – the input list
        - ``results``  – per-ticker options payload
        - ``errors``   – per-ticker error messages (empty on full success)
    """
    if not tickers:
        logger.warning("run_options_agent called with an empty ticker list")
        return AgentState(tickers=[], results={}, errors={})

    agent = build_options_agent()

    initial_state: AgentState = AgentState(
        tickers=tickers,
        results={},
        errors={},
    )

    logger.info("Starting options agent for tickers: %s", tickers)
    final_state: AgentState = agent.invoke(initial_state)
    logger.info("Options agent completed for tickers: %s", tickers)

    return dict(final_state)