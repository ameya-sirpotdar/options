from fastapi import APIRouter, HTTPException
from backend.models.poll import PollOptionsRequest, PollOptionsResponse
from backend.services.polling_service import PollingService

router = APIRouter()
_polling_service = PollingService()


@router.post("/poll/options", response_model=PollOptionsResponse, status_code=200)
async def poll_options(request: PollOptionsRequest) -> PollOptionsResponse:
    """
    On-demand options polling endpoint.

    Accepts a list of tickers and invokes the options agent workflow
    to fetch and process options data for each ticker.

    Returns a summary of the polling results including per-ticker status.
    """
    try:
        result = await _polling_service.poll(request.tickers)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error during options polling") from exc

    return result