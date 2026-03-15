from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class PollOptionsBody(BaseModel):
    tickers: List[str]


def _flatten_chain(ticker: str, chain: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for map_key in ("callExpDateMap", "putExpDateMap"):
        exp_map = chain.get(map_key) or {}
        for _exp_date_key, strikes in exp_map.items():
            if not isinstance(strikes, dict):
                continue
            for _strike_key, contract_list in strikes.items():
                if not isinstance(contract_list, list):
                    continue
                for contract in contract_list:
                    if not isinstance(contract, dict):
                        continue
                    rows.append({
                        "ticker": ticker,
                        "putCall": contract.get("putCall"),
                        "strikePrice": contract.get("strikePrice"),
                        "expirationDate": contract.get("expirationDate"),
                        "bid": contract.get("bid"),
                        "ask": contract.get("ask"),
                        "last": contract.get("last"),
                        "volume": contract.get("volume"),
                        "openInterest": contract.get("openInterest"),
                        "delta": contract.get("delta"),
                        "gamma": contract.get("gamma"),
                        "theta": contract.get("theta"),
                        "vega": contract.get("vega"),
                        "impliedVolatility": contract.get("impliedVolatility"),
                        "inTheMoney": contract.get("inTheMoney"),
                    })
    return rows


@router.post("/poll/options")
async def poll_options(body: PollOptionsBody, request: Request):
    """Internal endpoint: fetch and flatten options chain for each ticker."""
    schwab_client = getattr(request.app.state, "schwab_client", None)
    if schwab_client is None:
        raise HTTPException(status_code=503, detail="Schwab service not available.")

    rows: List[Dict[str, Any]] = []
    try:
        for ticker in body.tickers:
            chain = await schwab_client.get_option_chain(ticker)
            rows.extend(_flatten_chain(ticker, chain))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {"rows": rows}
