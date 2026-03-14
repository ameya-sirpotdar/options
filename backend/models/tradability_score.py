backend/models/tradability_score.py
from pydantic import BaseModel, Field
from typing import Optional


class TradabilityScore(BaseModel):
    symbol: str = Field(..., description="The ticker symbol of the underlying asset")
    score: float = Field(..., ge=0.0, le=1.0, description="Tradability score between 0 and 1")
    is_tradable: bool = Field(..., description="Whether the asset is considered tradable")
    reason: Optional[str] = Field(None, description="Optional reason or explanation for the score")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "score": 0.85,
                "is_tradable": True,
                "reason": "High liquidity and favorable market conditions",
            }
        }