from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from backend.models.tradability import ScoredTrade
from backend.services.tradability_service import TradabilityService

router = APIRouter(prefix="/trades", tags=["trades"])


def get_tradability_service() -> TradabilityService:
    return TradabilityService()


@router.get("/best", response_model=List[ScoredTrade])
async def get_best_trades(
    top_n: Optional[int] = Query(default=10, ge=1, le=100, description="Number of top trades to return"),
    min_score: Optional[float] = Query(default=None, ge=0.0, le=1.0, description="Minimum tradability score filter"),
    service: TradabilityService = Depends(get_tradability_service),
) -> List[ScoredTrade]:
    """
    Retrieve the best trades ranked by tradability index score.

    Returns a list of trades sorted by their computed tradability score in
    descending order. Optionally filter by a minimum score threshold and
    limit the number of results returned.
    """
    scored_trades = service.get_best_trades(top_n=top_n, min_score=min_score)
    return scored_trades