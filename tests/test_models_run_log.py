import pytest
from datetime import date, datetime, timezone
from pydantic import ValidationError

from backend.models.run_log import RunLog, RunStatus


class TestRunLogConstruction:
    def test_minimal_valid_run_log(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        assert run_log.run_date == "2024-01-15"
        assert run_log.run_id == "abc123def456"
        assert run_log.status == RunStatus.SUCCESS
        assert run_log.message is None

    def test_full_valid_run_log(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.FAILURE,
            message="Something went wrong during data fetch.",
        )
        assert run_log.run_date == "2024-01-15"
        assert run_log.run_id == "abc123def456"
        assert run_log.status == RunStatus.FAILURE
        assert run_log.message == "Something went wrong during data fetch."

    def test_run_log_with_in_progress_status(self):
        run_log = RunLog(
            run_date="2024-06-30",
            run_id="run20240630001",
            status=RunStatus.IN_PROGRESS,
        )
        assert run_log.status == RunStatus.IN_PROGRESS

    def test_run_log_with_partial_status(self):
        run_log = RunLog(
            run_date="2024-06-30",
            run_id="run20240630001",
            status=RunStatus.PARTIAL,
            message="3 of 5 tickers processed successfully.",
        )
        assert run_log.status == RunStatus.PARTIAL
        assert run_log.message == "3 of 5 tickers processed successfully."

    def test_run_log_status_string_coercion_success(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status="success",
        )
        assert run_log.status == RunStatus.SUCCESS

    def test_run_log_status_string_coercion_failure(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status="failure",
        )
        assert run_log.status == RunStatus.FAILURE

    def test_run_log_status_string_coercion_in_progress(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status="in_progress",
        )
        assert run_log.status == RunStatus.IN_PROGRESS

    def test_run_log_status_string_coercion_partial(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status="partial",
        )
        assert run_log.status == RunStatus.PARTIAL


class TestRunLogPartitionKeyRowKey:
    def test_partition_key_equals_run_date(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        assert run_log.PartitionKey == "2024-01-15"

    def test_row_key_equals_run_id(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        assert run_log.RowKey == "abc123def456"

    def test_partition_key_different_date(self):
        run_log = RunLog(
            run_date="2023-12-31",
            run_id="endofyearrun",
            status=RunStatus.SUCCESS,
        )
        assert run_log.PartitionKey == "2023-12-31"

    def test_row_key_different_run_id(self):
        run_log = RunLog(
            run_date="2023-12-31",
            run_id="endofyearrun",
            status=RunStatus.SUCCESS,
        )
        assert run_log.RowKey == "endofyearrun"


class TestRunLogRunDateValidation:
    def test_valid_run_date_format(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="testrun001",
            status=RunStatus.SUCCESS,
        )
        assert run_log.run_date == "2024-01-15"

    def test_invalid_run_date_format_no_dashes(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="20240115",
                run_id="testrun001",
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_date" in str(e["loc"]) for e in errors)

    def test_invalid_run_date_format_slashes(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024/01/15",
                run_id="testrun001",
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_date" in str(e["loc"]) for e in errors)

    def test_invalid_run_date_format_partial(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024-01",
                run_id="testrun001",
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_date" in str(e["loc"]) for e in errors)

    def test_invalid_run_date_not_a_real_date(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024-13-45",
                run_id="testrun001",
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_date" in str(e["loc"]) for e in errors)

    def test_invalid_run_date_empty_string(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="",
                run_id="testrun001",
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_date" in str(e["loc"]) for e in errors)

    def test_run_date_leap_year_valid(self):
        run_log = RunLog(
            run_date="2024-02-29",
            run_id="leapyearrun",
            status=RunStatus.SUCCESS,
        )
        assert run_log.run_date == "2024-02-29"

    def test_run_date_non_leap_year_feb29_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2023-02-29",
                run_id="notleapyear",
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_date" in str(e["loc"]) for e in errors)

    def test_run_date_azure_forbidden_slash_in_date(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024/01/15",
                run_id="testrun001",
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_date" in str(e["loc"]) for e in errors)


class TestRunLogRunIdValidation:
    def test_valid_run_id_alphanumeric(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        assert run_log.run_id == "abc123def456"

    def test_valid_run_id_with_hyphens(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="run-2024-01-15-001",
            status=RunStatus.SUCCESS,
        )
        assert run_log.run_id == "run-2024-01-15-001"

    def test_valid_run_id_with_underscores(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="run_2024_001",
            status=RunStatus.SUCCESS,
        )
        assert run_log.run_id == "run_2024_001"

    def test_invalid_run_id_empty_string(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024-01-15",
                run_id="",
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_id" in str(e["loc"]) for e in errors)

    def test_invalid_run_id_azure_forbidden_forward_slash(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024-01-15",
                run_id="run/001",
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_id" in str(e["loc"]) for e in errors)

    def test_invalid_run_id_azure_forbidden_backslash(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024-01-15",
                run_id="run\\001",
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_id" in str(e["loc"]) for e in errors)

    def test_invalid_run_id_azure_forbidden_hash(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024-01-15",
                run_id="run#001",
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_id" in str(e["loc"]) for e in errors)

    def test_invalid_run_id_azure_forbidden_question_mark(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024-01-15",
                run_id="run?001",
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_id" in str(e["loc"]) for e in errors)

    def test_invalid_run_id_too_long(self):
        long_run_id = "r" * 1025
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024-01-15",
                run_id=long_run_id,
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_id" in str(e["loc"]) for e in errors)

    def test_valid_run_id_max_length(self):
        max_run_id = "r" * 1024
        run_log = RunLog(
            run_date="2024-01-15",
            run_id=max_run_id,
            status=RunStatus.SUCCESS,
        )
        assert len(run_log.run_id) == 1024


class TestRunLogStatusValidation:
    def test_invalid_status_string(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024-01-15",
                run_id="testrun001",
                status="unknown_status",
            )
        errors = exc_info.value.errors()
        assert any("status" in str(e["loc"]) for e in errors)

    def test_invalid_status_integer(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024-01-15",
                run_id="testrun001",
                status=42,
            )
        errors = exc_info.value.errors()
        assert any("status" in str(e["loc"]) for e in errors)

    def test_invalid_status_none(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024-01-15",
                run_id="testrun001",
                status=None,
            )
        errors = exc_info.value.errors()
        assert any("status" in str(e["loc"]) for e in errors)

    def test_all_valid_status_enum_values(self):
        for status in RunStatus:
            run_log = RunLog(
                run_date="2024-01-15",
                run_id="testrun001",
                status=status,
            )
            assert run_log.status == status


class TestRunLogToEntity:
    def test_to_entity_basic_structure(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        entity = run_log.to_entity()
        assert isinstance(entity, dict)

    def test_to_entity_partition_key(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        entity = run_log.to_entity()
        assert entity["PartitionKey"] == "2024-01-15"

    def test_to_entity_row_key(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        entity = run_log.to_entity()
        assert entity["RowKey"] == "abc123def456"

    def test_to_entity_status_is_string(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        entity = run_log.to_entity()
        assert isinstance(entity["status"], str)
        assert entity["status"] == "success"

    def test_to_entity_status_failure(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.FAILURE,
        )
        entity = run_log.to_entity()
        assert entity["status"] == "failure"

    def test_to_entity_status_in_progress(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.IN_PROGRESS,
        )
        entity = run_log.to_entity()
        assert entity["status"] == "in_progress"

    def test_to_entity_status_partial(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.PARTIAL,
        )
        entity = run_log.to_entity()
        assert entity["status"] == "partial"

    def test_to_entity_no_message_excludes_or_none(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        entity = run_log.to_entity()
        assert entity.get("message") is None or "message" not in entity

    def test_to_entity_with_message(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.FAILURE,
            message="Connection timeout.",
        )
        entity = run_log.to_entity()
        assert entity["message"] == "Connection timeout."

    def test_to_entity_contains_run_date(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        entity = run_log.to_entity()
        assert entity["run_date"] == "2024-01-15"

    def test_to_entity_contains_run_id(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        entity = run_log.to_entity()
        assert entity["run_id"] == "abc123def456"


class TestRunLogFromEntity:
    def test_from_entity_basic(self):
        entity = {
            "PartitionKey": "2024-01-15",
            "RowKey": "abc123def456",
            "run_date": "2024-01-15",
            "run_id": "abc123def456",
            "status": "success",
        }
        run_log = RunLog.from_entity(entity)
        assert run_log.run_date == "2024-01-15"
        assert run_log.run_id == "abc123def456"
        assert run_log.status == RunStatus.SUCCESS

    def test_from_entity_with_message(self):
        entity = {
            "PartitionKey": "2024-01-15",
            "RowKey": "abc123def456",
            "run_date": "2024-01-15",
            "run_id": "abc123def456",
            "status": "failure",
            "message": "Timeout error occurred.",
        }
        run_log = RunLog.from_entity(entity)
        assert run_log.status == RunStatus.FAILURE
        assert run_log.message == "Timeout error occurred."

    def test_from_entity_without_message(self):
        entity = {
            "PartitionKey": "2024-01-15",
            "RowKey": "abc123def456",
            "run_date": "2024-01-15",
            "run_id": "abc123def456",
            "status": "success",
        }
        run_log = RunLog.from_entity(entity)
        assert run_log.message is None

    def test_from_entity_in_progress_status(self):
        entity = {
            "PartitionKey": "2024-06-30",
            "RowKey": "run20240630001",
            "run_date": "2024-06-30",
            "run_id": "run20240630001",
            "status": "in_progress",
        }
        run_log = RunLog.from_entity(entity)
        assert run_log.status == RunStatus.IN_PROGRESS

    def test_from_entity_partial_status(self):
        entity = {
            "PartitionKey": "2024-06-30",
            "RowKey": "run20240630001",
            "run_date": "2024-06-30",
            "run_id": "run20240630001",
            "status": "partial",
            "message": "2 of 4 tickers succeeded.",
        }
        run_log = RunLog.from_entity(entity)
        assert run_log.status == RunStatus.PARTIAL
        assert run_log.message == "2 of 4 tickers succeeded."


class TestRunLogRoundTrip:
    def test_round_trip_success_no_message(self):
        original = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        entity = original.to_entity()
        restored = RunLog.from_entity(entity)
        assert restored.run_date == original.run_date
        assert restored.run_id == original.run_id
        assert restored.status == original.status
        assert restored.message == original.message

    def test_round_trip_failure_with_message(self):
        original = RunLog(
            run_date="2024-03-22",
            run_id="failrun20240322",
            status=RunStatus.FAILURE,
            message="API rate limit exceeded.",
        )
        entity = original.to_entity()
        restored = RunLog.from_entity(entity)
        assert restored.run_date == original.run_date
        assert restored.run_id == original.run_id
        assert restored.status == original.status
        assert restored.message == original.message

    def test_round_trip_in_progress(self):
        original = RunLog(
            run_date="2024-07-04",
            run_id="inprogress20240704",
            status=RunStatus.IN_PROGRESS,
        )
        entity = original.to_entity()
        restored = RunLog.from_entity(entity)
        assert restored.status == RunStatus.IN_PROGRESS

    def test_round_trip_partial_with_message(self):
        original = RunLog(
            run_date="2024-11-11",
            run_id="partial20241111",
            status=RunStatus.PARTIAL,
            message="AAPL and MSFT succeeded; TSLA failed.",
        )
        entity = original.to_entity()
        restored = RunLog.from_entity(entity)
        assert restored.run_date == original.run_date
        assert restored.run_id == original.run_id
        assert restored.status == original.status
        assert restored.message == original.message

    def test_round_trip_partition_key_preserved(self):
        original = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        entity = original.to_entity()
        restored = RunLog.from_entity(entity)
        assert restored.PartitionKey == original.PartitionKey

    def test_round_trip_row_key_preserved(self):
        original = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        entity = original.to_entity()
        restored = RunLog.from_entity(entity)
        assert restored.RowKey == original.RowKey


class TestRunStatusEnum:
    def test_run_status_success_value(self):
        assert RunStatus.SUCCESS.value == "success"

    def test_run_status_failure_value(self):
        assert RunStatus.FAILURE.value == "failure"

    def test_run_status_in_progress_value(self):
        assert RunStatus.IN_PROGRESS.value == "in_progress"

    def test_run_status_partial_value(self):
        assert RunStatus.PARTIAL.value == "partial"

    def test_run_status_has_four_members(self):
        assert len(RunStatus) == 4

    def test_run_status_members(self):
        members = {s.value for s in RunStatus}
        assert members == {"success", "failure", "in_progress", "partial"}


class TestRunLogMissingRequiredFields:
    def test_missing_run_date(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_id="abc123def456",
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_date" in str(e["loc"]) for e in errors)

    def test_missing_run_id(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024-01-15",
                status=RunStatus.SUCCESS,
            )
        errors = exc_info.value.errors()
        assert any("run_id" in str(e["loc"]) for e in errors)

    def test_missing_status(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog(
                run_date="2024-01-15",
                run_id="abc123def456",
            )
        errors = exc_info.value.errors()
        assert any("status" in str(e["loc"]) for e in errors)

    def test_missing_all_required_fields(self):
        with pytest.raises(ValidationError) as exc_info:
            RunLog()
        errors = exc_info.value.errors()
        assert len(errors) >= 3


class TestRunLogEdgeCases:
    def test_run_log_message_empty_string(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
            message="",
        )
        assert run_log.message == "" or run_log.message is None

    def test_run_log_message_long_string(self):
        long_message = "Error: " + "x" * 1000
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.FAILURE,
            message=long_message,
        )
        assert run_log.message == long_message

    def test_run_log_run_id_single_char(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="a",
            status=RunStatus.SUCCESS,
        )
        assert run_log.run_id == "a"

    def test_run_log_earliest_valid_date(self):
        run_log = RunLog(
            run_date="0001-01-01",
            run_id="earlyrun",
            status=RunStatus.SUCCESS,
        )
        assert run_log.run_date == "0001-01-01"

    def test_run_log_future_date(self):
        run_log = RunLog(
            run_date="2099-12-31",
            run_id="futurerun",
            status=RunStatus.SUCCESS,
        )
        assert run_log.run_date == "2099-12-31"

    def test_to_entity_returns_new_dict_each_call(self):
        run_log = RunLog(
            run_date="2024-01-15",
            run_id="abc123def456",
            status=RunStatus.SUCCESS,
        )
        entity1 = run_log.to_entity()
        entity2 = run_log.to_entity()
        assert entity1 is not entity2
        assert entity1 == entity2