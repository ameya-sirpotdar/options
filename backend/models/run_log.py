from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator
import uuid


class RunLogRecord(BaseModel):
    """
    Record for a single polling run cycle, stored in Azure Table Storage.

    PartitionKey = "RunLog" (logical grouping)
    RowKey = runId (unique per run)
    """

    runId: str = Field(
        description="Unique identifier for the polling run cycle.",
    )
    status: str = Field(
        description="Status of the polling run: 'success', 'partial', or 'failure'.",
    )

    # Timestamps — two name conventions are supported to be compatible with
    # both the existing polling_service and test fixtures.
    startedAt: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when the polling cycle started (camelCase variant).",
    )
    finishedAt: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when the polling cycle finished (camelCase variant).",
    )
    startTime: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when the polling cycle started (alternate name).",
    )
    endTime: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when the polling cycle ended (alternate name).",
    )

    # Contract counts
    contractsFetched: Optional[int] = Field(
        default=None,
        description="Total number of option contracts returned by the API.",
    )
    contractsPersisted: Optional[int] = Field(
        default=None,
        description="Number of option contracts successfully persisted to storage.",
    )
    contractsProcessed: Optional[int] = Field(
        default=None,
        description="Number of option contracts processed in this run.",
    )

    # Ticker / symbol metadata
    tickers: Optional[List[str]] = Field(
        default=None,
        description="List of ticker symbols polled in this run.",
    )
    symbol: Optional[str] = Field(
        default=None,
        description="The underlying symbol that was polled (e.g. 'SPY').",
    )
    underlyingSymbol: Optional[str] = Field(
        default=None,
        description="Underlying symbol (alternate to symbol).",
    )
    underlyingPrice: Optional[float] = Field(
        default=None,
        description="Price of the underlying at poll time.",
    )

    # Miscellaneous
    errorMessage: Optional[str] = Field(
        default=None,
        description="Error or warning message if the run encountered problems.",
    )
    pollingIntervalSeconds: Optional[int] = Field(
        default=None,
        description="Polling interval in seconds.",
    )

    # Azure Table Storage keys
    partitionKey: str = Field(
        default="RunLog",
        description="ATS partition key — fixed to 'RunLog' for all run records.",
    )
    rowKey: Optional[str] = Field(
        default=None,
        description="ATS row key — defaults to runId.",
    )

    @model_validator(mode="after")
    def _set_row_key_default(self) -> "RunLogRecord":
        if self.rowKey is None:
            self.rowKey = self.runId
        return self

    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
        },
    }

    @property
    def PartitionKey(self) -> str:
        return self.partitionKey

    @property
    def RowKey(self) -> str:
        return self.rowKey or self.runId
