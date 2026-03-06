from typing import Any

from backend.agents.options_agent import run_options_agent
from backend.models.poll import PollOptionsRequest, PollOptionsResponse


async def poll_options(request: PollOptionsRequest) -> PollOptionsResponse:
    """
    Service layer for the on-demand options polling endpoint.

    Normalises the incoming request, delegates to the LangGraph options agent,
    and wraps the result in a validated response model.

    Parameters
    ----------
    request:
        Validated and normalised poll-options request containing one or more
        ticker symbols.

    Returns
    -------
    PollOptionsResponse
        A response model containing the per-ticker results returned by the
        agent workflow.
    """
    results: dict[str, Any] = await run_options_agent(tickers=request.tickers)

    return PollOptionsResponse(
        tickers=request.tickers,
        results=results,
    )