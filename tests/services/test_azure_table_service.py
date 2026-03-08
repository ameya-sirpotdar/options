from unittest.mock import MagicMock, patch, call
import pytest
from datetime import datetime, timezone

from backend.services.azure_table_service import AzureTableService, PersistenceError
from backend.models.options_data import OptionsContractRecord
from backend.models.run_log import RunLogRecord


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OGLjX+N6+LJGhjl2xoVElTkJpk2FjgtkvRQnNHVk==;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"


def _make_contract(symbol: str = "AAPL", strike: float = 150.0) -> OptionsContractRecord:
    """Return a minimal but valid OptionsContractRecord."""
    return OptionsContractRecord(
        runId="run-001",
        underlyingSymbol=symbol,
        contractType="CALL",
        strikePrice=strike,
        expirationDate="2024-12-20",
        symbol=f"{symbol}241220C{int(strike * 1000):08d}",
        description=f"{symbol} Dec 20 2024 {strike} Call",
        bid=1.50,
        ask=1.55,
        last=1.52,
        mark=1.525,
        bidSize=10,
        askSize=10,
        lastSize=5,
        highPrice=1.80,
        lowPrice=1.20,
        openPrice=1.40,
        closePrice=1.45,
        totalVolume=1000,
        tradeTimeInLong=1700000000000,
        quoteTimeInLong=1700000001000,
        netChange=0.07,
        volatility=0.25,
        delta=0.55,
        gamma=0.05,
        theta=-0.03,
        vega=0.10,
        rho=0.02,
        openInterest=5000,
        timeValue=0.50,
        theoreticalOptionValue=1.52,
        theoreticalVolatility=0.24,
        percentChange=4.8,
        markChange=0.07,
        markPercentChange=4.8,
        intrinsicValue=1.00,
        inTheMoney=True,
        mini=False,
        nonStandard=False,
        pennyPilot=True,
        settlementType="P",
        deliverableNote="",
        daysToExpiration=30,
        expirationType="R",
        lastTradingDay=1734652800000,
        multiplier=100.0,
        optionDeliverablesList=None,
    )


def _make_run_log(run_id: str = "run-001") -> RunLogRecord:
    return RunLogRecord(
        runId=run_id,
        startedAt=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        finishedAt=datetime(2024, 1, 15, 12, 0, 5, tzinfo=timezone.utc),
        status="success",
        contractsProcessed=10,
        underlyingSymbol="AAPL",
        errorMessage=None,
    )


# ---------------------------------------------------------------------------
# Construction tests
# ---------------------------------------------------------------------------


class TestAzureTableServiceConstruction:
    @patch("backend.services.azure_table_service.TableServiceClient")
    def test_creates_table_service_client_from_connection_string(self, mock_tsc_cls):
        mock_tsc = MagicMock()
        mock_tsc_cls.from_connection_string.return_value = mock_tsc

        svc = AzureTableService(connection_string=CONNECTION_STRING)

        mock_tsc_cls.from_connection_string.assert_called_once_with(CONNECTION_STRING)
        assert svc._service_client is mock_tsc

    @patch("backend.services.azure_table_service.TableServiceClient")
    def test_creates_table_clients_for_both_tables(self, mock_tsc_cls):
        mock_tsc = MagicMock()
        mock_tsc_cls.from_connection_string.return_value = mock_tsc

        AzureTableService(connection_string=CONNECTION_STRING)

        calls = [c[0][0] for c in mock_tsc.get_table_client.call_args_list]
        assert "optionsdata" in calls
        assert "runlogs" in calls

    @patch("backend.services.azure_table_service.TableServiceClient")
    def test_custom_table_names_are_respected(self, mock_tsc_cls):
        mock_tsc = MagicMock()
        mock_tsc_cls.from_connection_string.return_value = mock_tsc

        AzureTableService(
            connection_string=CONNECTION_STRING,
            options_table="myoptions",
            runlog_table="myrunlogs",
        )

        calls = [c[0][0] for c in mock_tsc.get_table_client.call_args_list]
        assert "myoptions" in calls
        assert "myrunlogs" in calls

    @patch("backend.services.azure_table_service.TableServiceClient")
    def test_raises_persistence_error_on_bad_connection_string(self, mock_tsc_cls):
        mock_tsc_cls.from_connection_string.side_effect = ValueError("bad conn str")

        with pytest.raises(PersistenceError, match="bad conn str"):
            AzureTableService(connection_string="bad")


# ---------------------------------------------------------------------------
# upsert_contracts tests
# ---------------------------------------------------------------------------


class TestUpsertContracts:
    def _build_service(self):
        with patch("backend.services.azure_table_service.TableServiceClient") as mock_tsc_cls:
            mock_tsc = MagicMock()
            mock_tsc_cls.from_connection_string.return_value = mock_tsc
            mock_options_client = MagicMock()
            mock_runlog_client = MagicMock()

            def _get_table_client(name):
                if name == "optionsdata":
                    return mock_options_client
                return mock_runlog_client

            mock_tsc.get_table_client.side_effect = _get_table_client
            svc = AzureTableService(connection_string=CONNECTION_STRING)

        return svc, mock_options_client, mock_runlog_client

    def test_empty_list_does_not_call_submit_transaction(self):
        svc, mock_options_client, _ = self._build_service()
        svc.upsert_contracts([])
        mock_options_client.submit_transaction.assert_not_called()

    def test_single_contract_submits_one_transaction(self):
        svc, mock_options_client, _ = self._build_service()
        contract = _make_contract()
        svc.upsert_contracts([contract])
        mock_options_client.submit_transaction.assert_called_once()

    def test_transaction_contains_upsert_merge_operations(self):
        svc, mock_options_client, _ = self._build_service()
        contracts = [_make_contract(strike=150.0), _make_contract(strike=155.0)]
        svc.upsert_contracts(contracts)

        submitted = mock_options_client.submit_transaction.call_args[0][0]
        operations = list(submitted)
        assert len(operations) == 2
        for op in operations:
            assert op[0] == "upsert"

    def test_entity_has_partition_key_and_row_key(self):
        svc, mock_options_client, _ = self._build_service()
        contract = _make_contract(symbol="AAPL", strike=150.0)
        svc.upsert_contracts([contract])

        submitted = mock_options_client.submit_transaction.call_args[0][0]
        _, entity = list(submitted)[0]
        assert "PartitionKey" in entity
        assert "RowKey" in entity

    def test_partition_key_is_run_id(self):
        svc, mock_options_client, _ = self._build_service()
        contract = _make_contract()
        contract.runId = "run-xyz"
        svc.upsert_contracts([contract])

        submitted = mock_options_client.submit_transaction.call_args[0][0]
        _, entity = list(submitted)[0]
        assert entity["PartitionKey"] == "run-xyz"

    def test_row_key_is_contract_symbol(self):
        svc, mock_options_client, _ = self._build_service()
        contract = _make_contract()
        svc.upsert_contracts([contract])

        submitted = mock_options_client.submit_transaction.call_args[0][0]
        _, entity = list(submitted)[0]
        assert entity["RowKey"] == contract.symbol

    def test_entity_contains_all_model_fields(self):
        svc, mock_options_client, _ = self._build_service()
        contract = _make_contract()
        svc.upsert_contracts([contract])

        submitted = mock_options_client.submit_transaction.call_args[0][0]
        _, entity = list(submitted)[0]

        for field in contract.model_fields:
            assert field in entity, f"Missing field: {field}"

    def test_batches_100_entities_per_transaction(self):
        svc, mock_options_client, _ = self._build_service()
        contracts = [_make_contract(strike=float(i)) for i in range(100)]
        svc.upsert_contracts(contracts)
        mock_options_client.submit_transaction.assert_called_once()

    def test_101_contracts_produce_two_transactions(self):
        svc, mock_options_client, _ = self._build_service()
        contracts = [_make_contract(strike=float(i)) for i in range(101)]
        svc.upsert_contracts(contracts)
        assert mock_options_client.submit_transaction.call_count == 2

    def test_200_contracts_produce_two_transactions(self):
        svc, mock_options_client, _ = self._build_service()
        contracts = [_make_contract(strike=float(i)) for i in range(200)]
        svc.upsert_contracts(contracts)
        assert mock_options_client.submit_transaction.call_count == 2

    def test_201_contracts_produce_three_transactions(self):
        svc, mock_options_client, _ = self._build_service()
        contracts = [_make_contract(strike=float(i)) for i in range(201)]
        svc.upsert_contracts(contracts)
        assert mock_options_client.submit_transaction.call_count == 3

    def test_raises_persistence_error_on_azure_exception(self):
        svc, mock_options_client, _ = self._build_service()
        mock_options_client.submit_transaction.side_effect = Exception("network error")
        contracts = [_make_contract()]

        with pytest.raises(PersistenceError, match="network error"):
            svc.upsert_contracts(contracts)

    def test_none_fields_are_excluded_from_entity(self):
        svc, mock_options_client, _ = self._build_service()
        contract = _make_contract()
        contract.optionDeliverablesList = None
        svc.upsert_contracts([contract])

        submitted = mock_options_client.submit_transaction.call_args[0][0]
        _, entity = list(submitted)[0]
        assert "optionDeliverablesList" not in entity

    def test_boolean_fields_preserved(self):
        svc, mock_options_client, _ = self._build_service()
        contract = _make_contract()
        contract.inTheMoney = True
        contract.mini = False
        svc.upsert_contracts([contract])

        submitted = mock_options_client.submit_transaction.call_args[0][0]
        _, entity = list(submitted)[0]
        assert entity["inTheMoney"] is True
        assert entity["mini"] is False


# ---------------------------------------------------------------------------
# upsert_run_log tests
# ---------------------------------------------------------------------------


class TestUpsertRunLog:
    def _build_service(self):
        with patch("backend.services.azure_table_service.TableServiceClient") as mock_tsc_cls:
            mock_tsc = MagicMock()
            mock_tsc_cls.from_connection_string.return_value = mock_tsc
            mock_options_client = MagicMock()
            mock_runlog_client = MagicMock()

            def _get_table_client(name):
                if name == "optionsdata":
                    return mock_options_client
                return mock_runlog_client

            mock_tsc.get_table_client.side_effect = _get_table_client
            svc = AzureTableService(connection_string=CONNECTION_STRING)

        return svc, mock_options_client, mock_runlog_client

    def test_calls_upsert_entity_on_runlog_client(self):
        svc, _, mock_runlog_client = self._build_service()
        run_log = _make_run_log()
        svc.upsert_run_log(run_log)
        mock_runlog_client.upsert_entity.assert_called_once()

    def test_does_not_call_options_client(self):
        svc, mock_options_client, _ = self._build_service()
        run_log = _make_run_log()
        svc.upsert_run_log(run_log)
        mock_options_client.upsert_entity.assert_not_called()

    def test_entity_partition_key_is_underlying_symbol(self):
        svc, _, mock_runlog_client = self._build_service()
        run_log = _make_run_log()
        run_log.underlyingSymbol = "TSLA"
        svc.upsert_run_log(run_log)

        entity = mock_runlog_client.upsert_entity.call_args[0][0]
        assert entity["PartitionKey"] == "TSLA"

    def test_entity_row_key_is_run_id(self):
        svc, _, mock_runlog_client = self._build_service()
        run_log = _make_run_log(run_id="run-abc")
        svc.upsert_run_log(run_log)

        entity = mock_runlog_client.upsert_entity.call_args[0][0]
        assert entity["RowKey"] == "run-abc"

    def test_entity_contains_status(self):
        svc, _, mock_runlog_client = self._build_service()
        run_log = _make_run_log()
        run_log.status = "failure"
        svc.upsert_run_log(run_log)

        entity = mock_runlog_client.upsert_entity.call_args[0][0]
        assert entity["status"] == "failure"

    def test_entity_contains_contracts_processed(self):
        svc, _, mock_runlog_client = self._build_service()
        run_log = _make_run_log()
        run_log.contractsProcessed = 42
        svc.upsert_run_log(run_log)

        entity = mock_runlog_client.upsert_entity.call_args[0][0]
        assert entity["contractsProcessed"] == 42

    def test_entity_started_at_is_iso_string(self):
        svc, _, mock_runlog_client = self._build_service()
        run_log = _make_run_log()
        svc.upsert_run_log(run_log)

        entity = mock_runlog_client.upsert_entity.call_args[0][0]
        started_at = entity["startedAt"]
        # Should be parseable as ISO datetime
        parsed = datetime.fromisoformat(started_at)
        assert parsed == run_log.startedAt

    def test_entity_finished_at_is_iso_string(self):
        svc, _, mock_runlog_client = self._build_service()
        run_log = _make_run_log()
        svc.upsert_run_log(run_log)

        entity = mock_runlog_client.upsert_entity.call_args[0][0]
        finished_at = entity["finishedAt"]
        parsed = datetime.fromisoformat(finished_at)
        assert parsed == run_log.finishedAt

    def test_none_error_message_excluded_from_entity(self):
        svc, _, mock_runlog_client = self._build_service()
        run_log = _make_run_log()
        run_log.errorMessage = None
        svc.upsert_run_log(run_log)

        entity = mock_runlog_client.upsert_entity.call_args[0][0]
        assert "errorMessage" not in entity

    def test_error_message_included_when_set(self):
        svc, _, mock_runlog_client = self._build_service()
        run_log = _make_run_log()
        run_log.errorMessage = "Something went wrong"
        svc.upsert_run_log(run_log)

        entity = mock_runlog_client.upsert_entity.call_args[0][0]
        assert entity["errorMessage"] == "Something went wrong"

    def test_raises_persistence_error_on_azure_exception(self):
        svc, _, mock_runlog_client = self._build_service()
        mock_runlog_client.upsert_entity.side_effect = Exception("timeout")
        run_log = _make_run_log()

        with pytest.raises(PersistenceError, match="timeout"):
            svc.upsert_run_log(run_log)


# ---------------------------------------------------------------------------
# ensure_tables_exist tests
# ---------------------------------------------------------------------------


class TestEnsureTablesExist:
    def _build_service(self):
        with patch("backend.services.azure_table_service.TableServiceClient") as mock_tsc_cls:
            mock_tsc = MagicMock()
            mock_tsc_cls.from_connection_string.return_value = mock_tsc
            svc = AzureTableService(connection_string=CONNECTION_STRING)

        return svc, mock_tsc

    def test_calls_create_table_if_not_exists_for_both_tables(self):
        svc, mock_tsc = self._build_service()
        svc.ensure_tables_exist()

        calls = [c[0][0] for c in mock_tsc.create_table_if_not_exists.call_args_list]
        assert "optionsdata" in calls
        assert "runlogs" in calls

    def test_does_not_raise_on_success(self):
        svc, mock_tsc = self._build_service()
        mock_tsc.create_table_if_not_exists.return_value = MagicMock()
        svc.ensure_tables_exist()  # should not raise

    def test_raises_persistence_error_on_failure(self):
        svc, mock_tsc = self._build_service()
        mock_tsc.create_table_if_not_exists.side_effect = Exception("auth error")

        with pytest.raises(PersistenceError, match="auth error"):
            svc.ensure_tables_exist()


# ---------------------------------------------------------------------------
# Batch chunking edge cases
# ---------------------------------------------------------------------------


class TestBatchChunking:
    def _build_service(self):
        with patch("backend.services.azure_table_service.TableServiceClient") as mock_tsc_cls:
            mock_tsc = MagicMock()
            mock_tsc_cls.from_connection_string.return_value = mock_tsc
            mock_options_client = MagicMock()
            mock_runlog_client = MagicMock()

            def _get_table_client(name):
                if name == "optionsdata":
                    return mock_options_client
                return mock_runlog_client

            mock_tsc.get_table_client.side_effect = _get_table_client
            svc = AzureTableService(connection_string=CONNECTION_STRING)

        return svc, mock_options_client

    def test_first_batch_has_100_entities(self):
        svc, mock_options_client = self._build_service()
        contracts = [_make_contract(strike=float(i)) for i in range(150)]
        svc.upsert_contracts(contracts)

        first_call_ops = list(mock_options_client.submit_transaction.call_args_list[0][0][0])
        assert len(first_call_ops) == 100

    def test_second_batch_has_remaining_entities(self):
        svc, mock_options_client = self._build_service()
        contracts = [_make_contract(strike=float(i)) for i in range(150)]
        svc.upsert_contracts(contracts)

        second_call_ops = list(mock_options_client.submit_transaction.call_args_list[1][0][0])
        assert len(second_call_ops) == 50

    def test_exactly_100_contracts_single_batch(self):
        svc, mock_options_client = self._build_service()
        contracts = [_make_contract(strike=float(i)) for i in range(100)]
        svc.upsert_contracts(contracts)
        assert mock_options_client.submit_transaction.call_count == 1

    def test_one_contract_single_batch(self):
        svc, mock_options_client = self._build_service()
        svc.upsert_contracts([_make_contract()])
        assert mock_options_client.submit_transaction.call_count == 1

    def test_300_contracts_three_batches_of_100(self):
        svc, mock_options_client = self._build_service()
        contracts = [_make_contract(strike=float(i)) for i in range(300)]
        svc.upsert_contracts(contracts)
        assert mock_options_client.submit_transaction.call_count == 3
        for call_args in mock_options_client.submit_transaction.call_args_list:
            ops = list(call_args[0][0])
            assert len(ops) == 100


# ---------------------------------------------------------------------------
# PersistenceError tests
# ---------------------------------------------------------------------------


class TestPersistenceError:
    def test_is_exception_subclass(self):
        assert issubclass(PersistenceError, Exception)

    def test_carries_message(self):
        err = PersistenceError("something failed")
        assert str(err) == "something failed"

    def test_can_chain_cause(self):
        cause = ValueError("root cause")
        err = PersistenceError("wrapper") 
        err.__cause__ = cause
        assert err.__cause__ is cause

    def test_can_be_raised_and_caught(self):
        with pytest.raises(PersistenceError):
            raise PersistenceError("test error")


# ---------------------------------------------------------------------------
# Integration-style: upsert_contracts + upsert_run_log together
# ---------------------------------------------------------------------------


class TestCombinedPersistence:
    def _build_service(self):
        with patch("backend.services.azure_table_service.TableServiceClient") as mock_tsc_cls:
            mock_tsc = MagicMock()
            mock_tsc_cls.from_connection_string.return_value = mock_tsc
            mock_options_client = MagicMock()
            mock_runlog_client = MagicMock()

            def _get_table_client(name):
                if name == "optionsdata":
                    return mock_options_client
                return mock_runlog_client

            mock_tsc.get_table_client.side_effect = _get_table_client
            svc = AzureTableService(connection_string=CONNECTION_STRING)

        return svc, mock_options_client, mock_runlog_client

    def test_contracts_and_run_log_use_separate_clients(self):
        svc, mock_options_client, mock_runlog_client = self._build_service()
        contracts = [_make_contract()]
        run_log = _make_run_log()

        svc.upsert_contracts(contracts)
        svc.upsert_run_log(run_log)

        mock_options_client.submit_transaction.assert_called_once()
        mock_runlog_client.upsert_entity.assert_called_once()
        mock_options_client.upsert_entity.assert_not_called()
        mock_runlog_client.submit_transaction.assert_not_called()

    def test_run_id_consistent_across_contract_and_log(self):
        svc, mock_options_client, mock_runlog_client = self._build_service()
        run_id = "run-consistent-001"
        contract = _make_contract()
        contract.runId = run_id
        run_log = _make_run_log(run_id=run_id)

        svc.upsert_contracts([contract])
        svc.upsert_run_log(run_log)

        submitted = mock_options_client.submit_transaction.call_args[0][0]
        _, entity = list(submitted)[0]
        assert entity["PartitionKey"] == run_id

        log_entity = mock_runlog_client.upsert_entity.call_args[0][0]
        assert log_entity["RowKey"] == run_id