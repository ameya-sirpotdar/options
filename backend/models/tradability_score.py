backend/models/tradability_score.py
from pydantic import BaseModel
from typing import Optional


class TradabilityScore(BaseModel):
    score: float
    reasoning: str
    recommendation: str
    confidence: Optional[float] = None