from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from backend.models.poll import OptionsChainRequest, PollOptionsResponse
from backend.services.polling_service import PollingService

router = APIRouter()
polling_service = PollingService()


class OptionsChainDep:
    def __init__(self, tickers: List[str] = Query(..., min_length=1)):
        validated = OptionsChainRequest(tickers=tickers)
        self.tickers = validated.tickers


@router.get("/options-chain", response_model=PollOptionsResponse)
async def get_options_chain(params: OptionsChainDep = Depends(), response: Response = None):
    if response is not None:
        response.headers["Cache-Control"] = "no-store"
    try:
        results = polling_service.poll_options(request.tickers)
        return PollOptionsResponse(tickers=request.tickers, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
