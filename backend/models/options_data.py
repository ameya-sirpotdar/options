from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class OptionsContractRecord(BaseModel):
    """
    Pydantic model representing a single options contract record
    as returned by the Schwab API, mapped for Azure Table Storage persistence.

    Partition key: underlying symbol (e.g. "AAPL")
    Row key: unique contract identifier (e.g. "AAPL_2024-01-19_150.0_C")
    """

    # -------------------------------------------------------------------------
    # Azure Table Storage keys
    # -------------------------------------------------------------------------
    PartitionKey: str = Field(
        ...,
        description="Underlying symbol used as the ATS partition key.",
    )
    RowKey: str = Field(
        ...,
        description="Unique contract identifier used as the ATS row key.",
    )

    # -------------------------------------------------------------------------
    # Run / ingestion metadata
    # -------------------------------------------------------------------------
    runId: str = Field(
        ...,
        description="UUID identifying the polling run that produced this record.",
    )
    ingestedAt: datetime = Field(
        ...,
        description="UTC timestamp at which this record was written to storage.",
    )

    # -------------------------------------------------------------------------
    # Contract identity
    # -------------------------------------------------------------------------
    symbol: str = Field(..., description="Option contract symbol.")
    underlyingSymbol: str = Field(..., description="Underlying equity/ETF symbol.")
    description: Optional[str] = Field(None, description="Human-readable contract description.")
    exchangeName: Optional[str] = Field(None, description="Exchange on which the contract trades.")
    contractType: Optional[str] = Field(None, description="'CALL' or 'PUT'.")
    optionDeliverablesList: Optional[str] = Field(
        None,
        description="JSON-serialised list of deliverables (stored as string in ATS).",
    )

    # -------------------------------------------------------------------------
    # Expiration / strike
    # -------------------------------------------------------------------------
    expirationDate: Optional[str] = Field(None, description="Expiration date string (ISO-8601).")
    expirationDateTimestamp: Optional[int] = Field(
        None, description="Expiration date as a Unix epoch millisecond timestamp."
    )
    daysToExpiration: Optional[int] = Field(None, description="Calendar days until expiration.")
    expirationType: Optional[str] = Field(None, description="e.g. 'R' (regular), 'W' (weekly).")
    settlementType: Optional[str] = Field(None, description="e.g. 'A' (AM), 'P' (PM).")
    strikePrice: Optional[float] = Field(None, description="Strike price of the contract.")

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
    netPercentChange: Optional[float] = Field(
        None, description="Net percentage change from previous close."
    )
    markChange: Optional[float] = Field(None, description="Change in the mark price.")
    markPercentChange: Optional[float] = Field(
        None, description="Percentage change in the mark price."
    )

    # -------------------------------------------------------------------------
    # Volume / open interest
    # -------------------------------------------------------------------------
    totalVolume: Optional[int] = Field(None, description="Total contracts traded today.")
    openInterest: Optional[int] = Field(None, description="Number of open contracts.")

    # -------------------------------------------------------------------------
    # Greeks
    # -------------------------------------------------------------------------
    delta: Optional[float] = Field(None, description="Delta – rate of change vs. underlying.")
    gamma: Optional[float] = Field(None, description="Gamma – rate of change of delta.")
    theta: Optional[float] = Field(None, description="Theta – time decay per day.")
    vega: Optional[float] = Field(None, description="Vega – sensitivity to implied volatility.")
    rho: Optional[float] = Field(None, description="Rho – sensitivity to interest rates.")

    # -------------------------------------------------------------------------
    # Volatility / probability
    # -------------------------------------------------------------------------
    volatility: Optional[float] = Field(None, description="Implied volatility (annualised %).")
    theoreticalOptionValue: Optional[float] = Field(
        None, description="Theoretical fair value of the contract."
    )
    theoreticalVolatility: Optional[float] = Field(
        None, description="Theoretical volatility used in pricing model."
    )
    percentChange: Optional[float] = Field(None, description="Percentage change in option price.")
    intrinsicValue: Optional[float] = Field(None, description="Intrinsic (in-the-money) value.")
    extrinsicValue: Optional[float] = Field(None, description="Extrinsic (time) value.")
    optionRoot: Optional[str] = Field(None, description="Root symbol of the option series.")
    inTheMoney: Optional[bool] = Field(None, description="True when the contract is in-the-money.")
    pennyPilot: Optional[bool] = Field(
        None, description="True when the contract participates in the penny pilot programme."
    )
    nonStandard: Optional[bool] = Field(
        None, description="True when the contract has non-standard deliverables."
    )
    mini: Optional[bool] = Field(None, description="True for mini-option contracts.")

    # -------------------------------------------------------------------------
    # Multiplier / misc
    # -------------------------------------------------------------------------
    multiplier: Optional[float] = Field(
        None, description="Contract multiplier (typically 100 for equity options)."
    )
    timeValue: Optional[float] = Field(None, description="Time value component of the premium.")
    bidAskSize: Optional[str] = Field(
        None, description="Combined bid/ask size string as returned by the API."
    )

    # -------------------------------------------------------------------------
    # Timestamps from the API payload
    # -------------------------------------------------------------------------
    tradeTimeInLong: Optional[int] = Field(
        None, description="Last trade time as a Unix epoch millisecond timestamp."
    )
    quoteTimeInLong: Optional[int] = Field(
        None, description="Last quote time as a Unix epoch millisecond timestamp."
    )
    lastTradingDay: Optional[int] = Field(
        None, description="Last trading day as a Unix epoch millisecond timestamp."
    )

    # -------------------------------------------------------------------------
    # Status flags
    # -------------------------------------------------------------------------
    tradingStatus: Optional[str] = Field(
        None, description="Current trading status of the contract."
    )

    # -------------------------------------------------------------------------
    # CCP (Cash Covered Put) calculated fields
    # -------------------------------------------------------------------------
    annualizedRoi: Optional[float] = Field(
        None,
        alias="annualizedRoi",
        description=(
            "Annualized return on investment for a cash-covered put strategy, "
            "expressed as a decimal (e.g. 0.25 = 25%). "
            "Populated only for PUT contracts with sufficient pricing data."
        ),
    )

    class Config:
        # Allow population by field name as well as alias so that raw Schwab
        # API dicts (which use camelCase) can be passed directly.
        populate_by_name = True
        # Serialise datetime objects as ISO-8601 strings for ATS compatibility.
        json_encoders = {datetime: lambda v: v.isoformat()}


class TradabilityMetrics(BaseModel):
    """
    Extracted metrics used as inputs to the tradability scoring formula.
    """

    symbol: str = Field(..., description="Option contract symbol (RowKey).")
    underlying_symbol: str = Field(..., description="Underlying equity/ETF symbol.")
    delta: Optional[float] = Field(None, description="Delta greek value.")
    theta: Optional[float] = Field(None, description="Theta greek value (time decay per day).")
    iv: Optional[float] = Field(None, description="Implied volatility (annualised %).")
    premium: Optional[float] = Field(None, description="Mid-point mark price used as premium.")


class TradabilityScore(BaseModel):
    """
    Tradability score computed for a single options contract candidate.
    """

    symbol: str = Field(..., description="Option contract symbol (RowKey).")
    underlying_symbol: str = Field(..., description="Underlying equity/ETF symbol.")
    score: float = Field(..., description="Weighted tradability score.")
    delta: Optional[float] = Field(None, description="Delta used in scoring.")
    theta: Optional[float] = Field(None, description="Theta used in scoring.")
    iv: Optional[float] = Field(None, description="Implied volatility used in scoring.")
    premium: Optional[float] = Field(None, description="Premium used in scoring.")


class BestTradeResponse(BaseModel):
    """
    Response payload returned by the GET /trades/best endpoint.
    """

    best_candidate: Optional[TradabilityScore] = Field(
        None, description="The highest-scoring trade candidate, or null if none available."
    )
    ranked_candidates: List[TradabilityScore] = Field(
        default_factory=list,
        description="All evaluated candidates ordered from highest to lowest score.",
    )

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def to_entity_dict(self) -> dict:
        """
        Return a flat dictionary suitable for direct insertion into an
        Azure Table Storage entity.  Datetime values are converted to
        ISO-8601 strings so that the ATS SDK can serialise them without
        additional configuration.
        """
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
        """
        Construct a deterministic, human-readable ATS row key from the
        four fields that uniquely identify an options contract.

        Format: ``<SYMBOL>_<EXPIRY>_<STRIKE>_<TYPE>``
        Example: ``AAPL_2024-01-19_150.0_C``
        """
        type_char = contract_type[0].upper() if contract_type else "X"
        return f"{underlying_symbol}_{expiration_date}_{strike_price}_{type_char}"