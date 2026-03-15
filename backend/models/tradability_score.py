backend/models/tradability_score.py
from pydantic import BaseModel


class TradabilityScore(BaseModel):
    score: float
    label: str