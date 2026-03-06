from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from pydantic import field_validator, model_validator

from .base import AzureTableModel

# Characters that are forbidden in Azure Table Storage partition and row keys
_AZURE_KEY_FORBIDDEN = re.compile(r'[/\\#?\x00-\x1f\x7f-\x9f]')

# Expected timestamp format stored in RowKey
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"

# Valid option types
_VALID_OPTION_TYPES = frozenset({"call", "put"})


def _check_azure_key(value: str, field_name: str) -> str:
    """Raise ValueError if *value* contains characters forbidden in Azure Table keys."""
    if _AZURE_KEY_FORBIDDEN.search(value):
        raise ValueError(
            f"{field_name!r} contains characters that are forbidden in Azure Table "
            f"Storage partition or row keys (/, \\, #, ?, and control characters)."
        )
    return value


class OptionsData(AzureTableModel):
    """
    Azure Table Storage entity for a single options contract data point.

    Table name : ``optionsdata``

    Partition key
        The underlying ticker symbol (e.g. ``"AAPL"``).  Upper-cased on
        assignment and validated to contain only alphanumeric characters plus
        ``-`` and ``.``.

    Row key
        A UTC timestamp string in ``YYYYMMDDTHHMMSSz`` format
        (e.g. ``"20240115T143022Z"``).  Uniquely identifies the snapshot
        within a ticker's partition.

    All remaining fields describe the options contract itself.
    """

    # ------------------------------------------------------------------ #
    # Identity / key fields                                                #
    # ------------------------------------------------------------------ #

    ticker: str
    """Underlying ticker symbol – becomes the PartitionKey."""

    timestamp: str
    """UTC snapshot timestamp in ``YYYYMMDDTHHMMSSz`` format – becomes the RowKey."""

    # ------------------------------------------------------------------ #
    # Contract description fields                                          #
    # ------------------------------------------------------------------ #

    option_type: str
    """``"call"`` or ``"put"``."""

    expiration_date: str
    """Option expiration date in ``YYYY-MM-DD`` format."""

    strike_price: float
    """Strike price of the contract (must be positive)."""

    # ------------------------------------------------------------------ #
    # Market data fields                                                   #
    # ------------------------------------------------------------------ #

    underlying_price: float
    """Spot price of the underlying asset at snapshot time (must be positive)."""

    bid: float
    """Bid price of the option (must be >= 0)."""

    ask: float
    """Ask price of the option (must be >= 0)."""

    volume: int
    """Trading volume for the session (must be >= 0)."""

    open_interest: int
    """Open interest at snapshot time (must be >= 0)."""

    implied_volatility: float
    """Implied volatility as a decimal fraction (e.g. ``0.25`` for 25 %)."""

    # ------------------------------------------------------------------ #
    # Optional Greeks                                                      #
    # ------------------------------------------------------------------ #

    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None

    # ================================================================== #
    # Validators                                                           #
    # ================================================================== #

    @field_validator("ticker", mode="before")
    @classmethod
    def _validate_ticker(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("ticker must be a string.")
        v = v.strip().upper()
        if not v:
            raise ValueError("ticker must not be empty.")
        if not re.fullmatch(r"[A-Z0-9.\-]+", v):
            raise ValueError(
                "ticker must contain only alphanumeric characters, hyphens, or dots."
            )
        _check_azure_key(v, "ticker")
        return v

    @field_validator("timestamp", mode="before")
    @classmethod
    def _validate_timestamp(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("timestamp must be a string.")
        v = v.strip()
        if not v:
            raise ValueError("timestamp must not be empty.")
        try:
            datetime.strptime(v, _TIMESTAMP_FORMAT)
        except ValueError:
            raise ValueError(
                f"timestamp must be in '{_TIMESTAMP_FORMAT}' format "
                f"(e.g. '20240115T143022Z').  Got: {v!r}"
            )
        _check_azure_key(v, "timestamp")
        return v

    @field_validator("option_type", mode="before")
    @classmethod
    def _validate_option_type(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("option_type must be a string.")
        v = v.strip().lower()
        if v not in _VALID_OPTION_TYPES:
            raise ValueError(
                f"option_type must be one of {sorted(_VALID_OPTION_TYPES)}.  Got: {v!r}"
            )
        return v

    @field_validator("expiration_date", mode="before")
    @classmethod
    def _validate_expiration_date(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("expiration_date must be a string.")
        v = v.strip()
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"expiration_date must be in 'YYYY-MM-DD' format.  Got: {v!r}"
            )
        _check_azure_key(v, "expiration_date")
        return v

    @field_validator("strike_price", "underlying_price", mode="before")
    @classmethod
    def _validate_positive_float(cls, v: object) -> float:
        try:
            fv = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            raise ValueError("Value must be a number.")
        if fv <= 0:
            raise ValueError("Value must be strictly positive (> 0).")
        return fv

    @field_validator("bid", "ask", mode="before")
    @classmethod
    def _validate_non_negative_float(cls, v: object) -> float:
        try:
            fv = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            raise ValueError("Value must be a number.")
        if fv < 0:
            raise ValueError("Value must be non-negative (>= 0).")
        return fv

    @field_validator("volume", "open_interest", mode="before")
    @classmethod
    def _validate_non_negative_int(cls, v: object) -> int:
        try:
            iv = int(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            raise ValueError("Value must be an integer.")
        if iv < 0:
            raise ValueError("Value must be non-negative (>= 0).")
        return iv

    @field_validator("implied_volatility", mode="before")
    @classmethod
    def _validate_implied_volatility(cls, v: object) -> float:
        try:
            fv = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            raise ValueError("implied_volatility must be a number.")
        if fv < 0:
            raise ValueError("implied_volatility must be non-negative (>= 0).")
        return fv

    # ================================================================== #
    # AzureTableModel interface                                            #
    # ================================================================== #

    @property
    def partition_key(self) -> str:  # noqa: D102
        return self.ticker

    @property
    def row_key(self) -> str:  # noqa: D102
        return self.timestamp

    # ================================================================== #
    # Convenience constructors                                             #
    # ================================================================== #

    @classmethod
    def from_datetime(cls, dt: datetime, **kwargs: object) -> "OptionsData":
        """
        Construct an :class:`OptionsData` instance using a :class:`~datetime.datetime`
        object for the *timestamp* field instead of a pre-formatted string.

        The datetime is converted to UTC and formatted as ``YYYYMMDDTHHMMSSz``.

        Parameters
        ----------
        dt:
            The snapshot datetime.  If *dt* is naive it is assumed to be UTC.
        **kwargs:
            All other fields required by :class:`OptionsData`.
        """
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
        timestamp = dt.strftime(_TIMESTAMP_FORMAT)
        return cls(timestamp=timestamp, **kwargs)  # type: ignore[arg-type]

    def to_datetime(self) -> datetime:
        """
        Parse :attr:`timestamp` back into a timezone-aware UTC
        :class:`~datetime.datetime`.
        """
        return datetime.strptime(self.timestamp, _TIMESTAMP_FORMAT).replace(
            tzinfo=timezone.utc
        )