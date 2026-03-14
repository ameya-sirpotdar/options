backend/models/tradability_metrics.py

from pydantic import BaseModel, Field
from typing import Optional


class TradabilityMetrics(BaseModel):
    delta: Optional[float] = Field(None, description="Option delta value")
    gamma: Optional[float] = Field(None, description="Option gamma value")
    theta: Optional[float] = Field(None, description="Option theta value")
    vega: Optional[float] = Field(None, description="Option vega value")
    rho: Optional[float] = Field(None, description="Option rho value")
    implied_volatility: Optional[float] = Field(None, description="Implied volatility of the option")
    open_interest: Optional[int] = Field(None, description="Open interest for the option contract")
    total_volume: Optional[int] = Field(None, description="Total trading volume for the option contract")
    bid: Optional[float] = Field(None, description="Bid price of the option")
    ask: Optional[float] = Field(None, description="Ask price of the option")
    bid_ask_spread: Optional[float] = Field(None, description="Spread between bid and ask prices")
    intrinsic_value: Optional[float] = Field(None, description="Intrinsic value of the option")
    extrinsic_value: Optional[float] = Field(None, description="Extrinsic (time) value of the option")
    days_to_expiration: Optional[int] = Field(None, description="Number of days until the option expires")
    strike_price: Optional[float] = Field(None, description="Strike price of the option contract")
    underlying_price: Optional[float] = Field(None, description="Current price of the underlying asset")
    moneyness: Optional[float] = Field(None, description="Ratio of underlying price to strike price")
    probability_of_profit: Optional[float] = Field(None, description="Estimated probability of the trade being profitable")
    max_profit: Optional[float] = Field(None, description="Maximum potential profit for the trade")
    max_loss: Optional[float] = Field(None, description="Maximum potential loss for the trade")
    breakeven_price: Optional[float] = Field(None, description="Price at which the trade breaks even")

    class Config:
        populate_by_name = True