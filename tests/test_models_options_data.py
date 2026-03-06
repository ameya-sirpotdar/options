import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from backend.models.options_data import OptionsData


class TestOptionsDataCreation:
    def test_create_minimal_valid_options_data(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        assert data.ticker == "AAPL"
        assert data.timestamp == "2024-01-15T10:30:00Z"
        assert data.expiry == "2024-02-16"
        assert data.strike == 150.0
        assert data.delta == 0.45
        assert data.theta == -0.05
        assert data.iv == 0.25
        assert data.premium == 3.50

    def test_create_with_all_fields(self):
        data = OptionsData(
            ticker="SPY",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-03-15",
            strike=450.0,
            delta=0.50,
            theta=-0.10,
            iv=0.18,
            premium=5.75,
        )
        assert data.ticker == "SPY"
        assert data.strike == 450.0

    def test_partition_key_is_ticker(self):
        data = OptionsData(
            ticker="TSLA",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=200.0,
            delta=0.40,
            theta=-0.08,
            iv=0.55,
            premium=8.00,
        )
        assert data.PartitionKey == "TSLA"

    def test_row_key_is_timestamp(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        assert data.RowKey == "2024-01-15T10:30:00Z"

    def test_partition_key_syncs_with_ticker(self):
        data = OptionsData(
            ticker="MSFT",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=300.0,
            delta=0.55,
            theta=-0.06,
            iv=0.22,
            premium=4.20,
        )
        assert data.PartitionKey == data.ticker

    def test_row_key_syncs_with_timestamp(self):
        ts = "2024-01-15T10:30:00Z"
        data = OptionsData(
            ticker="AAPL",
            timestamp=ts,
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        assert data.RowKey == data.timestamp


class TestOptionsDataValidation:
    def test_ticker_cannot_be_empty(self):
        with pytest.raises(ValidationError) as exc_info:
            OptionsData(
                ticker="",
                timestamp="2024-01-15T10:30:00Z",
                expiry="2024-02-16",
                strike=150.0,
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )
        errors = exc_info.value.errors()
        assert any("ticker" in str(e) for e in errors)

    def test_ticker_cannot_contain_forward_slash(self):
        with pytest.raises(ValidationError) as exc_info:
            OptionsData(
                ticker="AA/PL",
                timestamp="2024-01-15T10:30:00Z",
                expiry="2024-02-16",
                strike=150.0,
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )
        errors = exc_info.value.errors()
        assert any("ticker" in str(e) for e in errors)

    def test_ticker_cannot_contain_backslash(self):
        with pytest.raises(ValidationError) as exc_info:
            OptionsData(
                ticker="AA\\PL",
                timestamp="2024-01-15T10:30:00Z",
                expiry="2024-02-16",
                strike=150.0,
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )
        errors = exc_info.value.errors()
        assert any("ticker" in str(e) for e in errors)

    def test_ticker_cannot_contain_hash(self):
        with pytest.raises(ValidationError) as exc_info:
            OptionsData(
                ticker="AA#PL",
                timestamp="2024-01-15T10:30:00Z",
                expiry="2024-02-16",
                strike=150.0,
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )
        errors = exc_info.value.errors()
        assert any("ticker" in str(e) for e in errors)

    def test_ticker_cannot_contain_question_mark(self):
        with pytest.raises(ValidationError) as exc_info:
            OptionsData(
                ticker="AA?PL",
                timestamp="2024-01-15T10:30:00Z",
                expiry="2024-02-16",
                strike=150.0,
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )
        errors = exc_info.value.errors()
        assert any("ticker" in str(e) for e in errors)

    def test_timestamp_cannot_be_empty(self):
        with pytest.raises(ValidationError) as exc_info:
            OptionsData(
                ticker="AAPL",
                timestamp="",
                expiry="2024-02-16",
                strike=150.0,
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )
        errors = exc_info.value.errors()
        assert any("timestamp" in str(e) for e in errors)

    def test_timestamp_cannot_contain_forward_slash(self):
        with pytest.raises(ValidationError) as exc_info:
            OptionsData(
                ticker="AAPL",
                timestamp="2024/01/15T10:30:00Z",
                expiry="2024-02-16",
                strike=150.0,
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )
        errors = exc_info.value.errors()
        assert any("timestamp" in str(e) for e in errors)

    def test_strike_must_be_positive(self):
        with pytest.raises(ValidationError) as exc_info:
            OptionsData(
                ticker="AAPL",
                timestamp="2024-01-15T10:30:00Z",
                expiry="2024-02-16",
                strike=-10.0,
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )
        errors = exc_info.value.errors()
        assert any("strike" in str(e) for e in errors)

    def test_strike_cannot_be_zero(self):
        with pytest.raises(ValidationError) as exc_info:
            OptionsData(
                ticker="AAPL",
                timestamp="2024-01-15T10:30:00Z",
                expiry="2024-02-16",
                strike=0.0,
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )
        errors = exc_info.value.errors()
        assert any("strike" in str(e) for e in errors)

    def test_delta_must_be_between_negative_one_and_one(self):
        with pytest.raises(ValidationError) as exc_info:
            OptionsData(
                ticker="AAPL",
                timestamp="2024-01-15T10:30:00Z",
                expiry="2024-02-16",
                strike=150.0,
                delta=1.5,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )
        errors = exc_info.value.errors()
        assert any("delta" in str(e) for e in errors)

    def test_delta_lower_bound(self):
        with pytest.raises(ValidationError) as exc_info:
            OptionsData(
                ticker="AAPL",
                timestamp="2024-01-15T10:30:00Z",
                expiry="2024-02-16",
                strike=150.0,
                delta=-1.5,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )
        errors = exc_info.value.errors()
        assert any("delta" in str(e) for e in errors)

    def test_delta_boundary_values_valid(self):
        data_pos = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=1.0,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        assert data_pos.delta == 1.0

        data_neg = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=-1.0,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        assert data_neg.delta == -1.0

    def test_iv_must_be_non_negative(self):
        with pytest.raises(ValidationError) as exc_info:
            OptionsData(
                ticker="AAPL",
                timestamp="2024-01-15T10:30:00Z",
                expiry="2024-02-16",
                strike=150.0,
                delta=0.45,
                theta=-0.05,
                iv=-0.10,
                premium=3.50,
            )
        errors = exc_info.value.errors()
        assert any("iv" in str(e) for e in errors)

    def test_iv_can_be_zero(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.0,
            premium=3.50,
        )
        assert data.iv == 0.0

    def test_premium_must_be_non_negative(self):
        with pytest.raises(ValidationError) as exc_info:
            OptionsData(
                ticker="AAPL",
                timestamp="2024-01-15T10:30:00Z",
                expiry="2024-02-16",
                strike=150.0,
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=-1.0,
            )
        errors = exc_info.value.errors()
        assert any("premium" in str(e) for e in errors)

    def test_premium_can_be_zero(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.25,
            premium=0.0,
        )
        assert data.premium == 0.0

    def test_missing_required_field_ticker(self):
        with pytest.raises(ValidationError):
            OptionsData(
                timestamp="2024-01-15T10:30:00Z",
                expiry="2024-02-16",
                strike=150.0,
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )

    def test_missing_required_field_strike(self):
        with pytest.raises(ValidationError):
            OptionsData(
                ticker="AAPL",
                timestamp="2024-01-15T10:30:00Z",
                expiry="2024-02-16",
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )

    def test_missing_required_field_expiry(self):
        with pytest.raises(ValidationError):
            OptionsData(
                ticker="AAPL",
                timestamp="2024-01-15T10:30:00Z",
                strike=150.0,
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )


class TestOptionsDataToEntity:
    def test_to_entity_returns_dict(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        entity = data.to_entity()
        assert isinstance(entity, dict)

    def test_to_entity_contains_partition_key(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        entity = data.to_entity()
        assert "PartitionKey" in entity
        assert entity["PartitionKey"] == "AAPL"

    def test_to_entity_contains_row_key(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        entity = data.to_entity()
        assert "RowKey" in entity
        assert entity["RowKey"] == "2024-01-15T10:30:00Z"

    def test_to_entity_contains_all_fields(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        entity = data.to_entity()
        assert "expiry" in entity
        assert "strike" in entity
        assert "delta" in entity
        assert "theta" in entity
        assert "iv" in entity
        assert "premium" in entity

    def test_to_entity_field_values(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        entity = data.to_entity()
        assert entity["expiry"] == "2024-02-16"
        assert entity["strike"] == 150.0
        assert entity["delta"] == 0.45
        assert entity["theta"] == -0.05
        assert entity["iv"] == 0.25
        assert entity["premium"] == 3.50

    def test_to_entity_does_not_contain_ticker_separately(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        entity = data.to_entity()
        assert "ticker" not in entity

    def test_to_entity_does_not_contain_timestamp_separately(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        entity = data.to_entity()
        assert "timestamp" not in entity


class TestOptionsDataFromEntity:
    def test_from_entity_creates_instance(self):
        entity = {
            "PartitionKey": "AAPL",
            "RowKey": "2024-01-15T10:30:00Z",
            "expiry": "2024-02-16",
            "strike": 150.0,
            "delta": 0.45,
            "theta": -0.05,
            "iv": 0.25,
            "premium": 3.50,
        }
        data = OptionsData.from_entity(entity)
        assert isinstance(data, OptionsData)

    def test_from_entity_sets_ticker_from_partition_key(self):
        entity = {
            "PartitionKey": "AAPL",
            "RowKey": "2024-01-15T10:30:00Z",
            "expiry": "2024-02-16",
            "strike": 150.0,
            "delta": 0.45,
            "theta": -0.05,
            "iv": 0.25,
            "premium": 3.50,
        }
        data = OptionsData.from_entity(entity)
        assert data.ticker == "AAPL"

    def test_from_entity_sets_timestamp_from_row_key(self):
        entity = {
            "PartitionKey": "AAPL",
            "RowKey": "2024-01-15T10:30:00Z",
            "expiry": "2024-02-16",
            "strike": 150.0,
            "delta": 0.45,
            "theta": -0.05,
            "iv": 0.25,
            "premium": 3.50,
        }
        data = OptionsData.from_entity(entity)
        assert data.timestamp == "2024-01-15T10:30:00Z"

    def test_from_entity_sets_all_fields(self):
        entity = {
            "PartitionKey": "AAPL",
            "RowKey": "2024-01-15T10:30:00Z",
            "expiry": "2024-02-16",
            "strike": 150.0,
            "delta": 0.45,
            "theta": -0.05,
            "iv": 0.25,
            "premium": 3.50,
        }
        data = OptionsData.from_entity(entity)
        assert data.expiry == "2024-02-16"
        assert data.strike == 150.0
        assert data.delta == 0.45
        assert data.theta == -0.05
        assert data.iv == 0.25
        assert data.premium == 3.50

    def test_from_entity_missing_partition_key_raises(self):
        entity = {
            "RowKey": "2024-01-15T10:30:00Z",
            "expiry": "2024-02-16",
            "strike": 150.0,
            "delta": 0.45,
            "theta": -0.05,
            "iv": 0.25,
            "premium": 3.50,
        }
        with pytest.raises((ValidationError, KeyError, ValueError)):
            OptionsData.from_entity(entity)

    def test_from_entity_missing_row_key_raises(self):
        entity = {
            "PartitionKey": "AAPL",
            "expiry": "2024-02-16",
            "strike": 150.0,
            "delta": 0.45,
            "theta": -0.05,
            "iv": 0.25,
            "premium": 3.50,
        }
        with pytest.raises((ValidationError, KeyError, ValueError)):
            OptionsData.from_entity(entity)


class TestOptionsDataRoundTrip:
    def test_round_trip_to_entity_and_back(self):
        original = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        entity = original.to_entity()
        restored = OptionsData.from_entity(entity)

        assert restored.ticker == original.ticker
        assert restored.timestamp == original.timestamp
        assert restored.expiry == original.expiry
        assert restored.strike == original.strike
        assert restored.delta == original.delta
        assert restored.theta == original.theta
        assert restored.iv == original.iv
        assert restored.premium == original.premium

    def test_round_trip_preserves_partition_and_row_keys(self):
        original = OptionsData(
            ticker="SPY",
            timestamp="2024-03-01T09:00:00Z",
            expiry="2024-04-19",
            strike=500.0,
            delta=0.50,
            theta=-0.12,
            iv=0.15,
            premium=6.00,
        )
        entity = original.to_entity()
        restored = OptionsData.from_entity(entity)

        assert restored.PartitionKey == original.PartitionKey
        assert restored.RowKey == original.RowKey

    def test_round_trip_with_extreme_values(self):
        original = OptionsData(
            ticker="GME",
            timestamp="2024-01-15T23:59:59Z",
            expiry="2024-01-19",
            strike=0.01,
            delta=-1.0,
            theta=-999.99,
            iv=5.0,
            premium=0.01,
        )
        entity = original.to_entity()
        restored = OptionsData.from_entity(entity)

        assert restored.strike == original.strike
        assert restored.delta == original.delta
        assert restored.theta == original.theta
        assert restored.iv == original.iv

    def test_multiple_tickers_have_different_partition_keys(self):
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]
        entities = []
        for ticker in tickers:
            data = OptionsData(
                ticker=ticker,
                timestamp="2024-01-15T10:30:00Z",
                expiry="2024-02-16",
                strike=100.0,
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )
            entities.append(data.to_entity())

        partition_keys = [e["PartitionKey"] for e in entities]
        assert len(set(partition_keys)) == len(tickers)

    def test_same_ticker_different_timestamps_have_different_row_keys(self):
        timestamps = [
            "2024-01-15T10:00:00Z",
            "2024-01-15T11:00:00Z",
            "2024-01-15T12:00:00Z",
        ]
        entities = []
        for ts in timestamps:
            data = OptionsData(
                ticker="AAPL",
                timestamp=ts,
                expiry="2024-02-16",
                strike=150.0,
                delta=0.45,
                theta=-0.05,
                iv=0.25,
                premium=3.50,
            )
            entities.append(data.to_entity())

        row_keys = [e["RowKey"] for e in entities]
        assert len(set(row_keys)) == len(timestamps)


class TestOptionsDataEdgeCases:
    def test_ticker_with_numbers_is_valid(self):
        data = OptionsData(
            ticker="BRK.B",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=350.0,
            delta=0.45,
            theta=-0.05,
            iv=0.20,
            premium=4.00,
        )
        assert data.ticker == "BRK.B"

    def test_large_strike_price(self):
        data = OptionsData(
            ticker="AMZN",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=3500.0,
            delta=0.45,
            theta=-0.05,
            iv=0.30,
            premium=50.0,
        )
        assert data.strike == 3500.0

    def test_very_small_premium(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.01,
            theta=-0.001,
            iv=0.25,
            premium=0.01,
        )
        assert data.premium == 0.01

    def test_negative_theta_is_valid(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-100.0,
            iv=0.25,
            premium=3.50,
        )
        assert data.theta == -100.0

    def test_positive_theta_is_valid(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=0.05,
            iv=0.25,
            premium=3.50,
        )
        assert data.theta == 0.05

    def test_model_is_immutable_after_creation(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        with pytest.raises(Exception):
            data.ticker = "MSFT"

    def test_to_entity_returns_new_dict_each_call(self):
        data = OptionsData(
            ticker="AAPL",
            timestamp="2024-01-15T10:30:00Z",
            expiry="2024-02-16",
            strike=150.0,
            delta=0.45,
            theta=-0.05,
            iv=0.25,
            premium=3.50,
        )
        entity1 = data.to_entity()
        entity2 = data.to_entity()
        assert entity1 is not entity2
        assert entity1 == entity2