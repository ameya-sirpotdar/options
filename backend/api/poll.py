from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import ValidationError
from backend.models.poll import OptionsChainRequest, PollOptionsResponse
from backend.services.polling_service import PollingService

router = APIRouter()
polling_service = PollingService()


class OptionsChainRequestDep:
    def __init__(self, tickers: list[str] = Query(..., description="Ticker symbols")):
        try:
            validated = OptionsChainRequest(tickers=tickers)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        self.tickers = validated.tickers


@router.get("/options-chain", response_model=PollOptionsResponse)
async def get_options_chain(response: Response, request: OptionsChainRequestDep = Depends()):
    response.headers["Cache-Control"] = "no-store"
    try:
        results = polling_service.poll_options(request.tickers)
        return PollOptionsResponse(tickers=request.tickers, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
