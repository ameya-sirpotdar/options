from __future__ import annotations

import logging
import math
from typing import Any

from azure.core.exceptions import AzureError
from azure.data.tables import TableServiceClient, UpdateMode

from backend.models.options_data import OptionsContractRecord
from backend.models.run_log import RunLogRecord

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


class PersistenceError(Exception):
    """Raised when a persistence operation fails after retries."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class AzureTableService:
    """Thin wrapper around the azure-data-tables SDK.

    Provides typed upsert helpers for options contract records and run log
    records.  All writes use *merge* semantics so that partial updates do not
    wipe existing columns.

    Parameters
    ----------
    connection_string:
        Azure Storage connection string.  Must grant read/write access to the
        ``optionsdata`` and ``runlogs`` tables (which are created on first use
        if they do not already exist).
    options_table_name:
        Override the default ``optionsdata`` table name (useful in tests).
    run_log_table_name:
        Override the default ``runlogs`` table name (useful in tests).
    """

    OPTIONS_TABLE: str = "optionsdata"
    RUN_LOG_TABLE: str = "runlogs"

    def __init__(
        self,
        connection_string: str,
        options_table_name: str | None = None,
        run_log_table_name: str | None = None,
    ) -> None:
        self._connection_string = connection_string
        self._options_table_name = options_table_name or self.OPTIONS_TABLE
        self._run_log_table_name = run_log_table_name or self.RUN_LOG_TABLE

        try:
            self._service_client: TableServiceClient = (
                TableServiceClient.from_connection_string(connection_string)
            )
        except Exception as exc:
            raise PersistenceError(
                f"Failed to create TableServiceClient: {exc}", cause=exc
            ) from exc

        self._options_client = self._get_or_create_table(self._options_table_name)
        self._run_log_client = self._get_or_create_table(self._run_log_table_name)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_create_table(self, table_name: str):
        """Return a TableClient, creating the table if it does not exist."""
        try:
            return self._service_client.create_table_if_not_exists(table_name)
        except AzureError as exc:
            raise PersistenceError(
                f"Unable to get or create table '{table_name}': {exc}", cause=exc
            ) from exc

    @staticmethod
    def _record_to_entity(record: OptionsContractRecord | RunLogRecord) -> dict[str, Any]:
        """Serialise a Pydantic model to an ATS-compatible entity dict.

        Azure Table Storage requires ``PartitionKey`` and ``RowKey`` as plain
        strings.  All other fields are included as-is; Pydantic's
        ``model_dump`` converts ``datetime`` objects to ISO strings which ATS
        accepts.
        """
        data = record.model_dump(mode="json")
        entity: dict[str, Any] = {
            "PartitionKey": str(data.pop("PartitionKey")),
            "RowKey": str(data.pop("RowKey")),
        }
        entity.update(data)
        return entity

    @staticmethod
    def _chunk(items: list[Any], size: int):
        """Yield successive *size*-length chunks from *items*."""
        for i in range(0, len(items), size):
            yield items[i : i + size]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upsert_options_contracts(self, records: list[OptionsContractRecord]) -> None:
        """Persist a list of options contract records using batch upsert.

        Records are written in chunks of up to 100 entities (the ATS batch
        limit).  Each chunk is submitted as a single transaction.  On failure
        the exception is re-raised as a :class:`PersistenceError`.

        Parameters
        ----------
        records:
            List of :class:`~backend.models.options_data.OptionsContractRecord`
            instances to persist.
        """
        if not records:
            logger.debug("upsert_options_contracts called with empty list – nothing to do.")
            return

        total_chunks = math.ceil(len(records) / BATCH_SIZE)
        logger.info(
            "Upserting %d options contract record(s) in %d batch(es).",
            len(records),
            total_chunks,
        )

        for chunk_index, chunk in enumerate(self._chunk(records, BATCH_SIZE), start=1):
            entities = [self._record_to_entity(r) for r in chunk]
            operations = [("upsert", entity, {"mode": UpdateMode.MERGE}) for entity in entities]
            try:
                self._options_client.submit_transaction(operations)
                logger.debug(
                    "Batch %d/%d committed (%d entities).",
                    chunk_index,
                    total_chunks,
                    len(entities),
                )
            except AzureError as exc:
                raise PersistenceError(
                    f"Batch upsert failed for options contracts "
                    f"(chunk {chunk_index}/{total_chunks}): {exc}",
                    cause=exc,
                ) from exc

    def upsert_run_log(self, record: RunLogRecord) -> None:
        """Persist a single run log record.

        Parameters
        ----------
        record:
            :class:`~backend.models.run_log.RunLogRecord` instance to persist.
        """
        entity = self._record_to_entity(record)
        try:
            self._run_log_client.upsert_entity(entity=entity, mode=UpdateMode.MERGE)
            logger.info("Run log record persisted: runId=%s", record.runId)
        except AzureError as exc:
            raise PersistenceError(
                f"Failed to upsert run log record (runId={record.runId}): {exc}",
                cause=exc,
            ) from exc

    def get_options_contracts(
        self,
        partition_key: str,
        *,
        select: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Query all options contract entities for a given partition key.

        Parameters
        ----------
        partition_key:
            The partition key to filter on (typically the underlying symbol).
        select:
            Optional list of column names to project.  When *None* all columns
            are returned.

        Returns
        -------
        list[dict[str, Any]]
            Raw entity dicts as returned by the SDK.
        """
        filter_expr = f"PartitionKey eq '{partition_key}'"
        try:
            entities = self._options_client.query_entities(
                query_filter=filter_expr,
                select=select,
            )
            return list(entities)
        except AzureError as exc:
            raise PersistenceError(
                f"Failed to query options contracts for partition '{partition_key}': {exc}",
                cause=exc,
            ) from exc

    def get_run_logs(
        self,
        partition_key: str,
        *,
        select: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Query run log entities for a given partition key.

        Parameters
        ----------
        partition_key:
            The partition key to filter on (typically the symbol or a date
            string).
        select:
            Optional list of column names to project.

        Returns
        -------
        list[dict[str, Any]]
            Raw entity dicts as returned by the SDK.
        """
        filter_expr = f"PartitionKey eq '{partition_key}'"
        try:
            entities = self._run_log_client.query_entities(
                query_filter=filter_expr,
                select=select,
            )
            return list(entities)
        except AzureError as exc:
            raise PersistenceError(
                f"Failed to query run logs for partition '{partition_key}': {exc}",
                cause=exc,
            ) from exc