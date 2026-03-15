from pydantic import BaseModel, Field
from typing import Optional


class OptionsChainRequest(BaseModel):
    symbol: str = Field(..., description="The ticker symbol for the underlying asset")
    strike_count: Optional[int] = Field(
        default=10,
        description="Number of strikes to return above and below the at-the-money price",
    )
    include_quotes: Optional[bool] = Field(
        default=False,
        description="Whether to include real-time quotes in the response",
    )
    strategy: Optional[str] = Field(
        default="SINGLE",
        description="Option strategy type (e.g., SINGLE, COVERED, VERTICAL, etc.)",
    )
    interval: Optional[float] = Field(
        default=None,
        description="Strike interval for spread strategies",
    )
    strike: Optional[float] = Field(
        default=None,
        description="Specific strike price to filter by",
    )
    range: Optional[str] = Field(
        default=None,
        description="Range of strikes to return (ITM, NTM, OTM, SAK, SBK, SNK, ALL)",
    )
    from_date: Optional[str] = Field(
        default=None,
        description="Start date for expiration range (format: YYYY-MM-DD)",
    )
    to_date: Optional[str] = Field(
        default=None,
        description="End date for expiration range (format: YYYY-MM-DD)",
    )
    volatility: Optional[float] = Field(
        default=None,
        description="Volatility to use in calculations",
    )
    underlying_price: Optional[float] = Field(
        default=None,
        description="Underlying price to use in calculations",
    )
    interest_rate: Optional[float] = Field(
        default=None,
        description="Interest rate to use in calculations",
    )
    days_to_expiration: Optional[int] = Field(
        default=None,
        description="Days to expiration to use in calculations",
    )
    exp_month: Optional[str] = Field(
        default=None,
        description="Expiration month filter (e.g., JAN, FEB, ..., ALL)",
    )
    option_type: Optional[str] = Field(
        default=None,
        description="Option type filter (CALL, PUT, ALL)",
    )
    entitlement: Optional[str] = Field(
        default=None,
        description="Entitlement type for real-time data (PN, NP, PP)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "strike_count": 10,
                "include_quotes": False,
                "strategy": "SINGLE",
                "option_type": "ALL",
            }
        }