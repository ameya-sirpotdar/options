from fastapi import APIRouter, HTTPException, Query
from typing import List
from backend.models.poll import PollOptionsResponse
from backend.services.polling_service import PollingService

router = APIRouter()
polling_service = PollingService()


@router.get("/options-chain", response_model=PollOptionsResponse)
async def get_options_chain(tickers: List[str] = Query(...)):
    try:
        results = polling_service.poll_options(tickers)
        return PollOptionsResponse(tickers=tickers, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
