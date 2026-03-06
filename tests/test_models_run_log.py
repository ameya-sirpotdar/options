from datetime import datetime, timezone
from unittest.mock import patch
import pytest
from backend.models.run_log import RunLog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_entity() -> dict:
    """Return a minimal valid Azure Table entity dict for RunLog."""
    return {
        "PartitionKey": "2024-01-15",
        "RowKey": "run-001",
        "status": "success",
        "created_at": "2024-01-15T10:30:00+00:00",
        "message": "Completed successfully",
    }


def _make_run_log(**overrides) -> RunLog:
    """Construct a RunLog with sensible defaults, applying any overrides."""
    defaults = dict(
        partition_key="2024-01-15",
        row_key="run-001",
        status="success",
        created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        message="Completed successfully",
    )
    defaults.update(overrides)
    return RunLog(**defaults)


# ---------------------------------------------------------------------------
# Construction & defaults
# ---------------------------------------------------------------------------

class TestRunLogConstruction:
    def test_minimal_required_fields(self):
        run_log = RunLog(
            partition_key="2024-01-15",
            row_key="run-001",
            status="success",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        )
        assert run_log.partition_key == "2024-01-15"
        assert run_log.row_key == "run-001"
        assert run_log.status == "success"
        assert run_log.message is None

    def test_all_fields(self):
        run_log = _make_run_log()
        assert run_log.partition_key == "2024-01-15"
        assert run_log.row_key == "run-001"
        assert run_log.status == "success"
        assert run_log.created_at == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert run_log.message == "Completed successfully"

    def test_message_defaults_to_none(self):
        run_log = RunLog(
            partition_key="2024-01-15",
            row_key="run-001",
            status="pending",
            created_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        assert run_log.message is None

    def test_status_running(self):
        run_log = _make_run_log(status="running")
        assert run_log.status == "running"

    def test_status_failed(self):
        run_log = _make_run_log(status="failed", message="Something went wrong")
        assert run_log.status == "failed"
        assert run_log.message == "Something went wrong"

    def test_status_pending(self):
        run_log = _make_run_log(status="pending")
        assert run_log.status == "pending"

    def test_long_message(self):
        long_msg = "Error: " + "x" * 500
        run_log = _make_run_log(status="failed", message=long_msg)
        assert run_log.message == long_msg

    def test_empty_message_string(self):
        run_log = _make_run_log(message="")
        assert run_log.message == ""


# ---------------------------------------------------------------------------
# PartitionKey validation (run_date format)
# ---------------------------------------------------------------------------

class TestPartitionKeyValidation:
    def test_valid_iso_date(self):
        run_log = _make_run_log(partition_key="2024-01-15")
        assert run_log.partition_key == "2024-01-15"

    def test_valid_date_start_of_year(self):
        run_log = _make_run_log(partition_key="2024-01-01")
        assert run_log.partition_key == "2024-01-01"

    def test_valid_date_end_of_year(self):
        run_log = _make_run_log(partition_key="2024-12-31")
        assert run_log.partition_key == "2024-12-31"

    def test_empty_partition_key_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key="")

    def test_partition_key_with_slash_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key="2024/01/15")

    def test_partition_key_with_backslash_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key="2024\\01\\15")

    def test_partition_key_with_hash_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key="2024#01#15")

    def test_partition_key_with_question_mark_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key="2024?01?15")

    def test_partition_key_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key="   ")

    def test_partition_key_leading_whitespace_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key=" 2024-01-15")

    def test_partition_key_trailing_whitespace_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key="2024-01-15 ")

    def test_partition_key_none_raises(self):
        with pytest.raises((ValueError, TypeError)):
            _make_run_log(partition_key=None)


# ---------------------------------------------------------------------------
# RowKey validation (run_id)
# ---------------------------------------------------------------------------

class TestRowKeyValidation:
    def test_valid_run_id(self):
        run_log = _make_run_log(row_key="run-001")
        assert run_log.row_key == "run-001"

    def test_valid_uuid_style_run_id(self):
        run_log = _make_run_log(row_key="550e8400-e29b-41d4-a716-446655440000")
        assert run_log.row_key == "550e8400-e29b-41d4-a716-446655440000"

    def test_valid_numeric_run_id(self):
        run_log = _make_run_log(row_key="12345")
        assert run_log.row_key == "12345"

    def test_valid_timestamp_run_id(self):
        run_log = _make_run_log(row_key="20240115T103000Z")
        assert run_log.row_key == "20240115T103000Z"

    def test_empty_row_key_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="")

    def test_row_key_with_slash_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="run/001")

    def test_row_key_with_backslash_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="run\\001")

    def test_row_key_with_hash_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="run#001")

    def test_row_key_with_question_mark_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="run?001")

    def test_row_key_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="   ")

    def test_row_key_leading_whitespace_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key=" run-001")

    def test_row_key_trailing_whitespace_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="run-001 ")

    def test_row_key_none_raises(self):
        with pytest.raises((ValueError, TypeError)):
            _make_run_log(row_key=None)


# ---------------------------------------------------------------------------
# Status field validation
# ---------------------------------------------------------------------------

class TestStatusValidation:
    def test_status_success(self):
        run_log = _make_run_log(status="success")
        assert run_log.status == "success"

    def test_status_failed(self):
        run_log = _make_run_log(status="failed")
        assert run_log.status == "failed"

    def test_status_running(self):
        run_log = _make_run_log(status="running")
        assert run_log.status == "running"

    def test_status_pending(self):
        run_log = _make_run_log(status="pending")
        assert run_log.status == "pending"

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError):
            _make_run_log(status="unknown")

    def test_empty_status_raises(self):
        with pytest.raises(ValueError):
            _make_run_log(status="")

    def test_uppercase_status_raises(self):
        with pytest.raises(ValueError):
            _make_run_log(status="SUCCESS")

    def test_mixed_case_status_raises(self):
        with pytest.raises(ValueError):
            _make_run_log(status="Success")

    def test_status_none_raises(self):
        with pytest.raises((ValueError, TypeError)):
            _make_run_log(status=None)


# ---------------------------------------------------------------------------
# created_at field validation
# ---------------------------------------------------------------------------

class TestCreatedAtValidation:
    def test_utc_datetime(self):
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        run_log = _make_run_log(created_at=dt)
        assert run_log.created_at == dt

    def test_naive_datetime_raises(self):
        naive_dt = datetime(2024, 1, 15, 10, 30, 0)
        with pytest.raises(ValueError, match="timezone"):
            _make_run_log(created_at=naive_dt)

    def test_created_at_none_raises(self):
        with pytest.raises((ValueError, TypeError)):
            _make_run_log(created_at=None)

    def test_iso_string_parsed(self):
        run_log = _make_run_log(created_at="2024-01-15T10:30:00+00:00")
        assert run_log.created_at.year == 2024
        assert run_log.created_at.month == 1
        assert run_log.created_at.day == 15

    def test_created_at_preserves_microseconds(self):
        dt = datetime(2024, 1, 15, 10, 30, 0, 123456, tzinfo=timezone.utc)
        run_log = _make_run_log(created_at=dt)
        assert run_log.created_at.microsecond == 123456


# ---------------------------------------------------------------------------
# to_entity()
# ---------------------------------------------------------------------------

class TestToEntity:
    def test_returns_dict(self):
        run_log = _make_run_log()
        entity = run_log.to_entity()
        assert isinstance(entity, dict)

    def test_partition_key_present(self):
        run_log = _make_run_log(partition_key="2024-01-15")
        entity = run_log.to_entity()
        assert entity["PartitionKey"] == "2024-01-15"

    def test_row_key_present(self):
        run_log = _make_run_log(row_key="run-001")
        entity = run_log.to_entity()
        assert entity["RowKey"] == "run-001"

    def test_status_present(self):
        run_log = _make_run_log(status="success")
        entity = run_log.to_entity()
        assert entity["status"] == "success"

    def test_created_at_is_iso_string(self):
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        run_log = _make_run_log(created_at=dt)
        entity = run_log.to_entity()
        assert isinstance(entity["created_at"], str)
        assert "2024-01-15" in entity["created_at"]

    def test_message_present_when_set(self):
        run_log = _make_run_log(message="All good")
        entity = run_log.to_entity()
        assert entity["message"] == "All good"

    def test_message_absent_when_none(self):
        run_log = RunLog(
            partition_key="2024-01-15",
            row_key="run-001",
            status="success",
            created_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        entity = run_log.to_entity()
        assert "message" not in entity or entity.get("message") is None

    def test_no_python_internal_fields(self):
        run_log = _make_run_log()
        entity = run_log.to_entity()
        assert "partition_key" not in entity
        assert "row_key" not in entity

    def test_failed_status_entity(self):
        run_log = _make_run_log(status="failed", message="DB connection error")
        entity = run_log.to_entity()
        assert entity["status"] == "failed"
        assert entity["message"] == "DB connection error"

    def test_running_status_entity(self):
        run_log = _make_run_log(status="running", message=None)
        entity = run_log.to_entity()
        assert entity["status"] == "running"


# ---------------------------------------------------------------------------
# from_entity()
# ---------------------------------------------------------------------------

class TestFromEntity:
    def test_roundtrip_basic(self):
        entity = _valid_entity()
        run_log = RunLog.from_entity(entity)
        assert run_log.partition_key == entity["PartitionKey"]
        assert run_log.row_key == entity["RowKey"]
        assert run_log.status == entity["status"]
        assert run_log.message == entity["message"]

    def test_partition_key_mapped(self):
        entity = _valid_entity()
        run_log = RunLog.from_entity(entity)
        assert run_log.partition_key == "2024-01-15"

    def test_row_key_mapped(self):
        entity = _valid_entity()
        run_log = RunLog.from_entity(entity)
        assert run_log.row_key == "run-001"

    def test_status_mapped(self):
        entity = _valid_entity()
        run_log = RunLog.from_entity(entity)
        assert run_log.status == "success"

    def test_created_at_parsed_from_string(self):
        entity = _valid_entity()
        run_log = RunLog.from_entity(entity)
        assert isinstance(run_log.created_at, datetime)
        assert run_log.created_at.tzinfo is not None

    def test_message_mapped(self):
        entity = _valid_entity()
        run_log = RunLog.from_entity(entity)
        assert run_log.message == "Completed successfully"

    def test_missing_message_defaults_to_none(self):
        entity = _valid_entity()
        del entity["message"]
        run_log = RunLog.from_entity(entity)
        assert run_log.message is None

    def test_failed_status_from_entity(self):
        entity = _valid_entity()
        entity["status"] = "failed"
        entity["message"] = "Timeout error"
        run_log = RunLog.from_entity(entity)
        assert run_log.status == "failed"
        assert run_log.message == "Timeout error"

    def test_running_status_from_entity(self):
        entity = _valid_entity()
        entity["status"] = "running"
        run_log = RunLog.from_entity(entity)
        assert run_log.status == "running"

    def test_pending_status_from_entity(self):
        entity = _valid_entity()
        entity["status"] = "pending"
        run_log = RunLog.from_entity(entity)
        assert run_log.status == "pending"

    def test_extra_azure_metadata_ignored(self):
        entity = _valid_entity()
        entity["odata.etag"] = "W/\"datetime'2024-01-15T10%3A30%3A00.0000000Z'\""
        entity["Timestamp"] = "2024-01-15T10:30:00Z"
        run_log = RunLog.from_entity(entity)
        assert run_log.partition_key == "2024-01-15"

    def test_missing_partition_key_raises(self):
        entity = _valid_entity()
        del entity["PartitionKey"]
        with pytest.raises((ValueError, KeyError)):
            RunLog.from_entity(entity)

    def test_missing_row_key_raises(self):
        entity = _valid_entity()
        del entity["RowKey"]
        with pytest.raises((ValueError, KeyError)):
            RunLog.from_entity(entity)

    def test_missing_status_raises(self):
        entity = _valid_entity()
        del entity["status"]
        with pytest.raises((ValueError, KeyError)):
            RunLog.from_entity(entity)

    def test_missing_created_at_raises(self):
        entity = _valid_entity()
        del entity["created_at"]
        with pytest.raises((ValueError, KeyError)):
            RunLog.from_entity(entity)


# ---------------------------------------------------------------------------
# Full serialization round-trip
# ---------------------------------------------------------------------------

class TestSerializationRoundTrip:
    def test_to_entity_then_from_entity(self):
        original = _make_run_log()
        entity = original.to_entity()
        restored = RunLog.from_entity(entity)
        assert restored.partition_key == original.partition_key
        assert restored.row_key == original.row_key
        assert restored.status == original.status
        assert restored.message == original.message

    def test_created_at_roundtrip_preserves_utc(self):
        dt = datetime(2024, 6, 15, 14, 45, 30, tzinfo=timezone.utc)
        original = _make_run_log(created_at=dt)
        entity = original.to_entity()
        restored = RunLog.from_entity(entity)
        assert restored.created_at.year == 2024
        assert restored.created_at.month == 6
        assert restored.created_at.day == 15
        assert restored.created_at.hour == 14
        assert restored.created_at.minute == 45
        assert restored.created_at.second == 30

    def test_roundtrip_with_none_message(self):
        original = RunLog(
            partition_key="2024-03-20",
            row_key="run-999",
            status="pending",
            created_at=datetime(2024, 3, 20, tzinfo=timezone.utc),
        )
        entity = original.to_entity()
        restored = RunLog.from_entity(entity)
        assert restored.message is None

    def test_roundtrip_failed_status(self):
        original = _make_run_log(
            status="failed",
            message="Critical failure in data pipeline",
        )
        entity = original.to_entity()
        restored = RunLog.from_entity(entity)
        assert restored.status == "failed"
        assert restored.message == "Critical failure in data pipeline"

    def test_roundtrip_running_status(self):
        original = _make_run_log(status="running", message="Processing batch 3 of 10")
        entity = original.to_entity()
        restored = RunLog.from_entity(entity)
        assert restored.status == "running"
        assert restored.message == "Processing batch 3 of 10"

    def test_multiple_roundtrips_stable(self):
        original = _make_run_log()
        entity1 = original.to_entity()
        restored1 = RunLog.from_entity(entity1)
        entity2 = restored1.to_entity()
        restored2 = RunLog.from_entity(entity2)
        assert restored2.partition_key == original.partition_key
        assert restored2.row_key == original.row_key
        assert restored2.status == original.status


# ---------------------------------------------------------------------------
# Table name
# ---------------------------------------------------------------------------

class TestTableName:
    def test_table_name_attribute_exists(self):
        assert hasattr(RunLog, "TABLE_NAME") or hasattr(RunLog, "table_name")

    def test_table_name_is_runlogs(self):
        name = getattr(RunLog, "TABLE_NAME", None) or getattr(RunLog, "table_name", None)
        assert name == "runlogs"


# ---------------------------------------------------------------------------
# Immutability / model config
# ---------------------------------------------------------------------------

class TestModelConfig:
    def test_model_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(RunLog, BaseModel)

    def test_instance_has_expected_fields(self):
        run_log = _make_run_log()
        assert hasattr(run_log, "partition_key")
        assert hasattr(run_log, "row_key")
        assert hasattr(run_log, "status")
        assert hasattr(run_log, "created_at")
        assert hasattr(run_log, "message")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_unicode_message(self):
        run_log = _make_run_log(message="Erreur: données invalides — café ☕")
        assert "café" in run_log.message

    def test_message_with_newlines(self):
        run_log = _make_run_log(message="Line 1\nLine 2\nLine 3")
        assert "\n" in run_log.message

    def test_run_id_with_dots(self):
        run_log = _make_run_log(row_key="run.2024.001")
        assert run_log.row_key == "run.2024.001"

    def test_run_id_alphanumeric(self):
        run_log = _make_run_log(row_key="abc123XYZ")
        assert run_log.row_key == "abc123XYZ"

    def test_partition_key_different_year(self):
        run_log = _make_run_log(partition_key="2023-06-30")
        assert run_log.partition_key == "2023-06-30"

    def test_entity_keys_are_strings(self):
        run_log = _make_run_log()
        entity = run_log.to_entity()
        for key in entity:
            assert isinstance(key, str)

    def test_entity_status_is_string(self):
        run_log = _make_run_log(status="success")
        entity = run_log.to_entity()
        assert isinstance(entity["status"], str)

    def test_from_entity_is_classmethod(self):
        import inspect
        assert isinstance(inspect.getattr_static(RunLog, "from_entity"), classmethod)