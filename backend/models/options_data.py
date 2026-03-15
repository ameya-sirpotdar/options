from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class OptionsContractRecord(BaseModel):
    """
    Pydantic model representing a single options contract record
    as returned by the Schwab API, mapped for Azure Table Storage persistence.

    PartitionKey = runId (set dynamically by the service layer)
    RowKey = symbol (set dynamically by the service layer)

    Extra fields (e.g. ``optionDeliverablesList``, ``annualizedRoi``) may be
    passed and are stored on the model but are not part of ``model_fields``.
    """

    # -------------------------------------------------------------------------
    # Run / ingestion metadata
    # -------------------------------------------------------------------------
    runId: str = Field(..., description="UUID identifying the polling run.")
    ingestedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp at which this record was written to storage.",
    )

    # -------------------------------------------------------------------------
    # Contract identity
    # -------------------------------------------------------------------------
    symbol: str = Field(..., description="Option contract symbol.")
    underlyingSymbol: str = Field(..., description="Underlying equity/ETF symbol.")
    description: Optional[str] = Field(None, description="Human-readable contract description.")
    contractType: Optional[str] = Field(None, description="'CALL' or 'PUT'.")

    # -------------------------------------------------------------------------
    # Expiration / strike
    # -------------------------------------------------------------------------
    expirationDate: Optional[str] = Field(None, description="Expiration date string (ISO-8601).")
    daysToExpiration: Optional[int] = Field(None, description="Calendar days until expiration.")
    expirationType: Optional[str] = Field(None, description="e.g. 'R' (regular), 'W' (weekly).")
    settlementType: Optional[str] = Field(None, description="e.g. 'A' (AM), 'P' (PM).")
    strikePrice: Optional[float] = Field(None, description="Strike price of the contract.")
    lastTradingDay: Optional[int] = Field(None, description="Last trading day (Unix ms).")

    # -------------------------------------------------------------------------
    # Pricing
    # -------------------------------------------------------------------------
    bid: Optional[float] = Field(None, description="Current best bid price.")
    ask: Optional[float] = Field(None, description="Current best ask price.")
    last: Optional[float] = Field(None, description="Last traded price.")
    mark: Optional[float] = Field(None, description="Mid-point mark price.")
    bidSize: Optional[int] = Field(None, description="Number of contracts at the bid.")
    askSize: Optional[int] = Field(None, description="Number of contracts at the ask.")
    lastSize: Optional[int] = Field(None, description="Size of the last trade.")
    highPrice: Optional[float] = Field(None, description="Intraday high price.")
    lowPrice: Optional[float] = Field(None, description="Intraday low price.")
    openPrice: Optional[float] = Field(None, description="Opening price for the session.")
    closePrice: Optional[float] = Field(None, description="Previous session closing price.")
    netChange: Optional[float] = Field(None, description="Net price change from previous close.")
    markChange: Optional[float] = Field(None, description="Change in the mark price.")
    markPercentChange: Optional[float] = Field(None, description="Percentage change in the mark price.")
    timeValue: Optional[float] = Field(None, description="Time value component of the premium.")
    intrinsicValue: Optional[float] = Field(None, description="Intrinsic (in-the-money) value.")

    # -------------------------------------------------------------------------
    # Volume / open interest
    # -------------------------------------------------------------------------
    totalVolume: Optional[int] = Field(None, description="Total contracts traded today.")
    openInterest: Optional[int] = Field(None, description="Number of open contracts.")

    # -------------------------------------------------------------------------
    # Greeks
    # -------------------------------------------------------------------------
    delta: Optional[float] = Field(None, description="Delta.")
    gamma: Optional[float] = Field(None, description="Gamma.")
    theta: Optional[float] = Field(None, description="Theta – time decay per day.")
    vega: Optional[float] = Field(None, description="Vega.")
    rho: Optional[float] = Field(None, description="Rho.")

    # -------------------------------------------------------------------------
    # Volatility / probability
    # -------------------------------------------------------------------------
    volatility: Optional[float] = Field(None, description="Implied volatility (annualised %).")
    theoreticalOptionValue: Optional[float] = Field(None, description="Theoretical fair value.")
    theoreticalVolatility: Optional[float] = Field(None, description="Theoretical volatility.")
    percentChange: Optional[float] = Field(None, description="Percentage change in option price.")

    # -------------------------------------------------------------------------
    # Status flags
    # -------------------------------------------------------------------------
    inTheMoney: Optional[bool] = Field(None, description="True when the contract is in-the-money.")
    pennyPilot: Optional[bool] = Field(None, description="True for penny pilot contracts.")
    nonStandard: Optional[bool] = Field(None, description="True for non-standard contracts.")
    mini: Optional[bool] = Field(None, description="True for mini-option contracts.")

    # -------------------------------------------------------------------------
    # Multiplier / misc
    # -------------------------------------------------------------------------
    multiplier: Optional[float] = Field(None, description="Contract multiplier.")

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    tradeTimeInLong: Optional[int] = Field(None, description="Last trade time (Unix ms).")
    quoteTimeInLong: Optional[int] = Field(None, description="Last quote time (Unix ms).")

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
        },
    }


class TradabilityMetrics(BaseModel):
    symbol: str = Field(..., description="Option contract symbol (RowKey).")
    underlying_symbol: str = Field(..., description="Underlying equity/ETF symbol.")
    delta: Optional[float] = Field(None, description="Delta greek value.")
    theta: Optional[float] = Field(None, description="Theta greek value (time decay per day).")
    iv: Optional[float] = Field(None, description="Implied volatility (annualised %).")
    premium: Optional[float] = Field(None, description="Mid-point mark price used as premium.")


class TradabilityScore(BaseModel):
    symbol: str = Field(..., description="Option contract symbol (RowKey).")
    underlying_symbol: str = Field(..., description="Underlying equity/ETF symbol.")
    score: float = Field(..., description="Weighted tradability score.")
    delta: Optional[float] = Field(None, description="Delta used in scoring.")
    theta: Optional[float] = Field(None, description="Theta used in scoring.")
    iv: Optional[float] = Field(None, description="Implied volatility used in scoring.")
    premium: Optional[float] = Field(None, description="Premium used in scoring.")


class BestTradeResponse(BaseModel):
    best_candidate: Optional[TradabilityScore] = Field(None)
    ranked_candidates: List[TradabilityScore] = Field(default_factory=list)

    def to_entity_dict(self) -> dict:
        data = self.model_dump()
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data

    @classmethod
    def build_row_key(
        cls,
        underlying_symbol: str,
        expiration_date: str,
        strike_price: float,
        contract_type: str,
    ) -> str:
        type_char = contract_type[0].upper() if contract_type else "X"
        return f"{underlying_symbol}_{expiration_date}_{strike_price}_{type_char}"
