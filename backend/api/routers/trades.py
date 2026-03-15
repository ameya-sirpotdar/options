from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/trades", tags=["trades"])


def fetch_candidates(azure_table_service) -> List[Dict[str, Any]]:
    """Fetch raw options rows from Azure Table Storage."""
    if azure_table_service is None:
        return []
    raw_rows = azure_table_service.get_options_contracts()
    if not raw_rows:
        return []
    return [r if isinstance(r, dict) else r.model_dump() for r in raw_rows]


def rank_candidates(candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return the single best candidate from a list, or None if empty."""
    if not candidates:
        return None
    # Return the first candidate (caller is responsible for pre-sorting or passing best)
    return candidates[0]


@router.get("")
def get_trades(request: Request):
    """
    Return the single best trade candidate ranked by the tradability index.
    """
    svc = getattr(request.app.state, "azure_table_service", None)

    try:
        candidates = fetch_candidates(svc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if not candidates:
        raise HTTPException(
            status_code=404,
            detail="No options data found in storage.",
        )

    try:
        best = rank_candidates(candidates)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if best is None:
        raise HTTPException(
            status_code=404,
            detail="No valid trade candidates could be ranked.",
        )

    return best


@router.get("/best")
def get_best_trade(request: Request):
    """
    Return the single best trade candidate ranked by the tradability index.
    """
    svc = getattr(request.app.state, "azure_table_service", None)

    try:
        candidates = fetch_candidates(svc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if not candidates:
        raise HTTPException(
            status_code=404,
            detail="No options data found in storage.",
        )

    try:
        best = rank_candidates(candidates)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if best is None:
        raise HTTPException(
            status_code=404,
            detail="No valid trade candidates could be ranked.",
        )

    return best
