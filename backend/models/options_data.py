from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, field_validator


_INVALID_KEY_CHARS = re.compile(r'[/\\#?\x00-\x1f\x7f-\x9f]')


class OptionsData(BaseModel):
    """
    Pydantic v2 model for rows in the *optionsdata* Azure Table Storage table.

    Dual-write schema
    -----------------
    The same record is written twice to enable bidirectional queries:

      Write 1 (by ticker): PartitionKey = ticker, RowKey = expiry
        → "give me all expiries for AAPL"

      Write 2 (by expiry): PartitionKey = expiry, RowKey = ticker
        → "give me all tickers expiring 2024-02-16"

    Use :meth:`to_entity` for write 1, :meth:`to_expiry_entity` for write 2,
    or :meth:`both_entities` to get both at once.

    Fields
    ------
    ticker    : str   – ticker symbol (e.g. "AAPL", "BRK.B")
    expiry    : str   – option expiration date in YYYY-MM-DD format
    strike    : float – strike price (must be > 0)
    delta     : float – option delta (−1.0 … 1.0)
    theta     : float – option theta
    iv        : float – implied volatility as a decimal fraction (≥ 0)
    premium   : float – option premium / last price (≥ 0)
    timestamp : str   – optional ISO-8601 capture timestamp
    """

    ticker: str
    expiry: str
    strike: float
    delta: float
    theta: float
    iv: float
    premium: float
    timestamp: Optional[str] = None

    model_config = {"frozen": True, "extra": "ignore"}

    # ------------------------------------------------------------------ #
    # Validators                                                           #
    # ------------------------------------------------------------------ #

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not v:
            raise ValueError("ticker must not be empty")
        if _INVALID_KEY_CHARS.search(v):
            raise ValueError(
                f"ticker contains invalid Azure Table Storage key characters: {v!r}"
            )
        return v

    @field_validator("expiry")
    @classmethod
    def validate_expiry(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"expiry must be YYYY-MM-DD format, got {v!r}")
        return v

    @field_validator("strike")
    @classmethod
    def validate_strike(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"strike must be > 0, got {v}")
        return v

    @field_validator("delta")
    @classmethod
    def validate_delta(cls, v: float) -> float:
        if not (-1.0 <= v <= 1.0):
            raise ValueError(f"delta must be between -1.0 and 1.0, got {v}")
        return v

    @field_validator("iv")
    @classmethod
    def validate_iv(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"iv must be >= 0, got {v}")
        return v

    @field_validator("premium")
    @classmethod
    def validate_premium(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"premium must be >= 0, got {v}")
        return v

    # ------------------------------------------------------------------ #
    # Serialisation helpers                                                #
    # ------------------------------------------------------------------ #

    def _base_fields(self) -> dict[str, Any]:
        entity: dict[str, Any] = {
            "strike": float(self.strike),
            "delta": float(self.delta),
            "theta": float(self.theta),
            "iv": float(self.iv),
            "premium": float(self.premium),
        }
        if self.timestamp is not None:
            entity["timestamp"] = self.timestamp
        return entity

    def to_entity(self) -> dict[str, Any]:
        """Write 1: PartitionKey=ticker, RowKey=expiry."""
        return {"PartitionKey": self.ticker, "RowKey": self.expiry, **self._base_fields()}

    def to_expiry_entity(self) -> dict[str, Any]:
        """Write 2: PartitionKey=expiry, RowKey=ticker."""
        return {"PartitionKey": self.expiry, "RowKey": self.ticker, **self._base_fields()}

    def both_entities(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Return (ticker_entity, expiry_entity) for dual-write."""
        return self.to_entity(), self.to_expiry_entity()

    @classmethod
    def from_entity(cls, entity: dict[str, Any]) -> "OptionsData":
        """
        Reconstruct from a primary entity (PartitionKey=ticker, RowKey=expiry).
        """
        return cls(
            ticker=str(entity["PartitionKey"]),
            expiry=str(entity["RowKey"]),
            strike=float(entity["strike"]),
            delta=float(entity["delta"]),
            theta=float(entity["theta"]),
            iv=float(entity["iv"]),
            premium=float(entity["premium"]),
            timestamp=str(entity["timestamp"]) if "timestamp" in entity else None,  # type: ignore[arg-type]
        )