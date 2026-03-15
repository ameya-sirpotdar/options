from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter()


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
