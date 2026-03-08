from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from backend.models.options_data import OptionsContractRecord


def _base_payload(**overrides) -> dict:
    """Return a minimal valid payload for OptionsContractRecord."""
    base = {
        "runId": "run-001",
        "symbol": "AAPL",
        "underlyingPrice": 175.50,
        "contractType": "CALL",
        "strikePrice": 180.00,
        "expirationDate": "2024-12-20",
        "daysToExpiration": 30,
        "bid": 2.10,
        "ask": 2.20,
        "last": 2.15,
        "mark": 2.15,
        "bidSize": 10,
        "askSize": 15,
        "lastSize": 5,
        "highPrice": 2.50,
        "lowPrice": 1.90,
        "openPrice": 2.00,
        "closePrice": 2.05,
        "totalVolume": 1500,
        "tradeTimeInLong": 1700000000000,
        "quoteTimeInLong": 1700000001000,
        "netChange": 0.10,
        "volatility": 0.25,
        "delta": 0.45,
        "gamma": 0.03,
        "theta": -0.05,
        "vega": 0.10,
        "rho": 0.02,
        "openInterest": 5000,
        "timeValue": 1.50,
        "theoreticalOptionValue": 2.15,
        "theoreticalVolatility": 0.26,
        "strikePrice2": None,
        "expirationDateISO": "2024-12-20T00:00:00Z",
        "percentChange": 4.88,
        "markChange": 0.10,
        "markPercentChange": 4.88,
        "intrinsicValue": 0.65,
        "inTheMoney": False,
        "mini": False,
        "nonStandard": False,
        "optionDeliverablesList": None,
        "settlementType": "PM",
        "deliverableNote": "",
        "isIndexOption": False,
        "description": "AAPL Dec 20 2024 180 Call",
        "exchangeName": "OPR",
        "multiplier": 100.0,
    }
    base.update(overrides)
    return base


class TestOptionsContractRecordCreation:
    def test_create_with_all_required_fields(self):
        payload = _base_payload()
        record = OptionsContractRecord(**payload)
        assert record.symbol == "AAPL"
        assert record.runId == "run-001"
        assert record.contractType == "CALL"

    def test_create_put_contract(self):
        payload = _base_payload(contractType="PUT", strikePrice=170.00)
        record = OptionsContractRecord(**payload)
        assert record.contractType == "PUT"
        assert record.strikePrice == 170.00

    def test_partition_key_equals_symbol(self):
        payload = _base_payload(symbol="MSFT")
        record = OptionsContractRecord(**payload)
        assert record.PartitionKey == "MSFT"

    def test_row_key_format(self):
        payload = _base_payload(
            runId="run-42",
            symbol="AAPL",
            contractType="CALL",
            strikePrice=180.00,
            expirationDate="2024-12-20",
        )
        record = OptionsContractRecord(**payload)
        assert record.RowKey == "run-42_CALL_180.0_2024-12-20"

    def test_row_key_put_contract(self):
        payload = _base_payload(
            runId="run-10",
            symbol="TSLA",
            contractType="PUT",
            strikePrice=250.00,
            expirationDate="2025-01-17",
        )
        record = OptionsContractRecord(**payload)
        assert record.RowKey == "run-10_PUT_250.0_2025-01-17"

    def test_timestamp_auto_generated(self):
        payload = _base_payload()
        record = OptionsContractRecord(**payload)
        assert isinstance(record.timestamp, datetime)

    def test_timestamp_is_utc(self):
        payload = _base_payload()
        record = OptionsContractRecord(**payload)
        assert record.timestamp.tzinfo is not None

    def test_explicit_timestamp_preserved(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        payload = _base_payload(timestamp=ts)
        record = OptionsContractRecord(**payload)
        assert record.timestamp == ts


class TestOptionsContractRecordFieldTypes:
    def test_underlying_price_float(self):
        record = OptionsContractRecord(**_base_payload(underlyingPrice=175.50))
        assert isinstance(record.underlyingPrice, float)
        assert record.underlyingPrice == 175.50

    def test_strike_price_float(self):
        record = OptionsContractRecord(**_base_payload(strikePrice=180.00))
        assert isinstance(record.strikePrice, float)

    def test_bid_ask_last_float(self):
        record = OptionsContractRecord(**_base_payload(bid=2.10, ask=2.20, last=2.15))
        assert isinstance(record.bid, float)
        assert isinstance(record.ask, float)
        assert isinstance(record.last, float)

    def test_greeks_are_floats(self):
        record = OptionsContractRecord(**_base_payload())
        assert isinstance(record.delta, float)
        assert isinstance(record.gamma, float)
        assert isinstance(record.theta, float)
        assert isinstance(record.vega, float)
        assert isinstance(record.rho, float)

    def test_volume_and_open_interest_int(self):
        record = OptionsContractRecord(**_base_payload(totalVolume=1500, openInterest=5000))
        assert isinstance(record.totalVolume, int)
        assert isinstance(record.openInterest, int)

    def test_boolean_fields(self):
        record = OptionsContractRecord(**_base_payload(inTheMoney=True, mini=False, nonStandard=False))
        assert record.inTheMoney is True
        assert record.mini is False
        assert record.nonStandard is False

    def test_days_to_expiration_int(self):
        record = OptionsContractRecord(**_base_payload(daysToExpiration=45))
        assert isinstance(record.daysToExpiration, int)
        assert record.daysToExpiration == 45

    def test_multiplier_float(self):
        record = OptionsContractRecord(**_base_payload(multiplier=100.0))
        assert isinstance(record.multiplier, float)
        assert record.multiplier == 100.0


class TestOptionsContractRecordNullableFields:
    def test_strike_price2_none(self):
        record = OptionsContractRecord(**_base_payload(strikePrice2=None))
        assert record.strikePrice2 is None

    def test_strike_price2_with_value(self):
        record = OptionsContractRecord(**_base_payload(strikePrice2=185.00))
        assert record.strikePrice2 == 185.00

    def test_option_deliverables_list_none(self):
        record = OptionsContractRecord(**_base_payload(optionDeliverablesList=None))
        assert record.optionDeliverablesList is None

    def test_option_deliverables_list_with_value(self):
        deliverables = [{"symbol": "AAPL", "assetType": "EQUITY"}]
        record = OptionsContractRecord(**_base_payload(optionDeliverablesList=deliverables))
        assert record.optionDeliverablesList == deliverables

    def test_is_index_option_none(self):
        record = OptionsContractRecord(**_base_payload(isIndexOption=None))
        assert record.isIndexOption is None

    def test_deliverable_note_empty_string(self):
        record = OptionsContractRecord(**_base_payload(deliverableNote=""))
        assert record.deliverableNote == ""

    def test_deliverable_note_with_value(self):
        record = OptionsContractRecord(**_base_payload(deliverableNote="100 shares AAPL"))
        assert record.deliverableNote == "100 shares AAPL"


class TestOptionsContractRecordValidation:
    def test_missing_run_id_raises(self):
        payload = _base_payload()
        del payload["runId"]
        with pytest.raises(ValidationError) as exc_info:
            OptionsContractRecord(**payload)
        assert "runId" in str(exc_info.value)

    def test_missing_symbol_raises(self):
        payload = _base_payload()
        del payload["symbol"]
        with pytest.raises(ValidationError) as exc_info:
            OptionsContractRecord(**payload)
        assert "symbol" in str(exc_info.value)

    def test_missing_contract_type_raises(self):
        payload = _base_payload()
        del payload["contractType"]
        with pytest.raises(ValidationError) as exc_info:
            OptionsContractRecord(**payload)
        assert "contractType" in str(exc_info.value)

    def test_missing_strike_price_raises(self):
        payload = _base_payload()
        del payload["strikePrice"]
        with pytest.raises(ValidationError) as exc_info:
            OptionsContractRecord(**payload)
        assert "strikePrice" in str(exc_info.value)

    def test_missing_expiration_date_raises(self):
        payload = _base_payload()
        del payload["expirationDate"]
        with pytest.raises(ValidationError) as exc_info:
            OptionsContractRecord(**payload)
        assert "expirationDate" in str(exc_info.value)

    def test_invalid_underlying_price_type_raises(self):
        with pytest.raises(ValidationError):
            OptionsContractRecord(**_base_payload(underlyingPrice="not-a-number"))

    def test_invalid_delta_type_raises(self):
        with pytest.raises(ValidationError):
            OptionsContractRecord(**_base_payload(delta="bad"))

    def test_invalid_total_volume_type_raises(self):
        with pytest.raises(ValidationError):
            OptionsContractRecord(**_base_payload(totalVolume="lots"))

    def test_invalid_boolean_field_raises(self):
        with pytest.raises(ValidationError):
            OptionsContractRecord(**_base_payload(inTheMoney="yes-it-is"))


class TestOptionsContractRecordSerialization:
    def test_model_dump_contains_partition_key(self):
        record = OptionsContractRecord(**_base_payload())
        data = record.model_dump()
        assert "PartitionKey" in data
        assert data["PartitionKey"] == "AAPL"

    def test_model_dump_contains_row_key(self):
        record = OptionsContractRecord(**_base_payload())
        data = record.model_dump()
        assert "RowKey" in data

    def test_model_dump_contains_timestamp(self):
        record = OptionsContractRecord(**_base_payload())
        data = record.model_dump()
        assert "timestamp" in data

    def test_model_dump_all_fields_present(self):
        record = OptionsContractRecord(**_base_payload())
        data = record.model_dump()
        expected_fields = [
            "runId", "symbol", "underlyingPrice", "contractType",
            "strikePrice", "expirationDate", "daysToExpiration",
            "bid", "ask", "last", "mark", "delta", "gamma", "theta",
            "vega", "rho", "openInterest", "totalVolume", "volatility",
            "inTheMoney", "PartitionKey", "RowKey", "timestamp",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_model_dump_round_trip(self):
        payload = _base_payload()
        record = OptionsContractRecord(**payload)
        data = record.model_dump()
        record2 = OptionsContractRecord(**data)
        assert record2.symbol == record.symbol
        assert record2.runId == record.runId
        assert record2.RowKey == record.RowKey

    def test_model_json_serializable(self):
        import json
        record = OptionsContractRecord(**_base_payload())
        json_str = record.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["symbol"] == "AAPL"
        assert parsed["PartitionKey"] == "AAPL"


class TestOptionsContractRecordEdgeCases:
    def test_zero_bid_ask(self):
        record = OptionsContractRecord(**_base_payload(bid=0.0, ask=0.0, last=0.0))
        assert record.bid == 0.0
        assert record.ask == 0.0

    def test_negative_theta(self):
        record = OptionsContractRecord(**_base_payload(theta=-0.15))
        assert record.theta == -0.15

    def test_negative_net_change(self):
        record = OptionsContractRecord(**_base_payload(netChange=-0.50))
        assert record.netChange == -0.50

    def test_large_open_interest(self):
        record = OptionsContractRecord(**_base_payload(openInterest=999999))
        assert record.openInterest == 999999

    def test_zero_days_to_expiration(self):
        record = OptionsContractRecord(**_base_payload(daysToExpiration=0))
        assert record.daysToExpiration == 0

    def test_deep_in_the_money_call(self):
        record = OptionsContractRecord(**_base_payload(
            delta=0.99,
            inTheMoney=True,
            intrinsicValue=50.00,
            timeValue=0.01,
        ))
        assert record.delta == 0.99
        assert record.inTheMoney is True

    def test_symbol_case_preserved(self):
        record = OptionsContractRecord(**_base_payload(symbol="aapl"))
        assert record.symbol == "aapl"
        assert record.PartitionKey == "aapl"

    def test_run_id_used_in_row_key(self):
        record = OptionsContractRecord(**_base_payload(runId="unique-run-xyz"))
        assert record.RowKey.startswith("unique-run-xyz_")

    def test_different_expiration_dates_different_row_keys(self):
        record1 = OptionsContractRecord(**_base_payload(expirationDate="2024-12-20"))
        record2 = OptionsContractRecord(**_base_payload(expirationDate="2025-01-17"))
        assert record1.RowKey != record2.RowKey

    def test_different_strikes_different_row_keys(self):
        record1 = OptionsContractRecord(**_base_payload(strikePrice=180.00))
        record2 = OptionsContractRecord(**_base_payload(strikePrice=185.00))
        assert record1.RowKey != record2.RowKey

    def test_call_and_put_same_strike_different_row_keys(self):
        record1 = OptionsContractRecord(**_base_payload(contractType="CALL", strikePrice=180.00))
        record2 = OptionsContractRecord(**_base_payload(contractType="PUT", strikePrice=180.00))
        assert record1.RowKey != record2.RowKey

    def test_integer_strike_price_in_row_key(self):
        record = OptionsContractRecord(**_base_payload(strikePrice=200.0))
        assert "200.0" in record.RowKey

    def test_float_strike_price_in_row_key(self):
        record = OptionsContractRecord(**_base_payload(strikePrice=197.50))
        assert "197.5" in record.RowKey