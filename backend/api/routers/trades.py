from typing import List

from fastapi import APIRouter, HTTPException, Request

from backend.models.tradability_score import TradabilityScore
from backend.services.trades_comparison_service import TradesComparisonService

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", response_model=List[TradabilityScore])
def get_trades(request: Request):
    """
    Return a flat list of all trade candidates ranked by tradability score.

    Fetches stored options contracts from Azure Table Storage, scores each one
    using TradesComparisonService, and returns the full ranked list.
    """
    svc = getattr(request.app.state, "azure_table_service", None)
    if svc is None:
        raise HTTPException(
            status_code=503,
            detail="Azure Table Storage is not available.",
        )

    raw_rows = svc.get_options_contracts()
    if not raw_rows:
        raise HTTPException(
            status_code=404,
            detail="No options data found in storage.",
        )

    comparison_service = TradesComparisonService()
    contracts = [
        r if isinstance(r, dict) else r.model_dump() for r in raw_rows
    ]
    ranked_scores: List[TradabilityScore] = comparison_service.rank_candidates(contracts)

    if not ranked_scores:
        raise HTTPException(
            status_code=404,
            detail="No valid trade candidates could be ranked.",
        )

    return ranked_scores
