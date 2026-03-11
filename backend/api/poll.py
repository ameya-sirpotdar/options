from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import ValidationError
from backend.models.poll import OptionsChainRequest, PollOptionsResponse
from backend.services.polling_service import PollingService

router = APIRouter()


class OptionsChainRequestDep:
    def __init__(self, tickers: list[str] = Query(..., description="Ticker symbols")):
        try:
            validated = OptionsChainRequest(tickers=tickers)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        self.tickers = validated.tickers


@router.get("/options-chain", response_model=PollOptionsResponse)
async def get_options_chain(
    http_request: Request,
    response: Response,
    request: OptionsChainRequestDep = Depends(),
):
    response.headers["Cache-Control"] = "no-store"
    try:
        schwab_client = getattr(http_request.app.state, "schwab_client", None)
        if schwab_client is None:
            raise HTTPException(status_code=503, detail="Schwab client not available")
        polling_service = PollingService(schwab_client=schwab_client)
        results = polling_service.poll_options(request.tickers)
        return PollOptionsResponse(tickers=request.tickers, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
