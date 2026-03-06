from datetime import datetime, timezone
import pytest
from backend.models.run_log import RunLog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_entity() -> dict:
    """Valid Azure Table entity — PartitionKey=run_id, RowKey=run_date."""
    return {
        "PartitionKey": "run-001",
        "RowKey": "2024-01-15",
        "status": "success",
        "created_at": "2024-01-15T10:30:00+00:00",
        "message": "Completed successfully",
    }


def _make_run_log(**overrides) -> RunLog:
    defaults = dict(
        partition_key="run-001",
        row_key="2024-01-15",
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
            partition_key="run-001",
            row_key="2024-01-15",
            status="success",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        )
        assert run_log.partition_key == "run-001"
        assert run_log.row_key == "2024-01-15"
        assert run_log.status == "success"
        assert run_log.message is None

    def test_all_fields(self):
        run_log = _make_run_log()
        assert run_log.partition_key == "run-001"
        assert run_log.row_key == "2024-01-15"
        assert run_log.status == "success"
        assert run_log.created_at == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert run_log.message == "Completed successfully"

    def test_message_defaults_to_none(self):
        run_log = RunLog(
            partition_key="run-001",
            row_key="2024-01-15",
            status="pending",
            created_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        assert run_log.message is None

    def test_status_running(self):
        assert _make_run_log(status="running").status == "running"

    def test_status_failed(self):
        run_log = _make_run_log(status="failed", message="Something went wrong")
        assert run_log.status == "failed"
        assert run_log.message == "Something went wrong"

    def test_status_pending(self):
        assert _make_run_log(status="pending").status == "pending"

    def test_long_message(self):
        long_msg = "Error: " + "x" * 500
        assert _make_run_log(status="failed", message=long_msg).message == long_msg

    def test_empty_message_string(self):
        assert _make_run_log(message="").message == ""


# ---------------------------------------------------------------------------
# PartitionKey validation (run_id — any valid non-empty string)
# ---------------------------------------------------------------------------

class TestPartitionKeyValidation:
    def test_valid_run_id(self):
        assert _make_run_log(partition_key="run-001").partition_key == "run-001"

    def test_valid_uuid_run_id(self):
        uid = "550e8400-e29b-41d4-a716-446655440000"
        assert _make_run_log(partition_key=uid).partition_key == uid

    def test_valid_numeric_run_id(self):
        assert _make_run_log(partition_key="12345").partition_key == "12345"

    def test_empty_partition_key_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key="")

    def test_partition_key_with_slash_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key="run/001")

    def test_partition_key_with_backslash_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key="run\\001")

    def test_partition_key_with_hash_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key="run#001")

    def test_partition_key_with_question_mark_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key="run?001")

    def test_partition_key_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key="   ")

    def test_partition_key_leading_whitespace_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key=" run-001")

    def test_partition_key_trailing_whitespace_raises(self):
        with pytest.raises(ValueError, match="PartitionKey"):
            _make_run_log(partition_key="run-001 ")

    def test_partition_key_none_raises(self):
        with pytest.raises((ValueError, TypeError)):
            _make_run_log(partition_key=None)


# ---------------------------------------------------------------------------
# RowKey validation (run_date — YYYY-MM-DD format)
# ---------------------------------------------------------------------------

class TestRowKeyValidation:
    def test_valid_iso_date(self):
        assert _make_run_log(row_key="2024-01-15").row_key == "2024-01-15"

    def test_valid_date_start_of_year(self):
        assert _make_run_log(row_key="2024-01-01").row_key == "2024-01-01"

    def test_valid_date_end_of_year(self):
        assert _make_run_log(row_key="2024-12-31").row_key == "2024-12-31"

    def test_empty_row_key_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="")

    def test_row_key_with_slash_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="2024/01/15")

    def test_row_key_with_backslash_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="2024\\01\\15")

    def test_row_key_with_hash_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="2024#01#15")

    def test_row_key_with_question_mark_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="2024?01?15")

    def test_row_key_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="   ")

    def test_row_key_leading_whitespace_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key=" 2024-01-15")

    def test_row_key_trailing_whitespace_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="2024-01-15 ")

    def test_row_key_none_raises(self):
        with pytest.raises((ValueError, TypeError)):
            _make_run_log(row_key=None)

    def test_row_key_not_a_date_raises(self):
        with pytest.raises(ValueError, match="RowKey"):
            _make_run_log(row_key="run-001")


# ---------------------------------------------------------------------------
# Status validation
# ---------------------------------------------------------------------------

class TestStatusValidation:
    def test_status_success(self):
        assert _make_run_log(status="success").status == "success"

    def test_status_failed(self):
        assert _make_run_log(status="failed").status == "failed"

    def test_status_running(self):
        assert _make_run_log(status="running").status == "running"

    def test_status_pending(self):
        assert _make_run_log(status="pending").status == "pending"

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
# created_at validation
# ---------------------------------------------------------------------------

class TestCreatedAtValidation:
    def test_utc_datetime(self):
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert _make_run_log(created_at=dt).created_at == dt

    def test_naive_datetime_raises(self):
        with pytest.raises(ValueError, match="timezone"):
            _make_run_log(created_at=datetime(2024, 1, 15, 10, 30, 0))

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
        assert _make_run_log(created_at=dt).created_at.microsecond == 123456


# ---------------------------------------------------------------------------
# to_entity()
# ---------------------------------------------------------------------------

class TestToEntity:
    def test_returns_dict(self):
        assert isinstance(_make_run_log().to_entity(), dict)

    def test_partition_key_is_run_id(self):
        entity = _make_run_log(partition_key="run-001").to_entity()
        assert entity["PartitionKey"] == "run-001"

    def test_row_key_is_run_date(self):
        entity = _make_run_log(row_key="2024-01-15").to_entity()
        assert entity["RowKey"] == "2024-01-15"

    def test_status_present(self):
        assert _make_run_log(status="success").to_entity()["status"] == "success"

    def test_created_at_is_iso_string(self):
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        entity = _make_run_log(created_at=dt).to_entity()
        assert isinstance(entity["created_at"], str)
        assert "2024-01-15" in entity["created_at"]

    def test_message_present_when_set(self):
        entity = _make_run_log(message="All good").to_entity()
        assert entity["message"] == "All good"

    def test_message_absent_when_none(self):
        entity = RunLog(
            partition_key="run-001",
            row_key="2024-01-15",
            status="success",
            created_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        ).to_entity()
        assert "message" not in entity or entity.get("message") is None

    def test_no_python_field_names(self):
        entity = _make_run_log().to_entity()
        assert "partition_key" not in entity
        assert "row_key" not in entity


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
        assert RunLog.from_entity(_valid_entity()).partition_key == "run-001"

    def test_row_key_mapped(self):
        assert RunLog.from_entity(_valid_entity()).row_key == "2024-01-15"

    def test_created_at_parsed_from_string(self):
        run_log = RunLog.from_entity(_valid_entity())
        assert isinstance(run_log.created_at, datetime)
        assert run_log.created_at.tzinfo is not None

    def test_missing_message_defaults_to_none(self):
        entity = _valid_entity()
        del entity["message"]
        assert RunLog.from_entity(entity).message is None

    def test_extra_azure_metadata_ignored(self):
        entity = _valid_entity()
        entity["odata.etag"] = "W/\"datetime'2024-01-15T10%3A30%3A00Z'\""
        entity["Timestamp"] = "2024-01-15T10:30:00Z"
        assert RunLog.from_entity(entity).partition_key == "run-001"

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
# Serialization round-trip
# ---------------------------------------------------------------------------

class TestSerializationRoundTrip:
    def test_to_entity_then_from_entity(self):
        original = _make_run_log()
        restored = RunLog.from_entity(original.to_entity())
        assert restored.partition_key == original.partition_key
        assert restored.row_key == original.row_key
        assert restored.status == original.status
        assert restored.message == original.message

    def test_created_at_roundtrip_preserves_utc(self):
        dt = datetime(2024, 6, 15, 14, 45, 30, tzinfo=timezone.utc)
        restored = RunLog.from_entity(_make_run_log(created_at=dt).to_entity())
        assert restored.created_at.year == 2024
        assert restored.created_at.hour == 14
        assert restored.created_at.minute == 45

    def test_roundtrip_with_none_message(self):
        original = RunLog(
            partition_key="run-999",
            row_key="2024-03-20",
            status="pending",
            created_at=datetime(2024, 3, 20, tzinfo=timezone.utc),
        )
        restored = RunLog.from_entity(original.to_entity())
        assert restored.message is None

    def test_multiple_roundtrips_stable(self):
        original = _make_run_log()
        e1 = original.to_entity()
        r1 = RunLog.from_entity(e1)
        r2 = RunLog.from_entity(r1.to_entity())
        assert r2.partition_key == original.partition_key
        assert r2.row_key == original.row_key
        assert r2.status == original.status


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
# Model config
# ---------------------------------------------------------------------------

class TestModelConfig:
    def test_model_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(RunLog, BaseModel)

    def test_instance_has_expected_fields(self):
        run_log = _make_run_log()
        for attr in ("partition_key", "row_key", "status", "created_at", "message"):
            assert hasattr(run_log, attr)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_unicode_message(self):
        assert "café" in _make_run_log(message="café ☕").message

    def test_message_with_newlines(self):
        assert "\n" in _make_run_log(message="Line 1\nLine 2").message

    def test_run_id_with_dots(self):
        assert _make_run_log(partition_key="run.2024.001").partition_key == "run.2024.001"

    def test_entity_keys_are_strings(self):
        for key in _make_run_log().to_entity():
            assert isinstance(key, str)

    def test_from_entity_is_classmethod(self):
        import inspect
        assert isinstance(inspect.getattr_static(RunLog, "from_entity"), classmethod)
