from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from backend.models.tradability import TradabilityScore
from backend.services.tradability_service import TradabilityService

router = APIRouter(prefix="/trades", tags=["trades"])


def get_tradability_service() -> TradabilityService:
    return TradabilityService()


@router.get("/best", response_model=TradabilityScore)
async def get_best_trade(
    top_n: Optional[int] = Query(default=10, ge=1, le=100, description="Number of top candidates to consider"),
    min_score: Optional[float] = Query(default=0.0, ge=0.0, le=1.0, description="Minimum tradability score threshold"),
    service: TradabilityService = Depends(get_tradability_service),
):
    """
    Returns the single best trade candidate based on the Tradability Index.

    The tradability score is computed as a weighted combination of:
    - Liquidity score
    - Volatility score
    - Momentum score
    - Spread score
    - Volume score
    """
    try:
        best = service.get_best_trade(top_n=top_n, min_score=min_score)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error while computing tradability scores") from exc

    if best is None:
        raise HTTPException(
            status_code=404,
            detail="No trade candidates meet the minimum score threshold",
        )

    return best