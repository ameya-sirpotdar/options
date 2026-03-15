from pydantic import BaseModel
from typing import Optional


class TradabilityMetrics(BaseModel):
    """Tradability metrics for a single options contract candidate."""

    symbol: str
    liquidity_score: Optional[float] = None
    volatility_score: Optional[float] = None
    momentum_score: Optional[float] = None
    overall_score: Optional[float] = None
