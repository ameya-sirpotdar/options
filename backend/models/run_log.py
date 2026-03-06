from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import field_validator, model_validator

from .base import AzureTableModel


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class RunLog(AzureTableModel):
    """
    Azure Table Storage schema for the `runlogs` table.

    Partition key: run_date  (YYYY-MM-DD)
    Row key:       run_id    (non-empty string, no forbidden Azure key chars)

    Additional fields
    -----------------
    status  : RunStatus  – lifecycle state of the run
    message : str | None – optional human-readable detail / error text
    """

    run_date: str
    run_id: str
    status: RunStatus
    message: Optional[str] = None

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("run_date")
    @classmethod
    def validate_run_date(cls, value: str) -> str:
        import re

        pattern = r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$"
        if not re.match(pattern, value):
            raise ValueError(
                f"run_date must be in YYYY-MM-DD format, got: {value!r}"
            )
        cls._check_azure_key_chars(value, "run_date")
        return value

    @field_validator("run_id")
    @classmethod
    def validate_run_id(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("run_id must be a non-empty string")
        cls._check_azure_key_chars(value, "run_id")
        return value

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(value) > 32_768:
            raise ValueError(
                "message must not exceed 32,768 characters (Azure Table Storage limit)"
            )
        return value

    # ------------------------------------------------------------------
    # AzureTableModel interface
    # ------------------------------------------------------------------

    def to_entity(self) -> dict[str, Any]:
        """
        Serialise to an Azure Table Storage entity dict.

        PartitionKey = run_date
        RowKey       = run_id
        """
        entity: dict[str, Any] = {
            "PartitionKey": self.run_date,
            "RowKey": self.run_id,
            "status": self.status.value,
        }
        if self.message is not None:
            entity["message"] = self.message
        return entity

    @classmethod
    def from_entity(cls, entity: dict[str, Any]) -> "RunLog":
        """
        Deserialise from an Azure Table Storage entity dict.

        Expects at minimum: PartitionKey, RowKey, status.
        """
        return cls(
            run_date=entity["PartitionKey"],
            run_id=entity["RowKey"],
            status=RunStatus(entity["status"]),
            message=entity.get("message"),
        )