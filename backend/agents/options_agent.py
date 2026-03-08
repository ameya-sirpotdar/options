import logging
from typing import Any, Dict, List, Optional

from backend.services.schwab_client import SchwabClient

logger = logging.getLogger(__name__)


def run_options_poll(
    tickers: List[str],
    schwab_client: Optional[SchwabClient] = None,
) -> Dict[str, Any]:
    """
    LangGraph agent stub for polling options data for the given tickers.
    Returns a dict mapping ticker symbol to its raw options chain payload
    as returned by the Schwab API (or an empty stub when no client is provided).

    Parameters
    ----------
    tickers:
        List of underlying ticker symbols to poll.
    schwab_client:
        An initialised SchwabClient instance.  When *None* the agent falls
        back to returning empty stub payloads so that the rest of the
        pipeline can still exercise its persistence / logging logic in
        development / test environments.
    """
    logger.info("run_options_poll called with tickers=%s", tickers)
    try:
        results: Dict[str, Any] = {}
        for ticker in tickers:
            logger.debug("Polling options data for ticker=%s", ticker)
            if schwab_client is not None:
                try:
                    payload = schwab_client.get_options_chain(ticker)
                    results[ticker] = payload
                    logger.debug(
                        "Received options chain for ticker=%s, keys=%s",
                        ticker,
                        list(payload.keys()) if isinstance(payload, dict) else "n/a",
                    )
                except Exception as client_exc:
                    logger.warning(
                        "SchwabClient.get_options_chain failed for ticker=%s: %s",
                        ticker,
                        client_exc,
                    )
                    results[ticker] = {
                        "ticker": ticker,
                        "calls": [],
                        "puts": [],
                        "error": str(client_exc),
                    }
            else:
                # Stub payload used when no real client is available.
                results[ticker] = {
                    "ticker": ticker,
                    "calls": [],
                    "puts": [],
                }

        logger.info("run_options_poll completed for %d ticker(s)", len(tickers))
        return results
    except Exception as exc:
        logger.exception("run_options_poll failed: %s", exc)
        raise RuntimeError(f"Options polling agent failed: {exc}") from exc
