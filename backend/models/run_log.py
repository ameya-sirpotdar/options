from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class RunLogRecord(BaseModel):
    PartitionKey: str = Field(
        default="runlog",
        description="Fixed partition key for all run log records",
    )
    RowKey: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this run log entry (UUID)",
    )
    run_id: str = Field(
        description="Unique identifier for the polling run cycle",
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the polling cycle started",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when the polling cycle completed",
    )
    status: str = Field(
        description="Status of the polling run: 'success', 'partial', or 'failure'",
    )
    symbol: str = Field(
        description="The underlying symbol that was polled (e.g. 'SPY')",
    )
    contracts_fetched: int = Field(
        default=0,
        description="Total number of option contracts returned by the API",
    )
    contracts_persisted: int = Field(
        default=0,
        description="Number of option contracts successfully persisted to storage",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error or warning message if the run encountered problems",
    )
    api_response_time_ms: Optional[float] = Field(
        default=None,
        description="Time in milliseconds taken by the Schwab API call",
    )
    persistence_time_ms: Optional[float] = Field(
        default=None,
        description="Time in milliseconds taken by the Azure Table Storage upsert",
    )
    expiration_date_from: Optional[str] = Field(
        default=None,
        description="The fromDate parameter used in the options chain request",
    )
    expiration_date_to: Optional[str] = Field(
        default=None,
        description="The toDate parameter used in the options chain request",
    )
    option_type: Optional[str] = Field(
        default=None,
        description="The optionType filter used in the request (e.g. 'ALL', 'CALL', 'PUT')",
    )
    strike_count: Optional[int] = Field(
        default=None,
        description="The strikeCount parameter used in the options chain request",
    )

    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
        },
    }

    def to_entity(self) -> dict:
        """
        Serialize this record to a flat dict suitable for Azure Table Storage.
        Datetime fields are converted to ISO 8601 strings.
        None values are omitted to avoid storing null strings in ATS.
        """
        raw = self.model_dump()
        entity: dict = {}
        for key, value in raw.items():
            if value is None:
                continue
            if isinstance(value, datetime):
                entity[key] = value.isoformat()
            else:
                entity[key] = value
        return entity

    @classmethod
    def from_entity(cls, entity: dict) -> "RunLogRecord":
        """
        Reconstruct a RunLogRecord from a raw Azure Table Storage entity dict.
        Converts ISO 8601 string timestamps back to datetime objects.
        """
        data = dict(entity)
        for dt_field in ("started_at", "completed_at"):
            if dt_field in data and isinstance(data[dt_field], str):
                data[dt_field] = datetime.fromisoformat(data[dt_field])
        return cls(**data)