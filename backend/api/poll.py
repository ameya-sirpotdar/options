from fastapi import APIRouter, Depends, HTTPException, Query, Response
from typing import List
from backend.models.poll import OptionsChainRequest, PollOptionsResponse
from backend.services.polling_service import PollingService

router = APIRouter()
polling_service = PollingService()


class OptionsChainRequestDep:
    def __init__(self, tickers: List[str] = Query(..., description="Ticker symbols")):
        request = OptionsChainRequest(tickers=tickers)
        self.tickers = request.tickers


@router.get("/options-chain", response_model=PollOptionsResponse)
async def get_options_chain(request: OptionsChainRequestDep = Depends(), response: Response):
    response.headers["Cache-Control"] = "no-store"
    try:
        results = polling_service.poll_options(request.tickers)
        return PollOptionsResponse(tickers=request.tickers, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
