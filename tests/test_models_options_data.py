import pytest
from pydantic import ValidationError

from backend.models.options_data import OptionsData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make(**overrides) -> OptionsData:
    defaults = dict(
        ticker="AAPL",
        expiry="2024-02-16",
        strike=150.0,
        delta=0.45,
        theta=-0.05,
        iv=0.25,
        premium=3.50,
        timestamp="2024-01-15T10:30:00",
    )
    defaults.update(overrides)
    return OptionsData(**defaults)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestOptionsDataCreation:
    def test_create_minimal(self):
        data = OptionsData(ticker="AAPL", expiry="2024-02-16", strike=150.0,
                           delta=0.45, theta=-0.05, iv=0.25, premium=3.50)
        assert data.ticker == "AAPL"
        assert data.expiry == "2024-02-16"
        assert data.timestamp is None

    def test_create_with_timestamp(self):
        data = _make()
        assert data.timestamp == "2024-01-15T10:30:00"

    def test_ticker_with_dot_is_valid(self):
        data = _make(ticker="BRK.B")
        assert data.ticker == "BRK.B"

    def test_large_strike_price(self):
        data = _make(ticker="AMZN", strike=3500.0)
        assert data.strike == 3500.0


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestOptionsDataValidation:
    def test_ticker_cannot_be_empty(self):
        with pytest.raises(ValidationError):
            _make(ticker="")

    def test_ticker_cannot_contain_forward_slash(self):
        with pytest.raises(ValidationError):
            _make(ticker="AA/PL")

    def test_ticker_cannot_contain_backslash(self):
        with pytest.raises(ValidationError):
            _make(ticker="AA\\PL")

    def test_ticker_cannot_contain_hash(self):
        with pytest.raises(ValidationError):
            _make(ticker="AA#PL")

    def test_ticker_cannot_contain_question_mark(self):
        with pytest.raises(ValidationError):
            _make(ticker="AA?PL")

    def test_expiry_must_be_yyyy_mm_dd(self):
        with pytest.raises(ValidationError):
            _make(expiry="16-02-2024")

    def test_expiry_cannot_be_timestamp(self):
        with pytest.raises(ValidationError):
            _make(expiry="2024-02-16T00:00:00")

    def test_strike_must_be_positive(self):
        with pytest.raises(ValidationError):
            _make(strike=-10.0)

    def test_strike_cannot_be_zero(self):
        with pytest.raises(ValidationError):
            _make(strike=0.0)

    def test_delta_upper_bound(self):
        with pytest.raises(ValidationError):
            _make(delta=1.5)

    def test_delta_lower_bound(self):
        with pytest.raises(ValidationError):
            _make(delta=-1.5)

    def test_delta_boundary_values_valid(self):
        assert _make(delta=1.0).delta == 1.0
        assert _make(delta=-1.0).delta == -1.0

    def test_iv_must_be_non_negative(self):
        with pytest.raises(ValidationError):
            _make(iv=-0.10)

    def test_iv_can_be_zero(self):
        assert _make(iv=0.0).iv == 0.0

    def test_premium_must_be_non_negative(self):
        with pytest.raises(ValidationError):
            _make(premium=-1.0)

    def test_premium_can_be_zero(self):
        assert _make(premium=0.0).premium == 0.0

    def test_missing_ticker_raises(self):
        with pytest.raises(ValidationError):
            OptionsData(expiry="2024-02-16", strike=150.0, delta=0.45,
                        theta=-0.05, iv=0.25, premium=3.50)

    def test_missing_expiry_raises(self):
        with pytest.raises(ValidationError):
            OptionsData(ticker="AAPL", strike=150.0, delta=0.45,
                        theta=-0.05, iv=0.25, premium=3.50)


# ---------------------------------------------------------------------------
# to_entity() — primary write (PartitionKey=ticker, RowKey=expiry)
# ---------------------------------------------------------------------------

class TestToEntity:
    def test_returns_dict(self):
        assert isinstance(_make().to_entity(), dict)

    def test_partition_key_is_ticker(self):
        entity = _make(ticker="AAPL").to_entity()
        assert entity["PartitionKey"] == "AAPL"

    def test_row_key_is_expiry(self):
        entity = _make(expiry="2024-02-16").to_entity()
        assert entity["RowKey"] == "2024-02-16"

    def test_contains_all_numeric_fields(self):
        entity = _make().to_entity()
        for field in ("strike", "delta", "theta", "iv", "premium"):
            assert field in entity

    def test_numeric_field_values(self):
        entity = _make(strike=150.0, delta=0.45, theta=-0.05, iv=0.25, premium=3.50).to_entity()
        assert entity["strike"] == 150.0
        assert entity["delta"] == 0.45
        assert entity["theta"] == -0.05
        assert entity["iv"] == 0.25
        assert entity["premium"] == 3.50

    def test_timestamp_present_when_set(self):
        entity = _make(timestamp="2024-01-15T10:30:00").to_entity()
        assert entity["timestamp"] == "2024-01-15T10:30:00"

    def test_timestamp_absent_when_none(self):
        entity = OptionsData(ticker="AAPL", expiry="2024-02-16", strike=150.0,
                             delta=0.45, theta=-0.05, iv=0.25, premium=3.50).to_entity()
        assert "timestamp" not in entity

    def test_ticker_not_a_separate_key(self):
        entity = _make().to_entity()
        assert "ticker" not in entity

    def test_expiry_not_a_separate_key(self):
        entity = _make().to_entity()
        assert "expiry" not in entity

    def test_returns_new_dict_each_call(self):
        data = _make()
        assert data.to_entity() is not data.to_entity()
        assert data.to_entity() == data.to_entity()


# ---------------------------------------------------------------------------
# to_expiry_entity() — secondary write (PartitionKey=expiry, RowKey=ticker)
# ---------------------------------------------------------------------------

class TestToExpiryEntity:
    def test_partition_key_is_expiry(self):
        entity = _make(expiry="2024-02-16").to_expiry_entity()
        assert entity["PartitionKey"] == "2024-02-16"

    def test_row_key_is_ticker(self):
        entity = _make(ticker="AAPL").to_expiry_entity()
        assert entity["RowKey"] == "AAPL"

    def test_data_fields_identical_to_primary(self):
        data = _make()
        primary = data.to_entity()
        secondary = data.to_expiry_entity()
        for field in ("strike", "delta", "theta", "iv", "premium"):
            assert primary[field] == secondary[field]

    def test_timestamp_present_when_set(self):
        entity = _make(timestamp="2024-01-15T10:30:00").to_expiry_entity()
        assert entity["timestamp"] == "2024-01-15T10:30:00"

    def test_timestamp_absent_when_none(self):
        entity = OptionsData(ticker="AAPL", expiry="2024-02-16", strike=150.0,
                             delta=0.45, theta=-0.05, iv=0.25, premium=3.50).to_expiry_entity()
        assert "timestamp" not in entity


# ---------------------------------------------------------------------------
# both_entities()
# ---------------------------------------------------------------------------

class TestBothEntities:
    def test_returns_tuple_of_two(self):
        result = _make().both_entities()
        assert len(result) == 2

    def test_first_is_ticker_entity(self):
        primary, _ = _make(ticker="AAPL", expiry="2024-02-16").both_entities()
        assert primary["PartitionKey"] == "AAPL"
        assert primary["RowKey"] == "2024-02-16"

    def test_second_is_expiry_entity(self):
        _, secondary = _make(ticker="AAPL", expiry="2024-02-16").both_entities()
        assert secondary["PartitionKey"] == "2024-02-16"
        assert secondary["RowKey"] == "AAPL"

    def test_both_share_same_data_fields(self):
        primary, secondary = _make().both_entities()
        assert primary["strike"] == secondary["strike"]
        assert primary["delta"] == secondary["delta"]
        assert primary["premium"] == secondary["premium"]


# ---------------------------------------------------------------------------
# from_entity()
# ---------------------------------------------------------------------------

class TestFromEntity:
    def _entity(self, **overrides):
        base = {
            "PartitionKey": "AAPL",
            "RowKey": "2024-02-16",
            "strike": 150.0,
            "delta": 0.45,
            "theta": -0.05,
            "iv": 0.25,
            "premium": 3.50,
        }
        base.update(overrides)
        return base

    def test_creates_instance(self):
        assert isinstance(OptionsData.from_entity(self._entity()), OptionsData)

    def test_sets_ticker_from_partition_key(self):
        data = OptionsData.from_entity(self._entity())
        assert data.ticker == "AAPL"

    def test_sets_expiry_from_row_key(self):
        data = OptionsData.from_entity(self._entity())
        assert data.expiry == "2024-02-16"

    def test_sets_all_numeric_fields(self):
        data = OptionsData.from_entity(self._entity())
        assert data.strike == 150.0
        assert data.delta == 0.45
        assert data.theta == -0.05
        assert data.iv == 0.25
        assert data.premium == 3.50

    def test_timestamp_optional(self):
        data = OptionsData.from_entity(self._entity())
        assert data.timestamp is None

    def test_timestamp_set_when_present(self):
        data = OptionsData.from_entity(self._entity(timestamp="2024-01-15T10:30:00"))
        assert data.timestamp == "2024-01-15T10:30:00"

    def test_missing_partition_key_raises(self):
        entity = self._entity()
        del entity["PartitionKey"]
        with pytest.raises((ValidationError, KeyError, ValueError)):
            OptionsData.from_entity(entity)

    def test_missing_row_key_raises(self):
        entity = self._entity()
        del entity["RowKey"]
        with pytest.raises((ValidationError, KeyError, ValueError)):
            OptionsData.from_entity(entity)


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_to_entity_and_back(self):
        original = _make()
        restored = OptionsData.from_entity(original.to_entity())
        assert restored.ticker == original.ticker
        assert restored.expiry == original.expiry
        assert restored.strike == original.strike
        assert restored.delta == original.delta
        assert restored.theta == original.theta
        assert restored.iv == original.iv
        assert restored.premium == original.premium
        assert restored.timestamp == original.timestamp

    def test_expiry_entity_round_trip(self):
        original = _make()
        expiry_entity = original.to_expiry_entity()
        # Reconstruct by swapping keys back
        primary_entity = {**expiry_entity, "PartitionKey": expiry_entity["RowKey"], "RowKey": expiry_entity["PartitionKey"]}
        restored = OptionsData.from_entity(primary_entity)
        assert restored.ticker == original.ticker
        assert restored.expiry == original.expiry

    def test_multiple_tickers_different_partition_keys(self):
        tickers = ["AAPL", "MSFT", "GOOGL"]
        pks = [_make(ticker=t).to_entity()["PartitionKey"] for t in tickers]
        assert len(set(pks)) == 3

    def test_same_ticker_different_expiries_have_different_row_keys(self):
        expiries = ["2024-02-16", "2024-03-15", "2024-04-19"]
        rks = [_make(expiry=e).to_entity()["RowKey"] for e in expiries]
        assert len(set(rks)) == 3
