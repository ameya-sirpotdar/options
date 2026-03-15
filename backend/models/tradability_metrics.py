backend/models/tradability_metrics.py
from pydantic import BaseModel
from typing import Optional


class TradabilityMetrics(BaseModel):
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    implied_volatility: Optional[float] = None
    open_interest: Optional[int] = None
    volume: Optional[int] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_ask_spread: Optional[float] = None
    bid_ask_spread_pct: Optional[float] = None
    days_to_expiration: Optional[int] = None
    intrinsic_value: Optional[float] = None
    extrinsic_value: Optional[float] = None
    in_the_money: Optional[bool] = None
    underlying_price: Optional[float] = None
    strike_price: Optional[float] = None
    moneyness: Optional[float] = None