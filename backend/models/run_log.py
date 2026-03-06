from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, field_validator


_INVALID_KEY_CHARS = re.compile(r'[/\\#?\x00-\x1f\x7f-\x9f]')
_ALLOWED_STATUSES = {"pending", "running", "success", "failed"}


class RunLog(BaseModel):
    """
    Pydantic v2 model for rows in the *runlogs* Azure Table Storage table.

    Schema (reversed from naive design for query efficiency)
    -------------------------------------------------------
    PartitionKey : run_id   – unique run identifier; spread across partitions
                              to avoid hot-partition on a single date
    RowKey       : run_date – calendar date in YYYY-MM-DD format

    Fields
    ------
    partition_key : str      – run_id (becomes PartitionKey in the entity)
    row_key       : str      – run_date in YYYY-MM-DD format (becomes RowKey)
    status        : str      – one of: pending | running | success | failed
    created_at    : datetime – timezone-aware UTC datetime
    message       : str|None – optional human-readable description or error
    """

    TABLE_NAME: ClassVar[str] = "runlogs"

    partition_key: str
    row_key: str
    status: str
    created_at: datetime
    message: Optional[str] = None

    model_config = {"extra": "ignore"}

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("partition_key")
    @classmethod
    def validate_partition_key(cls, value: str) -> str:
        """run_id: non-empty string, no Azure-forbidden chars, no surrounding whitespace."""
        if value != value.strip():
            raise ValueError("PartitionKey must not have leading or trailing whitespace")
        if not value.strip():
            raise ValueError("PartitionKey must not be empty")
        if _INVALID_KEY_CHARS.search(value):
            raise ValueError(
                f"PartitionKey contains invalid Azure Table Storage key characters: {value!r}"
            )
        return value

    @field_validator("row_key")
    @classmethod
    def validate_row_key(cls, value: str) -> str:
        """run_date: must be YYYY-MM-DD format, no surrounding whitespace."""
        if value != value.strip():
            raise ValueError("RowKey must not have leading or trailing whitespace")
        if not value.strip():
            raise ValueError("RowKey must not be empty")
        if _INVALID_KEY_CHARS.search(value):
            raise ValueError(
                f"RowKey contains invalid Azure Table Storage key characters: {value!r}"
            )
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"RowKey (run_date) must be YYYY-MM-DD format, got: {value!r}")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in _ALLOWED_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(_ALLOWED_STATUSES)}, got: {value!r}"
            )
        return value

    @field_validator("created_at", mode="before")
    @classmethod
    def validate_created_at(cls, value: Any) -> datetime:
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                raise ValueError(f"created_at must be a valid ISO-8601 datetime string, got: {value!r}")
        if not isinstance(value, datetime):
            raise TypeError(f"created_at must be a datetime, got {type(value)}")
        if value.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        return value

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_entity(self) -> dict[str, Any]:
        """Serialise to Azure Table Storage entity dict."""
        entity: dict[str, Any] = {
            "PartitionKey": self.partition_key,
            "RowKey": self.row_key,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
        if self.message is not None:
            entity["message"] = self.message
        return entity

    @classmethod
    def from_entity(cls, entity: dict[str, Any]) -> "RunLog":
        """Reconstruct from an Azure Table Storage entity dict."""
        return cls(
            partition_key=str(entity["PartitionKey"]),
            row_key=str(entity["RowKey"]),
            status=str(entity["status"]),
            created_at=entity["created_at"],
            message=str(entity["message"]) if entity.get("message") is not None else None,
        )

    # ------------------------------------------------------------------
    # Factory helper
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        run_date: str,
        status: str,
        message: Optional[str] = None,
        run_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> "RunLog":
        """Convenience constructor — auto-generates run_id and created_at if omitted."""
        if run_id is None:
            run_id = str(uuid.uuid4())
        if created_at is None:
            created_at = datetime.now(tz=timezone.utc)
        return cls(
            partition_key=run_id,
            row_key=run_date,
            status=status,
            created_at=created_at,
            message=message,
        )