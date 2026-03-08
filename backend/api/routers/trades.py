from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from backend.models.tradability import TradabilityScore
from backend.services.tradability_service import TradabilityService
from backend.config import Settings, get_settings

router = APIRouter(prefix="/trades", tags=["trades"])


def get_tradability_service(settings: Settings = Depends(get_settings)) -> TradabilityService:
    return TradabilityService(settings=settings)


@router.get(
    "/best",
    response_model=TradabilityScore,
    summary="Get the best tradable candidate",
    description=(
        "Evaluates all available trade candidates using the Tradability Index Engine "
        "and returns the single best candidate based on the computed tradability score."
    ),
)
def get_best_trade(
    min_score: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional minimum tradability score threshold (0.0 to 1.0). "
                    "If the best candidate does not meet this threshold, a 404 is returned.",
    ),
    service: TradabilityService = Depends(get_tradability_service),
) -> TradabilityScore:
    best = service.get_best_trade()

    if best is None:
        raise HTTPException(
            status_code=404,
            detail="No tradable candidates are currently available.",
        )

    if min_score is not None and best.score < min_score:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Best available candidate has a tradability score of {best.score:.4f}, "
                f"which is below the requested minimum threshold of {min_score:.4f}."
            ),
        )

    return best


@router.get(
    "/ranked",
    response_model=list[TradabilityScore],
    summary="Get all candidates ranked by tradability score",
    description=(
        "Returns all trade candidates sorted in descending order by their computed "
        "tradability score."
    ),
)
def get_ranked_trades(
    min_score: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional minimum tradability score filter. Only candidates at or "
                    "above this threshold will be included in the response.",
    ),
    limit: Optional[int] = Query(
        default=None,
        ge=1,
        description="Optional maximum number of candidates to return.",
    ),
    service: TradabilityService = Depends(get_tradability_service),
) -> list[TradabilityScore]:
    ranked = service.rank_candidates()

    if not ranked:
        raise HTTPException(
            status_code=404,
            detail="No tradable candidates are currently available.",
        )

    if min_score is not None:
        ranked = [candidate for candidate in ranked if candidate.score >= min_score]

    if not ranked:
        raise HTTPException(
            status_code=404,
            detail=f"No candidates meet the minimum score threshold of {min_score:.4f}.",
        )

    if limit is not None:
        ranked = ranked[:limit]

    return ranked