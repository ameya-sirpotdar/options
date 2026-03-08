from datetime import datetime, timezone
from backend.models.run_log import RunLogRecord


def test_run_log_record_required_fields():
    record = RunLogRecord(
        runId="run-001",
        startTime=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        endTime=datetime(2024, 1, 15, 10, 0, 5, tzinfo=timezone.utc),
        status="success",
        contractsFetched=42,
    )
    assert record.runId == "run-001"
    assert record.status == "success"
    assert record.contractsFetched == 42
    assert record.errorMessage is None
    assert record.symbol is None


def test_run_log_record_with_all_fields():
    start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    end = datetime(2024, 1, 15, 10, 0, 7, tzinfo=timezone.utc)
    record = RunLogRecord(
        runId="run-002",
        startTime=start,
        endTime=end,
        status="failure",
        contractsFetched=0,
        errorMessage="Connection timeout",
        symbol="AAPL",
        underlyingPrice=185.50,
        pollingIntervalSeconds=60,
    )
    assert record.runId == "run-002"
    assert record.status == "failure"
    assert record.contractsFetched == 0
    assert record.errorMessage == "Connection timeout"
    assert record.symbol == "AAPL"
    assert record.underlyingPrice == 185.50
    assert record.pollingIntervalSeconds == 60


def test_run_log_record_partition_key_defaults_to_run_log():
    record = RunLogRecord(
        runId="run-003",
        startTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        endTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        status="success",
        contractsFetched=10,
    )
    assert record.partitionKey == "RunLog"


def test_run_log_record_row_key_defaults_to_run_id():
    record = RunLogRecord(
        runId="run-004",
        startTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        endTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        status="success",
        contractsFetched=5,
    )
    assert record.rowKey == "run-004"


def test_run_log_record_custom_partition_and_row_key():
    record = RunLogRecord(
        runId="run-005",
        partitionKey="CustomPartition",
        rowKey="custom-row-key",
        startTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        endTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        status="success",
        contractsFetched=0,
    )
    assert record.partitionKey == "CustomPartition"
    assert record.rowKey == "custom-row-key"


def test_run_log_record_duration_seconds():
    start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    end = datetime(2024, 1, 15, 10, 0, 30, tzinfo=timezone.utc)
    record = RunLogRecord(
        runId="run-006",
        startTime=start,
        endTime=end,
        status="success",
        contractsFetched=20,
    )
    duration = (record.endTime - record.startTime).total_seconds()
    assert duration == 30.0


def test_run_log_record_status_values():
    for status in ["success", "failure", "partial"]:
        record = RunLogRecord(
            runId=f"run-{status}",
            startTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
            endTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
            status=status,
            contractsFetched=0,
        )
        assert record.status == status


def test_run_log_record_contracts_fetched_zero():
    record = RunLogRecord(
        runId="run-007",
        startTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        endTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        status="failure",
        contractsFetched=0,
        errorMessage="API unavailable",
    )
    assert record.contractsFetched == 0
    assert record.errorMessage == "API unavailable"


def test_run_log_record_to_dict():
    start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    end = datetime(2024, 1, 15, 10, 0, 5, tzinfo=timezone.utc)
    record = RunLogRecord(
        runId="run-008",
        startTime=start,
        endTime=end,
        status="success",
        contractsFetched=15,
        symbol="SPY",
    )
    data = record.model_dump()
    assert data["runId"] == "run-008"
    assert data["status"] == "success"
    assert data["contractsFetched"] == 15
    assert data["symbol"] == "SPY"
    assert data["startTime"] == start
    assert data["endTime"] == end


def test_run_log_record_underlying_price_none_by_default():
    record = RunLogRecord(
        runId="run-009",
        startTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        endTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        status="success",
        contractsFetched=3,
    )
    assert record.underlyingPrice is None


def test_run_log_record_polling_interval_none_by_default():
    record = RunLogRecord(
        runId="run-010",
        startTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        endTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        status="success",
        contractsFetched=3,
    )
    assert record.pollingIntervalSeconds is None


def test_run_log_record_large_contracts_fetched():
    record = RunLogRecord(
        runId="run-011",
        startTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        endTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        status="success",
        contractsFetched=10000,
    )
    assert record.contractsFetched == 10000


def test_run_log_record_error_message_with_success_status():
    record = RunLogRecord(
        runId="run-012",
        startTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        endTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        status="success",
        contractsFetched=5,
        errorMessage="Minor warning logged",
    )
    assert record.status == "success"
    assert record.errorMessage == "Minor warning logged"


def test_run_log_record_model_fields_present():
    record = RunLogRecord(
        runId="run-013",
        startTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        endTime=datetime(2024, 1, 15, tzinfo=timezone.utc),
        status="success",
        contractsFetched=0,
    )
    fields = record.model_fields
    assert "runId" in fields
    assert "startTime" in fields
    assert "endTime" in fields
    assert "status" in fields
    assert "contractsFetched" in fields
    assert "errorMessage" in fields
    assert "symbol" in fields
    assert "underlyingPrice" in fields
    assert "pollingIntervalSeconds" in fields
    assert "partitionKey" in fields
    assert "rowKey" in fields