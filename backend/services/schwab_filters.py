import logging
from datetime import date, timedelta
from typing import Any, Dict, List

from backend import config

logger = logging.getLogger(__name__)


def _is_weekly_expiry(expiry_str: str) -> bool:
    """Return True if the expiry date falls within the next WEEKLY_EXPIRY_DAYS days."""
    try:
        expiry = date.fromisoformat(expiry_str)
    except ValueError:
        return False
    today = date.today()
    return today <= expiry <= today + timedelta(days=config.WEEKLY_EXPIRY_DAYS)


def _is_near_target_delta(contract: Dict[str, Any]) -> bool:
    delta = contract.get("delta")
    if delta is None:
        return False
    return abs(abs(float(delta)) - config.DELTA_TARGET) <= config.DELTA_TOLERANCE


def filter_contracts(chain_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filter put contracts from a Schwab /marketdata/chains response to:
    - weekly expirations (within WEEKLY_EXPIRY_DAYS days)
    - delta near DELTA_TARGET (±DELTA_TOLERANCE)
    """
    put_exp_map: Dict[str, Any] = chain_data.get("putExpDateMap", {})
    filtered: List[Dict[str, Any]] = []

    for expiry_key, strikes in put_exp_map.items():
        # expiry_key format: "2026-03-07:5" — date portion before ":"
        expiry_str = expiry_key.split(":")[0]
        if not _is_weekly_expiry(expiry_str):
            continue
        for strike_str, contracts in strikes.items():
            for contract in contracts:
                if _is_near_target_delta(contract):
                    filtered.append({**contract, "expiry": expiry_str, "strike": float(strike_str)})

    logger.info("filter_contracts returned %d contracts", len(filtered))
    return filtered
