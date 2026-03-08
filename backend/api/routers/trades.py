from fastapi import APIRouter, HTTPException
from backend.services.tradability_service import rank_candidates
from backend.models.options_data import OptionsRow, BestTradeResponse

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("/best", response_model=BestTradeResponse)
def get_best_trade(candidates: list[OptionsRow] = None):
    """
    Return the single best trade candidate ranked by the tradability index.

    Expects a JSON body list of options rows (each with delta, theta, iv, premium).
    Returns the top-ranked candidate along with its computed tradability score.
    """
    if not candidates:
        raise HTTPException(
            status_code=422,
            detail="No candidate options rows provided. Supply a non-empty list of options rows.",
        )

    ranked = rank_candidates(candidates)

    if not ranked:
        raise HTTPException(
            status_code=404,
            detail="No valid trade candidates could be ranked from the provided data.",
        )

    best = ranked[0]

    return BestTradeResponse(
        best_candidate=best["candidate"],
        score=best["score"],
        rank=1,
    )