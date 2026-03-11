from fastapi import APIRouter, Depends, HTTPException, Response
from backend.models.poll import OptionsChainRequest, PollOptionsResponse
from backend.services.polling_service import PollingService

router = APIRouter()
polling_service = PollingService()


@router.get("/options-chain", response_model=PollOptionsResponse)
async def get_options_chain(request: OptionsChainRequest = Depends(), response: Response = None):
    response.headers["Cache-Control"] = "no-store"
    try:
        results = polling_service.poll_options(params.tickers)
        return PollOptionsResponse(tickers=params.tickers, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
