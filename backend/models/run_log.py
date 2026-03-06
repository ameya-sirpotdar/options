from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import field_validator, model_validator

from .base import AzureTableModel


class RunLog(AzureTableModel):
    """
    Model for the *runlogs* Azure Table Storage table.

    Schema
    ------
    PartitionKey : str
        The calendar date of the run in ``YYYY-MM-DD`` format, e.g.
        ``"2024-01-15"``.  Grouping rows by date keeps related runs in the
        same storage partition and makes date-range queries efficient.

    RowKey : str
        A UUID-4 string that uniquely identifies this individual run, e.g.
        ``"550e8400-e29b-41d4-a716-446655440000"``.

    status : str
        Current status of the run.  Expected values are ``"pending"``,
        ``"running"``, ``"success"``, or ``"failed"``, but the field is not
        restricted to those values so that callers can extend it without a
        schema migration.

    created_at : str
        ISO-8601 UTC timestamp recorded when the run entity was first
        persisted, e.g. ``"2024-01-15T10:30:00+00:00"``.

    message : str
        Human-readable description or error detail for the run.  Defaults to
        an empty string so that callers do not have to supply it for
        successful runs.
    """

    status: str
    created_at: str
    message: str = ""

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("PartitionKey")
    @classmethod
    def validate_partition_key(cls, value: str) -> str:
        """Ensure PartitionKey looks like a ``YYYY-MM-DD`` date string."""
        value = value.strip()
        if not value:
            raise ValueError("PartitionKey (run_date) must not be empty.")
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"PartitionKey must be a date in YYYY-MM-DD format, got: {value!r}"
            )
        return value

    @field_validator("RowKey")
    @classmethod
    def validate_row_key(cls, value: str) -> str:
        """Ensure RowKey is a valid UUID-4 string."""
        value = value.strip()
        if not value:
            raise ValueError("RowKey (run_id) must not be empty.")
        try:
            parsed = uuid.UUID(value, version=4)
        except ValueError:
            raise ValueError(
                f"RowKey must be a valid UUID-4 string, got: {value!r}"
            )
        # Normalise to the canonical lower-case hyphenated form.
        return str(parsed)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """Strip whitespace and reject empty status strings."""
        value = value.strip()
        if not value:
            raise ValueError("status must not be empty.")
        return value

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: str) -> str:
        """Ensure *created_at* is a parseable ISO-8601 timestamp string."""
        value = value.strip()
        if not value:
            raise ValueError("created_at must not be empty.")
        try:
            datetime.fromisoformat(value)
        except ValueError:
            raise ValueError(
                f"created_at must be an ISO-8601 timestamp string, got: {value!r}"
            )
        return value

    @model_validator(mode="after")
    def validate_azure_key_characters(self) -> RunLog:
        """
        Azure Table Storage forbids the characters ``/``, ``\\``, ``#``,
        ``?``, and control characters (U+0000–U+001F, U+007F–U+009F) in
        both PartitionKey and RowKey.  The date format and UUID format
        already prevent most of these, but we validate explicitly to surface
        clear error messages.
        """
        forbidden = set("/\\#?")
        for field_name, value in (
            ("PartitionKey", self.PartitionKey),
            ("RowKey", self.RowKey),
        ):
            bad = forbidden.intersection(value)
            if bad:
                raise ValueError(
                    f"{field_name} contains forbidden Azure Table Storage "
                    f"character(s): {bad!r}"
                )
            for ch in value:
                code = ord(ch)
                if (0x0000 <= code <= 0x001F) or (0x007F <= code <= 0x009F):
                    raise ValueError(
                        f"{field_name} contains a forbidden control character "
                        f"(U+{code:04X})."
                    )
        return self

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        run_date: str,
        status: str,
        message: str = "",
        run_id: str | None = None,
        created_at: str | None = None,
    ) -> RunLog:
        """
        Convenience constructor that fills in *run_id* and *created_at*
        automatically when they are not supplied.

        Parameters
        ----------
        run_date:
            Calendar date of the run in ``YYYY-MM-DD`` format.
        status:
            Status string for the run.
        message:
            Optional human-readable description or error detail.
        run_id:
            UUID-4 string.  A new UUID is generated when omitted.
        created_at:
            ISO-8601 UTC timestamp.  The current UTC time is used when
            omitted.

        Returns
        -------
        RunLog
            A fully validated :class:`RunLog` instance.
        """
        if run_id is None:
            run_id = str(uuid.uuid4())
        if created_at is None:
            created_at = datetime.now(tz=timezone.utc).isoformat()
        return cls(
            PartitionKey=run_date,
            RowKey=run_id,
            status=status,
            created_at=created_at,
            message=message,
        )

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_entity(self) -> dict[str, Any]:
        """
        Serialise the model to a flat dictionary suitable for writing to
        Azure Table Storage via the ``azure-data-tables`` SDK.

        All field values are returned as their native Python types; the SDK
        handles the underlying EDM type mapping.

        Returns
        -------
        dict[str, Any]
            A dictionary with keys ``PartitionKey``, ``RowKey``,
            ``status``, ``created_at``, and ``message``.
        """
        return {
            "PartitionKey": self.PartitionKey,
            "RowKey": self.RowKey,
            "status": self.status,
            "created_at": self.created_at,
            "message": self.message,
        }

    @classmethod
    def from_entity(cls, entity: dict[str, Any]) -> RunLog:
        """
        Deserialise a raw Azure Table Storage entity dictionary into a
        :class:`RunLog` instance.

        The SDK may return additional metadata keys (e.g. ``Timestamp``,
        ``etag``).  Unknown keys are silently ignored because the model is
        configured with ``extra="ignore"`` in :class:`~.base.AzureTableModel`.

        Parameters
        ----------
        entity:
            Raw entity dictionary returned by the ``azure-data-tables`` SDK.

        Returns
        -------
        RunLog
            A fully validated :class:`RunLog` instance.
        """
        return cls(
            PartitionKey=str(entity["PartitionKey"]),
            RowKey=str(entity["RowKey"]),
            status=str(entity["status"]),
            created_at=str(entity["created_at"]),
            message=str(entity.get("message", "")),
        )

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RunLog("
            f"run_date={self.PartitionKey!r}, "
            f"run_id={self.RowKey!r}, "
            f"status={self.status!r}, "
            f"created_at={self.created_at!r}, "
            f"message={self.message!r})"
        )