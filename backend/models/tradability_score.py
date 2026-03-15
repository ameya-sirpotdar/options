backend/models/tradability_score.py
from pydantic import BaseModel


class TradabilityScore(BaseModel):
    symbol: str
    score: float
    recommendation: str