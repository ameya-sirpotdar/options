from fastapi import APIRouter, HTTPException
from backend.models.poll import PollOptionsRequest, PollOptionsResponse
from backend.services.polling_service import PollingService

router = APIRouter()
polling_service = PollingService()


@router.post("/poll/options", response_model=PollOptionsResponse)
async def poll_options(request: PollOptionsRequest):
    try:
        result = await polling_service.poll_options(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))