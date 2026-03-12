from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request

from backend import config
from backend.api.poll import _flatten_chain

router = APIRouter()


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Remap Schwab raw field names to the names expected by the frontend."""
    bid = row.get("bid") or 0
    ask = row.get("ask") or 0
    return {
        "ticker": row.get("ticker"),
        "type": (row.get("putCall") or "").lower(),
        "strike": row.get("strikePrice"),
        "expiry": row.get("expirationDate"),
        "bid": bid,
        "ask": ask,
        "mid": round((bid + ask) / 2, 4),
        "last": row.get("last"),
        "volume": row.get("volume"),
        "open_interest": row.get("openInterest"),
        "delta": row.get("delta"),
        "gamma": row.get("gamma"),
        "theta": row.get("theta"),
        "vega": row.get("vega"),
        "iv": row.get("impliedVolatility"),
        "inTheMoney": row.get("inTheMoney"),
    }


@router.get("/options-chain")
async def get_options_chain(
    http_request: Request,
    tickers: List[str] = Query(...),
    delta: float = Query(default=0.30),
    expiry: Optional[str] = Query(default=None),
):
    schwab_client = getattr(http_request.app.state, "schwab_client", None)
    if schwab_client is None:
        raise HTTPException(status_code=503, detail="Schwab client not available")

    rows: List[Dict[str, Any]] = []
    try:
        for ticker in tickers:
            chain = await schwab_client.get_option_chain(ticker, from_date=expiry, to_date=expiry)
            flat = _flatten_chain(ticker, chain)
            for row in flat:
                delta_val = row.get("delta")
                if delta_val is not None and abs(abs(delta_val) - delta) > config.DELTA_TOLERANCE:
                    continue
                rows.append(_normalize_row(row))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"rows": rows, "vix": None}
