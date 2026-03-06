import logging
from typing import Any

logger = logging.getLogger(__name__)


def run_options_poll(tickers: list[str]) -> dict[str, Any]:
    """
    LangGraph agent stub for polling options data for the given tickers.

    Parameters
    ----------
    tickers:
        A list of normalised (uppercase) ticker symbols to poll.

    Returns
    -------
    dict[str, Any]
        A mapping of ticker symbol to its options data payload.
        In this stub implementation each ticker receives a placeholder
        dictionary that downstream services or tests can replace with
        real data once the LangGraph graph is wired up.

    Raises
    ------
    RuntimeError
        Re-raised from any unexpected exception encountered during the
        agent run so that callers can handle failures uniformly.
    """
    logger.info("run_options_poll called with tickers=%s", tickers)

    try:
        results: dict[str, Any] = {}

        for ticker in tickers:
            logger.debug("Polling options data for ticker=%s", ticker)
            # Stub payload – replace with real LangGraph node invocation.
            results[ticker] = {
                "ticker": ticker,
                "status": "ok",
                "options": [],
            }

        logger.info("run_options_poll completed successfully for %d ticker(s)", len(tickers))
        return results

    except Exception as exc:
        logger.exception("run_options_poll encountered an unexpected error: %s", exc)
        raise RuntimeError(
            f"Options polling agent failed: {exc}"
        ) from exc