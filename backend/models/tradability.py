from pydantic import BaseModel, Field
from typing import Optional


class TradabilityWeights(BaseModel):
    liquidity: float = Field(default=0.3, ge=0.0, le=1.0, description="Weight for liquidity score component")
    momentum: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight for momentum score component")
    volatility: float = Field(default=0.2, ge=0.0, le=1.0, description="Weight for volatility score component")
    volume_trend: float = Field(default=0.15, ge=0.0, le=1.0, description="Weight for volume trend score component")
    spread: float = Field(default=0.1, ge=0.0, le=1.0, description="Weight for bid-ask spread score component")

    class Config:
        json_schema_extra = {
            "example": {
                "liquidity": 0.3,
                "momentum": 0.25,
                "volatility": 0.2,
                "volume_trend": 0.15,
                "spread": 0.1,
            }
        }


class TradabilityScore(BaseModel):
    symbol: str = Field(..., description="Ticker symbol of the asset")
    total_score: float = Field(..., ge=0.0, le=1.0, description="Composite tradability score between 0 and 1")
    liquidity_score: float = Field(..., ge=0.0, le=1.0, description="Liquidity component score")
    momentum_score: float = Field(..., ge=0.0, le=1.0, description="Momentum component score")
    volatility_score: float = Field(..., ge=0.0, le=1.0, description="Volatility component score")
    volume_trend_score: float = Field(..., ge=0.0, le=1.0, description="Volume trend component score")
    spread_score: float = Field(..., ge=0.0, le=1.0, description="Bid-ask spread component score")
    rank: Optional[int] = Field(default=None, description="Rank among evaluated candidates (1 = best)")
    weights_used: TradabilityWeights = Field(..., description="Weights applied when computing this score")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "total_score": 0.82,
                "liquidity_score": 0.9,
                "momentum_score": 0.75,
                "volatility_score": 0.8,
                "volume_trend_score": 0.7,
                "spread_score": 0.95,
                "rank": 1,
                "weights_used": {
                    "liquidity": 0.3,
                    "momentum": 0.25,
                    "volatility": 0.2,
                    "volume_trend": 0.15,
                    "spread": 0.1,
                },
            }
        }


class TradabilityMetrics(BaseModel):
    symbol: str = Field(..., description="Ticker symbol of the asset")
    avg_daily_volume: float = Field(..., gt=0.0, description="Average daily trading volume")
    price_change_pct: float = Field(..., description="Percentage price change over the lookback period")
    volatility: float = Field(..., ge=0.0, description="Annualised or period volatility of returns")
    volume_change_pct: float = Field(..., description="Percentage change in volume over the lookback period")
    avg_spread_pct: float = Field(..., ge=0.0, description="Average bid-ask spread as a percentage of price")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "avg_daily_volume": 75_000_000.0,
                "price_change_pct": 4.5,
                "volatility": 0.22,
                "volume_change_pct": 12.0,
                "avg_spread_pct": 0.05,
            }
        }


class BestTradeResponse(BaseModel):
    best_symbol: str = Field(..., description="Symbol with the highest tradability score")
    scores: list[TradabilityScore] = Field(..., description="Full ranked list of tradability scores")

    class Config:
        json_schema_extra = {
            "example": {
                "best_symbol": "AAPL",
                "scores": [
                    {
                        "symbol": "AAPL",
                        "total_score": 0.82,
                        "liquidity_score": 0.9,
                        "momentum_score": 0.75,
                        "volatility_score": 0.8,
                        "volume_trend_score": 0.7,
                        "spread_score": 0.95,
                        "rank": 1,
                        "weights_used": {
                            "liquidity": 0.3,
                            "momentum": 0.25,
                            "volatility": 0.2,
                            "volume_trend": 0.15,
                            "spread": 0.1,
                        },
                    }
                ],
            }
        }