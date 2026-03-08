from pydantic import BaseModel, Field
from typing import Optional


class TradabilityWeights(BaseModel):
    liquidity: float = Field(default=0.4, ge=0.0, le=1.0)
    volatility: float = Field(default=0.3, ge=0.0, le=1.0)
    momentum: float = Field(default=0.2, ge=0.0, le=1.0)
    spread: float = Field(default=0.1, ge=0.0, le=1.0)


class ScoredTrade(BaseModel):
    symbol: str
    tradability_score: float = Field(ge=0.0, le=1.0)
    liquidity_score: float = Field(ge=0.0, le=1.0)
    volatility_score: float = Field(ge=0.0, le=1.0)
    momentum_score: float = Field(ge=0.0, le=1.0)
    spread_score: float = Field(ge=0.0, le=1.0)
    volume: Optional[float] = None
    price: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    price_change_24h: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC/USDT",
                "tradability_score": 0.85,
                "liquidity_score": 0.9,
                "volatility_score": 0.8,
                "momentum_score": 0.75,
                "spread_score": 0.95,
                "volume": 1500000.0,
                "price": 42000.0,
                "bid": 41999.0,
                "ask": 42001.0,
                "high_24h": 43000.0,
                "low_24h": 41000.0,
                "price_change_24h": 2.5,
            }
        }


class TradabilityRequest(BaseModel):
    symbols: Optional[list[str]] = None
    weights: Optional[TradabilityWeights] = None
    top_n: int = Field(default=10, ge=1, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
                "weights": {
                    "liquidity": 0.4,
                    "volatility": 0.3,
                    "momentum": 0.2,
                    "spread": 0.1,
                },
                "top_n": 5,
            }
        }


class TradabilityResponse(BaseModel):
    trades: list[ScoredTrade]
    total_evaluated: int
    weights_used: TradabilityWeights

    class Config:
        json_schema_extra = {
            "example": {
                "trades": [],
                "total_evaluated": 50,
                "weights_used": {
                    "liquidity": 0.4,
                    "volatility": 0.3,
                    "momentum": 0.2,
                    "spread": 0.1,
                },
            }
        }