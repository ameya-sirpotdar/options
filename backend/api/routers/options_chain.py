from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter()

_MAX_TICKER_LEN = 10
_MAX_TICKERS = 10
_DELTA_TOLERANCE = 0.05


def _validate_and_normalize(raw_tickers: List[str]) -> List[str]:
    """Strip, uppercase, deduplicate, and validate tickers.

    Raises HTTPException(422) on bad input so FastAPI returns a 422 response.
    """
    normalized: List[str] = []
    for t in raw_tickers:
        cleaned = t.strip().upper()
        if not cleaned:
            raise HTTPException(
                status_code=422,
                detail=f"Ticker '{t}' is empty or whitespace.",
            )
        if len(cleaned) > _MAX_TICKER_LEN:
            raise HTTPException(
                status_code=422,
                detail=f"Ticker '{cleaned}' exceeds maximum length of {_MAX_TICKER_LEN}.",
            )
        if cleaned not in normalized:
            normalized.append(cleaned)

    if len(normalized) > _MAX_TICKERS:
        raise HTTPException(
            status_code=422,
            detail=f"Too many tickers (max {_MAX_TICKERS}, got {len(normalized)}).",
        )

    return normalized


def _normalize_chain(ticker: str, chain: Dict) -> List[Dict]:
    """Flatten a Schwab options chain dict into normalized row dicts."""
    rows = []
    for map_key, contract_type in [("callExpDateMap", "call"), ("putExpDateMap", "put")]:
        exp_map = chain.get(map_key) or {}
        for _exp, strikes in exp_map.items():
            if not isinstance(strikes, dict):
                continue
            for _strike, contracts in strikes.items():
                if not isinstance(contracts, list):
                    continue
                for c in contracts:
                    if not isinstance(c, dict):
                        continue
                    bid = c.get("bid") or 0.0
                    ask = c.get("ask") or 0.0
                    rows.append({
                        "ticker": ticker,
                        "strike": c.get("strikePrice"),
                        "expiry": c.get("expirationDate"),
                        "type": contract_type,
                        "bid": bid,
                        "ask": ask,
                        "mid": round((bid + ask) / 2, 4),
                        "last": c.get("last"),
                        "volume": c.get("volume") or c.get("totalVolume"),
                        "open_interest": c.get("openInterest"),
                        "delta": c.get("delta"),
                        "gamma": c.get("gamma"),
                        "theta": c.get("theta"),
                        "vega": c.get("vega"),
                        "iv": c.get("impliedVolatility"),
                        "in_the_money": c.get("inTheMoney"),
                    })
    return rows


def _filter_by_delta(rows: List[Dict], target_delta: float) -> List[Dict]:
    return [
        r for r in rows
        if r.get("delta") is not None
        and abs(abs(r["delta"]) - target_delta) <= _DELTA_TOLERANCE
    ]


@router.get("/options-chain")
async def get_options_chain(
    http_request: Request,
    tickers: List[str] = Query(...),
    delta: Optional[float] = Query(None),
    expiry: Optional[str] = Query(None),
):
    """Fetch and normalize live options chain data from Schwab for the given tickers."""
    normalized = _validate_and_normalize(tickers)

    schwab_client = getattr(http_request.app.state, "schwab_client", None)
    if schwab_client is None:
        raise HTTPException(status_code=503, detail="Schwab service not available.")

    rows: List[Dict] = []
    for ticker in normalized:
        try:
            chain = await schwab_client.get_option_chain(
                ticker,
                from_date=expiry,
                to_date=expiry,
            )
            ticker_rows = _normalize_chain(ticker, chain)
            if delta is not None:
                ticker_rows = _filter_by_delta(ticker_rows, delta)
            rows.extend(ticker_rows)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    return {"rows": rows, "vix": None}
