from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter()

_DELTA_TOLERANCE = 0.05


def _flatten_chain(ticker: str, chain: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for map_key, put_call in (("callExpDateMap", "call"), ("putExpDateMap", "put")):
        exp_map = chain.get(map_key) or {}
        for exp_date_key, strikes in exp_map.items():
            expiry_str = exp_date_key.split(":")[0]
            if not isinstance(strikes, dict):
                continue
            for _strike_key, contract_list in strikes.items():
                if not isinstance(contract_list, list):
                    continue
                for contract in contract_list:
                    if not isinstance(contract, dict):
                        continue
                    bid = contract.get("bid")
                    ask = contract.get("ask")
                    mid = None
                    try:
                        if bid is not None and ask is not None:
                            mid = (float(bid) + float(ask)) / 2
                    except (TypeError, ValueError):
                        mid = None
                    rows.append({
                        "ticker": ticker,
                        "type": put_call,
                        "strike": contract.get("strikePrice"),
                        "expiry": expiry_str,
                        "bid": bid,
                        "ask": ask,
                        "mid": mid,
                        "delta": contract.get("delta"),
                        "iv": contract.get("volatility"),
                        "volume": contract.get("totalVolume"),
                        "open_interest": contract.get("openInterest"),
                    })
    return rows


@router.get("/options-chain")
async def get_options_chain(
    request: Request,
    tickers: List[str] = Query(...),
    delta: Optional[float] = Query(default=None),
    expiry: Optional[str] = Query(default=None),
):
    schwab_client = getattr(request.app.state, "schwab_client", None)
    if schwab_client is None:
        raise HTTPException(status_code=503, detail="Schwab client not available")

    rows: List[Dict[str, Any]] = []
    try:
        for ticker in tickers:
            chain = await schwab_client.get_option_chain(ticker)
            rows.extend(_flatten_chain(ticker, chain))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if expiry:
        rows = [r for r in rows if r.get("expiry") == expiry]

    if delta is not None:
        rows = [
            r for r in rows
            if r.get("delta") is not None
            and abs(abs(float(r["delta"])) - delta) <= _DELTA_TOLERANCE
        ]

    return {"rows": rows}
