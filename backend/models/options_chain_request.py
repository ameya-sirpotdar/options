from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class OptionsChainRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    symbol: str = Field(..., description="The ticker symbol for the underlying asset")
    contract_type: Optional[str] = Field(
        default="ALL",
        description="Type of options contract: CALL, PUT, or ALL",
    )
    strike_count: Optional[int] = Field(
        default=10,
        description="Number of strikes to return above and below the at-the-money price",
    )
    include_underlying_quote: Optional[bool] = Field(
        default=True,
        description="Whether to include a quote for the underlying asset",
    )
    strategy: Optional[str] = Field(
        default="SINGLE",
        description="Options strategy type (e.g., SINGLE, COVERED, VERTICAL, etc.)",
    )
    interval: Optional[float] = Field(
        default=None,
        description="Strike interval for spread strategies",
    )
    strike: Optional[float] = Field(
        default=None,
        description="Specific strike price to filter by",
    )
    strike_range: Optional[str] = Field(
        default="ALL",
        alias="range",
        description="Range of strikes: ITM, NTM, OTM, SAK, SBK, SNK, or ALL",
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
        default="ALL",
        description="Expiration month filter (e.g., JAN, FEB, ..., ALL)",
    )
    option_type: Optional[str] = Field(
        default=None,
        description="Option type: S (standard), NS (non-standard), or ALL",
    )
    entitlement: Optional[str] = Field(
        default=None,
        description="Entitlement level: PN (paying non-pro), NP (non-paying), PP (paying pro)",
    )
