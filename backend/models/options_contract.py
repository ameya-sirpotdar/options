backend/models/options_contract.py
from pydantic import BaseModel, Field
from typing import Optional


class OptionsContract(BaseModel):
    symbol: str = Field(..., description="The option contract symbol")
    underlying_symbol: str = Field(..., description="The underlying asset symbol")
    expiration_date: str = Field(..., description="Expiration date in YYYY-MM-DD format")
    strike_price: float = Field(..., description="Strike price of the option")
    option_type: str = Field(..., description="Option type: 'CALL' or 'PUT'")
    bid: Optional[float] = Field(None, description="Bid price")
    ask: Optional[float] = Field(None, description="Ask price")
    last: Optional[float] = Field(None, description="Last traded price")
    mark: Optional[float] = Field(None, description="Mark price (midpoint of bid/ask)")
    volume: Optional[int] = Field(None, description="Trading volume")
    open_interest: Optional[int] = Field(None, description="Open interest")
    implied_volatility: Optional[float] = Field(None, description="Implied volatility")
    delta: Optional[float] = Field(None, description="Delta greek")
    gamma: Optional[float] = Field(None, description="Gamma greek")
    theta: Optional[float] = Field(None, description="Theta greek")
    vega: Optional[float] = Field(None, description="Vega greek")
    rho: Optional[float] = Field(None, description="Rho greek")
    in_the_money: Optional[bool] = Field(None, description="Whether the option is in the money")
    intrinsic_value: Optional[float] = Field(None, description="Intrinsic value of the option")
    extrinsic_value: Optional[float] = Field(None, description="Extrinsic (time) value of the option")
    days_to_expiration: Optional[int] = Field(None, description="Number of days until expiration")

    class Config:
        populate_by_name = True