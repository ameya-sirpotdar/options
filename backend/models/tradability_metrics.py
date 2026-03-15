backend/models/tradability_metrics.py
from pydantic import BaseModel


class TradabilityMetrics(BaseModel):
    delta: float
    gamma: float
    theta: float
    vega: float
    implied_volatility: float
    open_interest: int
    volume: int
    bid_ask_spread: float
    days_to_expiration: int
    strike_distance_pct: float