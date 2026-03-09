from fastapi import APIRouter, HTTPException, Request

from backend.models.options_data import BestTradeResponse, TradabilityScore
from backend.services.tradability_service import rank_candidates

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("/best", response_model=BestTradeResponse)
def get_best_trade(request: Request):
    """
    Return the single best trade candidate ranked by the tradability index.

    Fetches stored options rows from Azure Table Storage, scores each one,
    and returns the top-ranked candidate along with all ranked candidates.
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

    # rank_candidates returns dicts augmented with 'metrics' and 'tradability_score'
    ranked_dicts = rank_candidates([r if isinstance(r, dict) else r.model_dump() for r in raw_rows])

    if not ranked_dicts:
        raise HTTPException(
            status_code=404,
            detail="No valid trade candidates could be ranked.",
        )

    def to_score(row: dict) -> TradabilityScore:
        m = row.get("metrics", {})
        return TradabilityScore(
            symbol=row.get("symbol", row.get("RowKey", "")),
            underlying_symbol=row.get("underlyingSymbol", row.get("PartitionKey", "")),
            score=row["tradability_score"],
            delta=m.get("delta"),
            theta=m.get("theta"),
            iv=m.get("iv"),
            premium=m.get("premium"),
        )

    ranked_scores = [to_score(r) for r in ranked_dicts]

    return BestTradeResponse(
        best_candidate=ranked_scores[0],
        ranked_candidates=ranked_scores,
    )
