from pydantic import BaseModel, Field
from typing import Optional


class TradabilityWeights(BaseModel):
    liquidity: float = Field(default=0.35, ge=0.0, le=1.0, description="Weight for liquidity score component")
    volatility: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight for volatility score component")
    spread: float = Field(default=0.20, ge=0.0, le=1.0, description="Weight for bid-ask spread score component")
    volume_consistency: float = Field(default=0.20, ge=0.0, le=1.0, description="Weight for volume consistency score component")

    class Config:
        json_schema_extra = {
            "example": {
                "liquidity": 0.35,
                "volatility": 0.25,
                "spread": 0.20,
                "volume_consistency": 0.20,
            }
        }


class TradabilityScore(BaseModel):
    symbol: str = Field(..., description="Ticker symbol of the asset")
    liquidity_score: float = Field(..., ge=0.0, le=1.0, description="Normalized liquidity score")
    volatility_score: float = Field(..., ge=0.0, le=1.0, description="Normalized volatility score")
    spread_score: float = Field(..., ge=0.0, le=1.0, description="Normalized bid-ask spread score")
    volume_consistency_score: float = Field(..., ge=0.0, le=1.0, description="Normalized volume consistency score")
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Weighted composite tradability score")
    rank: Optional[int] = Field(default=None, description="Rank among evaluated candidates (1 = best)")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "liquidity_score": 0.92,
                "volatility_score": 0.78,
                "spread_score": 0.85,
                "volume_consistency_score": 0.80,
                "composite_score": 0.8455,
                "rank": 1,
            }
        }