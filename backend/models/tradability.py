from pydantic import BaseModel, Field
from typing import Optional


class TradabilityWeights(BaseModel):
    liquidity: float = Field(default=0.35, ge=0.0, le=1.0, description="Weight for liquidity score component")
    momentum: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight for momentum score component")
    volatility: float = Field(default=0.20, ge=0.0, le=1.0, description="Weight for volatility score component")
    spread: float = Field(default=0.20, ge=0.0, le=1.0, description="Weight for bid-ask spread score component")

    class Config:
        json_schema_extra = {
            "example": {
                "liquidity": 0.35,
                "momentum": 0.25,
                "volatility": 0.20,
                "spread": 0.20,
            }
        }


class TradabilityScore(BaseModel):
    symbol: str = Field(..., description="Ticker symbol of the asset")
    total_score: float = Field(..., ge=0.0, le=1.0, description="Composite tradability score between 0 and 1")
    liquidity_score: float = Field(..., ge=0.0, le=1.0, description="Normalized liquidity component score")
    momentum_score: float = Field(..., ge=0.0, le=1.0, description="Normalized momentum component score")
    volatility_score: float = Field(..., ge=0.0, le=1.0, description="Normalized volatility component score")
    spread_score: float = Field(..., ge=0.0, le=1.0, description="Normalized bid-ask spread component score")
    volume: Optional[float] = Field(default=None, description="Raw trading volume used in computation")
    price_change_pct: Optional[float] = Field(default=None, description="Raw price change percentage used in computation")
    avg_spread: Optional[float] = Field(default=None, description="Raw average bid-ask spread used in computation")
    avg_volume: Optional[float] = Field(default=None, description="Raw average volume used in computation")
    rank: Optional[int] = Field(default=None, description="Rank among all scored candidates (1 = best)")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "total_score": 0.82,
                "liquidity_score": 0.90,
                "momentum_score": 0.75,
                "volatility_score": 0.80,
                "spread_score": 0.70,
                "volume": 75000000.0,
                "price_change_pct": 2.5,
                "avg_spread": 0.02,
                "avg_volume": 70000000.0,
                "rank": 1,
            }
        }


class BestTradeResponse(BaseModel):
    best_symbol: str = Field(..., description="Symbol with the highest tradability score")
    best_score: TradabilityScore = Field(..., description="Full tradability score details for the best candidate")
    all_scores: list[TradabilityScore] = Field(default_factory=list, description="Ranked list of all candidate scores")
    weights_used: TradabilityWeights = Field(..., description="Weights configuration used to compute scores")

    class Config:
        json_schema_extra = {
            "example": {
                "best_symbol": "AAPL",
                "best_score": {
                    "symbol": "AAPL",
                    "total_score": 0.82,
                    "liquidity_score": 0.90,
                    "momentum_score": 0.75,
                    "volatility_score": 0.80,
                    "spread_score": 0.70,
                    "volume": 75000000.0,
                    "price_change_pct": 2.5,
                    "avg_spread": 0.02,
                    "avg_volume": 70000000.0,
                    "rank": 1,
                },
                "all_scores": [],
                "weights_used": {
                    "liquidity": 0.35,
                    "momentum": 0.25,
                    "volatility": 0.20,
                    "spread": 0.20,
                },
            }
        }