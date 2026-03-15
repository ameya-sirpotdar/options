from fastapi import APIRouter, HTTPException, Request

from backend.models.tradability_score import TradabilityScore
from backend.services.trades_comparison_service import TradesComparisonService

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", summary="List all ranked trade candidates")
def list_trades(request: Request):
    """
    Return all trade candidates ranked by the tradability index.

    Fetches stored options rows from Azure Table Storage, scores each one,
    and returns all ranked candidates.
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

    comparison_svc = TradesComparisonService()
    ranked_dicts = comparison_svc.rank_candidates(
        [r if isinstance(r, dict) else r.model_dump() for r in raw_rows]
    )

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

    return [to_score(r) for r in ranked_dicts]


@router.get("/best", response_model=TradabilityScore, summary="Get the single best trade candidate")
def get_best_trade(request: Request):
    """
    Return the single best trade candidate ranked by the tradability index.

    Fetches stored options rows from Azure Table Storage, scores each one,
    and returns the top-ranked candidate.
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

    comparison_svc = TradesComparisonService()
    ranked_dicts = comparison_svc.rank_candidates(
        [r if isinstance(r, dict) else r.model_dump() for r in raw_rows]
    )

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

    return to_score(ranked_dicts[0])
