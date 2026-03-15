from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class OptionsContract(BaseModel):
    """Simplified options contract model used for scoring and comparison."""

    symbol: str
    strike: Optional[float] = None
    expiration: Optional[str] = None
    option_type: Optional[Literal["call", "put", "CALL", "PUT"]] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None


class OptionsContractRecord(BaseModel):
    """
    Options contract record for Azure Table Storage persistence.

    Required: runId, symbol, contractType, strikePrice, expirationDate.
    Auto-computed: PartitionKey, RowKey, timestamp.
    """

    # Required fields
    runId: str = Field(..., description="UUID identifying the polling run.")
    symbol: str = Field(..., description="Option contract symbol (underlying).")
    contractType: str = Field(..., description="'CALL' or 'PUT'.")
    strikePrice: float = Field(..., description="Strike price.")
    expirationDate: str = Field(..., description="Expiration date string (ISO-8601).")

    # Auto-computed keys (set via model_validator)
    PartitionKey: Optional[str] = Field(None, description="ATS partition key (= symbol).")
    RowKey: Optional[str] = Field(None, description="ATS row key.")

    # Timestamp
    timestamp: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when record was created.",
    )

    # Optional pricing fields
    underlyingPrice: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    mark: Optional[float] = None
    bidSize: Optional[int] = None
    askSize: Optional[int] = None
    lastSize: Optional[int] = None
    highPrice: Optional[float] = None
    lowPrice: Optional[float] = None
    openPrice: Optional[float] = None
    closePrice: Optional[float] = None
    totalVolume: Optional[int] = None
    netChange: Optional[float] = None
    percentChange: Optional[float] = None
    markChange: Optional[float] = None
    markPercentChange: Optional[float] = None

    # Greeks
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None

    # Volatility
    volatility: Optional[float] = None
    theoreticalOptionValue: Optional[float] = None
    theoreticalVolatility: Optional[float] = None

    # Volume / OI
    openInterest: Optional[int] = None

    # Time / expiry
    daysToExpiration: Optional[int] = None
    expirationType: Optional[str] = None
    settlementType: Optional[str] = None
    tradeTimeInLong: Optional[int] = None
    quoteTimeInLong: Optional[int] = None
    lastTradingDay: Optional[int] = None

    # Value fields
    intrinsicValue: Optional[float] = None
    extrinsicValue: Optional[float] = None
    timeValue: Optional[float] = None
    optionRoot: Optional[str] = None

    # Boolean flags
    inTheMoney: Optional[bool] = None
    pennyPilot: Optional[bool] = None
    nonStandard: Optional[bool] = None
    mini: Optional[bool] = None

    # Misc
    multiplier: Optional[float] = None
    bidAskSize: Optional[str] = None
    tradingStatus: Optional[str] = None
    description: Optional[str] = None
    exchangeName: Optional[str] = None
    underlyingSymbol: Optional[str] = None
    optionDeliverablesList: Optional[Any] = None
    deliverableNote: Optional[str] = None
    netPercentChange: Optional[float] = None

    # Extra fields accepted by tests
    strikePrice2: Optional[float] = None
    expirationDateISO: Optional[str] = None
    isIndexOption: Optional[bool] = None

    # CCP fields
    annualizedRoi: Optional[float] = Field(
        None,
        description="Annualized ROI for cash-covered put, as decimal.",
    )

    @model_validator(mode="after")
    def _set_computed_fields(self) -> "OptionsContractRecord":
        if self.PartitionKey is None:
            self.PartitionKey = self.symbol
        if self.RowKey is None:
            self.RowKey = f"{self.runId}_{self.contractType}_{self.strikePrice}_{self.expirationDate}"
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        return self

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
