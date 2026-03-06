from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import field_validator, model_validator

from .base import AzureTableModel


class OptionsData(AzureTableModel):
    """
    Pydantic v2 model representing a row in the *optionsdata* Azure Table Storage table.

    Schema
    ------
    Table name : optionsdata
    PartitionKey : ticker symbol (e.g. "AAPL")
    RowKey       : ISO-8601 timestamp string (e.g. "2024-01-15T09:30:00")

    Additional columns
    ------------------
    expiry    : str   – option expiration date in YYYY-MM-DD format
    strike    : float – strike price (must be > 0)
    delta     : float – option delta  (−1.0 … 1.0)
    theta     : float – option theta  (typically ≤ 0 for long positions)
    iv        : float – implied volatility as a decimal fraction (≥ 0)
    premium   : float – option premium / last price (≥ 0)
    """

    # ------------------------------------------------------------------ #
    # Fields                                                               #
    # ------------------------------------------------------------------ #
    expiry: str
    strike: float
    delta: float
    theta: float
    iv: float
    premium: float

    # ------------------------------------------------------------------ #
    # PartitionKey validator – ticker symbol                               #
    # ------------------------------------------------------------------ #
    @field_validator("PartitionKey")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """
        Ticker symbols must be 1-10 uppercase ASCII letters.
        Azure Table Storage also forbids certain special characters in keys;
        this constraint is a strict subset of those rules.
        """
        if not re.fullmatch(r"[A-Z]{1,10}", v):
            raise ValueError(
                f"PartitionKey (ticker) must be 1-10 uppercase ASCII letters, got {v!r}"
            )
        return v

    # ------------------------------------------------------------------ #
    # RowKey validator – ISO-8601 timestamp                                #
    # ------------------------------------------------------------------ #
    @field_validator("RowKey")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """
        RowKey must be a valid ISO-8601 datetime string.
        Accepted formats:
          • YYYY-MM-DDTHH:MM:SS
          • YYYY-MM-DDTHH:MM:SS.ffffff
        """
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                datetime.strptime(v, fmt)
                return v
            except ValueError:
                continue
        raise ValueError(
            f"RowKey (timestamp) must be an ISO-8601 datetime string, got {v!r}"
        )

    # ------------------------------------------------------------------ #
    # Field validators                                                     #
    # ------------------------------------------------------------------ #
    @field_validator("expiry")
    @classmethod
    def validate_expiry(cls, v: str) -> str:
        """Expiry must be a date string in YYYY-MM-DD format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"expiry must be a date string in YYYY-MM-DD format, got {v!r}"
            )
        return v

    @field_validator("strike")
    @classmethod
    def validate_strike(cls, v: float) -> float:
        """Strike price must be strictly positive."""
        if v <= 0:
            raise ValueError(f"strike must be > 0, got {v}")
        return v

    @field_validator("delta")
    @classmethod
    def validate_delta(cls, v: float) -> float:
        """Delta must be in the range [−1.0, 1.0]."""
        if not (-1.0 <= v <= 1.0):
            raise ValueError(f"delta must be between -1.0 and 1.0, got {v}")
        return v

    @field_validator("iv")
    @classmethod
    def validate_iv(cls, v: float) -> float:
        """Implied volatility must be non-negative."""
        if v < 0:
            raise ValueError(f"iv must be >= 0, got {v}")
        return v

    @field_validator("premium")
    @classmethod
    def validate_premium(cls, v: float) -> float:
        """Premium must be non-negative."""
        if v < 0:
            raise ValueError(f"premium must be >= 0, got {v}")
        return v

    # ------------------------------------------------------------------ #
    # Serialisation helpers                                                #
    # ------------------------------------------------------------------ #
    def to_entity(self) -> dict[str, Any]:
        """
        Serialise the model to a flat dict suitable for upsert into
        Azure Table Storage via the *azure-data-tables* SDK.

        All numeric fields are stored as their native Python float so that
        the SDK maps them to the correct Edm type automatically.
        """
        entity = super().to_entity()
        entity.update(
            {
                "expiry": self.expiry,
                "strike": float(self.strike),
                "delta": float(self.delta),
                "theta": float(self.theta),
                "iv": float(self.iv),
                "premium": float(self.premium),
            }
        )
        return entity

    @classmethod
    def from_entity(cls, entity: dict[str, Any]) -> "OptionsData":
        """
        Deserialise a raw entity dict returned by the *azure-data-tables* SDK
        back into an :class:`OptionsData` instance.

        The SDK may return numeric values as ``EntityProperty`` objects or as
        plain Python scalars; we coerce them to ``float`` defensively.
        """
        return cls(
            PartitionKey=str(entity["PartitionKey"]),
            RowKey=str(entity["RowKey"]),
            expiry=str(entity["expiry"]),
            strike=float(entity["strike"]),
            delta=float(entity["delta"]),
            theta=float(entity["theta"]),
            iv=float(entity["iv"]),
            premium=float(entity["premium"]),
        )