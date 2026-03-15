from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Any

from azure.core.exceptions import AzureError
from azure.data.tables import TableServiceClient, UpdateMode

from backend.models.options_data import OptionsContractRecord
from backend.models.run_log import RunLogRecord

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


class PersistenceError(Exception):
    """Raised when a persistence operation fails."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class AzureTableService:
    """Thin wrapper around the azure-data-tables SDK.

    Parameters
    ----------
    connection_string:
        Azure Storage connection string.
    options_table:
        Override the default ``optionsdata`` table name.
    runlog_table:
        Override the default ``runlogs`` table name.
    options_table_name:
        Alias for ``options_table`` (backwards compat).
    run_log_table_name:
        Alias for ``runlog_table`` (backwards compat).
    """

    OPTIONS_TABLE: str = "optionsdata"
    RUN_LOG_TABLE: str = "runlogs"

    def __init__(
        self,
        connection_string: str,
        options_table: str | None = None,
        runlog_table: str | None = None,
        # backwards-compat aliases
        options_table_name: str | None = None,
        run_log_table_name: str | None = None,
    ) -> None:
        self._connection_string = connection_string
        self._options_table_name = options_table or options_table_name or self.OPTIONS_TABLE
        self._run_log_table_name = runlog_table or run_log_table_name or self.RUN_LOG_TABLE

        try:
            self._service_client: TableServiceClient = (
                TableServiceClient.from_connection_string(connection_string)
            )
        except Exception as exc:
            raise PersistenceError(
                f"Failed to create TableServiceClient: {exc}", cause=exc
            ) from exc

        self._options_client = self._service_client.get_table_client(self._options_table_name)
        self._run_log_client = self._service_client.get_table_client(self._run_log_table_name)

    # ------------------------------------------------------------------
    # Table management
    # ------------------------------------------------------------------

    def ensure_tables_exist(self) -> None:
        """Create the options and run-log tables if they do not yet exist."""
        for table_name in (self._options_table_name, self._run_log_table_name):
            try:
                self._service_client.create_table_if_not_exists(table_name)
            except Exception as exc:
                raise PersistenceError(
                    f"Unable to ensure table '{table_name}' exists: {exc}", cause=exc
                ) from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _chunk(items: list[Any], size: int):
        """Yield successive *size*-length chunks from *items*."""
        for i in range(0, len(items), size):
            yield items[i : i + size]

    @staticmethod
    def _contract_to_entity(record: OptionsContractRecord) -> dict[str, Any]:
        """Serialise a contract record to an ATS entity dict.

        - PartitionKey = runId
        - RowKey = symbol
        - None values are excluded
        - datetime values are converted to ISO strings
        """
        raw = record.model_dump(mode="json")
        entity: dict[str, Any] = {
            "PartitionKey": str(record.runId),
            "RowKey": str(record.symbol),
        }
        for key, value in raw.items():
            if key in ("PartitionKey", "RowKey"):
                continue
            if value is None:
                continue
            entity[key] = value
        return entity

    @staticmethod
    def _runlog_to_entity(record: RunLogRecord) -> dict[str, Any]:
        """Serialise a run log record to an ATS entity dict.

        - PartitionKey = underlyingSymbol (or "RunLog" fallback)
        - RowKey = runId
        - None values are excluded
        - datetime values are converted to ISO strings
        """
        underlying = record.underlyingSymbol or record.symbol or "RunLog"
        entity: dict[str, Any] = {
            "PartitionKey": str(underlying),
            "RowKey": str(record.runId),
        }
        raw = record.model_dump(mode="json")
        for key, value in raw.items():
            if key in ("PartitionKey", "RowKey", "partitionKey", "rowKey"):
                continue
            if value is None:
                continue
            entity[key] = value
        return entity

    # ------------------------------------------------------------------
    # Public API — contracts
    # ------------------------------------------------------------------

    def upsert_contracts(self, records: list[OptionsContractRecord]) -> None:
        """Persist a list of options contract records using batch upsert."""
        if not records:
            logger.debug("upsert_contracts called with empty list – nothing to do.")
            return

        total_chunks = math.ceil(len(records) / BATCH_SIZE)
        logger.info(
            "Upserting %d options contract record(s) in %d batch(es).",
            len(records),
            total_chunks,
        )

        for chunk_index, chunk in enumerate(self._chunk(records, BATCH_SIZE), start=1):
            operations = [("upsert", self._contract_to_entity(r)) for r in chunk]
            try:
                self._options_client.submit_transaction(operations)
                logger.debug(
                    "Batch %d/%d committed (%d entities).",
                    chunk_index,
                    total_chunks,
                    len(operations),
                )
            except Exception as exc:
                raise PersistenceError(
                    f"Batch upsert failed for options contracts "
                    f"(chunk {chunk_index}/{total_chunks}): {exc}",
                    cause=exc,
                ) from exc

    def upsert_options_contracts(self, records: list[OptionsContractRecord]) -> None:
        """Alias for upsert_contracts (backwards compat)."""
        return self.upsert_contracts(records)

    def get_options_contracts(
        self,
        partition_key: str | None = None,
        *,
        select: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Query options contract entities.

        If ``partition_key`` is given, filters to that partition only.
        Otherwise returns all entities (up to SDK limits).
        """
        try:
            if partition_key:
                filter_expr = f"PartitionKey eq '{partition_key}'"
                entities = self._options_client.query_entities(
                    query_filter=filter_expr,
                    select=select,
                )
            else:
                entities = self._options_client.list_entities(select=select)
            return list(entities)
        except AzureError as exc:
            raise PersistenceError(
                f"Failed to query options contracts: {exc}",
                cause=exc,
            ) from exc

    # ------------------------------------------------------------------
    # Public API — run logs
    # ------------------------------------------------------------------

    def upsert_run_log(self, record: RunLogRecord) -> None:
        """Persist a single run log record."""
        entity = self._runlog_to_entity(record)
        try:
            self._run_log_client.upsert_entity(entity)
            logger.info("Run log record persisted: runId=%s", record.runId)
        except Exception as exc:
            raise PersistenceError(
                f"Failed to upsert run log record (runId={record.runId}): {exc}",
                cause=exc,
            ) from exc

    def get_run_logs(
        self,
        partition_key: str | None = None,
        *,
        select: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Query run log entities."""
        try:
            if partition_key:
                filter_expr = f"PartitionKey eq '{partition_key}'"
                entities = self._run_log_client.query_entities(
                    query_filter=filter_expr,
                    select=select,
                )
            else:
                entities = self._run_log_client.list_entities(select=select)
            return list(entities)
        except AzureError as exc:
            raise PersistenceError(
                f"Failed to query run logs: {exc}",
                cause=exc,
            ) from exc
