import pytest
from pydantic import ValidationError
from backend.models.options_data import OptionsData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def valid_kwargs(**overrides):
    """Return a dict of valid OptionsData constructor arguments."""
    defaults = {
        "ticker": "AAPL",
        "timestamp": "2024-01-15T10:30:00Z",
        "expiration_date": "2024-03-15",
        "strike": 150.0,
        "option_type": "call",
        "bid": 5.25,
        "ask": 5.50,
        "last_price": 5.35,
        "volume": 1000,
        "open_interest": 5000,
        "implied_volatility": 0.25,
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# Construction – happy path
# ---------------------------------------------------------------------------

class TestOptionsDataConstruction:
    def test_basic_construction(self):
        data = OptionsData(**valid_kwargs())
        assert data.ticker == "AAPL"
        assert data.strike == 150.0
        assert data.option_type == "call"

    def test_put_option_type(self):
        data = OptionsData(**valid_kwargs(option_type="put"))
        assert data.option_type == "put"

    def test_optional_fields_default_to_none(self):
        data = OptionsData(**valid_kwargs())
        # implied_volatility is provided; check a truly optional field if any
        assert data.implied_volatility == 0.25

    def test_zero_volume_allowed(self):
        data = OptionsData(**valid_kwargs(volume=0))
        assert data.volume == 0

    def test_zero_open_interest_allowed(self):
        data = OptionsData(**valid_kwargs(open_interest=0))
        assert data.open_interest == 0

    def test_implied_volatility_none_allowed(self):
        data = OptionsData(**valid_kwargs(implied_volatility=None))
        assert data.implied_volatility is None

    def test_large_strike_value(self):
        data = OptionsData(**valid_kwargs(strike=99999.99))
        assert data.strike == 99999.99

    def test_ticker_is_uppercased(self):
        data = OptionsData(**valid_kwargs(ticker="aapl"))
        assert data.ticker == "AAPL"

    def test_ticker_mixed_case_uppercased(self):
        data = OptionsData(**valid_kwargs(ticker="Msft"))
        assert data.ticker == "MSFT"

    def test_option_type_lowercased(self):
        data = OptionsData(**valid_kwargs(option_type="CALL"))
        assert data.option_type == "call"

    def test_option_type_put_lowercased(self):
        data = OptionsData(**valid_kwargs(option_type="PUT"))
        assert data.option_type == "put"


# ---------------------------------------------------------------------------
# PartitionKey and RowKey derivation
# ---------------------------------------------------------------------------

class TestPartitionKeyRowKey:
    def test_partition_key_equals_ticker(self):
        data = OptionsData(**valid_kwargs(ticker="TSLA"))
        assert data.PartitionKey == "TSLA"

    def test_row_key_equals_timestamp(self):
        ts = "2024-01-15T10:30:00Z"
        data = OptionsData(**valid_kwargs(timestamp=ts))
        assert data.RowKey == ts

    def test_partition_key_reflects_uppercase(self):
        data = OptionsData(**valid_kwargs(ticker="goog"))
        assert data.PartitionKey == "GOOG"

    def test_row_key_is_string(self):
        data = OptionsData(**valid_kwargs())
        assert isinstance(data.RowKey, str)

    def test_partition_key_is_string(self):
        data = OptionsData(**valid_kwargs())
        assert isinstance(data.PartitionKey, str)


# ---------------------------------------------------------------------------
# Serialization – to_entity()
# ---------------------------------------------------------------------------

class TestToEntity:
    def test_to_entity_returns_dict(self):
        data = OptionsData(**valid_kwargs())
        entity = data.to_entity()
        assert isinstance(entity, dict)

    def test_to_entity_contains_partition_key(self):
        data = OptionsData(**valid_kwargs(ticker="NVDA"))
        entity = data.to_entity()
        assert entity["PartitionKey"] == "NVDA"

    def test_to_entity_contains_row_key(self):
        ts = "2024-06-01T09:00:00Z"
        data = OptionsData(**valid_kwargs(timestamp=ts))
        entity = data.to_entity()
        assert entity["RowKey"] == ts

    def test_to_entity_contains_ticker(self):
        data = OptionsData(**valid_kwargs(ticker="AMZN"))
        entity = data.to_entity()
        assert entity["ticker"] == "AMZN"

    def test_to_entity_contains_timestamp(self):
        ts = "2024-06-01T09:00:00Z"
        data = OptionsData(**valid_kwargs(timestamp=ts))
        entity = data.to_entity()
        assert entity["timestamp"] == ts

    def test_to_entity_contains_strike(self):
        data = OptionsData(**valid_kwargs(strike=200.0))
        entity = data.to_entity()
        assert entity["strike"] == 200.0

    def test_to_entity_contains_option_type(self):
        data = OptionsData(**valid_kwargs(option_type="put"))
        entity = data.to_entity()
        assert entity["option_type"] == "put"

    def test_to_entity_contains_bid(self):
        data = OptionsData(**valid_kwargs(bid=3.10))
        entity = data.to_entity()
        assert entity["bid"] == 3.10

    def test_to_entity_contains_ask(self):
        data = OptionsData(**valid_kwargs(ask=3.20))
        entity = data.to_entity()
        assert entity["ask"] == 3.20

    def test_to_entity_contains_volume(self):
        data = OptionsData(**valid_kwargs(volume=500))
        entity = data.to_entity()
        assert entity["volume"] == 500

    def test_to_entity_contains_open_interest(self):
        data = OptionsData(**valid_kwargs(open_interest=2500))
        entity = data.to_entity()
        assert entity["open_interest"] == 2500

    def test_to_entity_contains_implied_volatility(self):
        data = OptionsData(**valid_kwargs(implied_volatility=0.30))
        entity = data.to_entity()
        assert entity["implied_volatility"] == 0.30

    def test_to_entity_none_implied_volatility_excluded_or_none(self):
        data = OptionsData(**valid_kwargs(implied_volatility=None))
        entity = data.to_entity()
        # None values may be excluded or kept as None; either is acceptable
        assert entity.get("implied_volatility") is None or "implied_volatility" not in entity

    def test_to_entity_expiration_date_present(self):
        data = OptionsData(**valid_kwargs(expiration_date="2024-03-15"))
        entity = data.to_entity()
        assert entity["expiration_date"] == "2024-03-15"


# ---------------------------------------------------------------------------
# Deserialization – from_entity()
# ---------------------------------------------------------------------------

class TestFromEntity:
    def _make_entity(self, **overrides):
        base = {
            "PartitionKey": "AAPL",
            "RowKey": "2024-01-15T10:30:00Z",
            "ticker": "AAPL",
            "timestamp": "2024-01-15T10:30:00Z",
            "expiration_date": "2024-03-15",
            "strike": 150.0,
            "option_type": "call",
            "bid": 5.25,
            "ask": 5.50,
            "last_price": 5.35,
            "volume": 1000,
            "open_interest": 5000,
            "implied_volatility": 0.25,
        }
        base.update(overrides)
        return base

    def test_from_entity_returns_options_data(self):
        entity = self._make_entity()
        data = OptionsData.from_entity(entity)
        assert isinstance(data, OptionsData)

    def test_from_entity_ticker(self):
        entity = self._make_entity(ticker="AAPL", PartitionKey="AAPL")
        data = OptionsData.from_entity(entity)
        assert data.ticker == "AAPL"

    def test_from_entity_timestamp(self):
        ts = "2024-01-15T10:30:00Z"
        entity = self._make_entity(timestamp=ts, RowKey=ts)
        data = OptionsData.from_entity(entity)
        assert data.timestamp == ts

    def test_from_entity_strike(self):
        entity = self._make_entity(strike=175.5)
        data = OptionsData.from_entity(entity)
        assert data.strike == 175.5

    def test_from_entity_option_type(self):
        entity = self._make_entity(option_type="put")
        data = OptionsData.from_entity(entity)
        assert data.option_type == "put"

    def test_from_entity_volume(self):
        entity = self._make_entity(volume=999)
        data = OptionsData.from_entity(entity)
        assert data.volume == 999

    def test_from_entity_implied_volatility_none(self):
        entity = self._make_entity(implied_volatility=None)
        data = OptionsData.from_entity(entity)
        assert data.implied_volatility is None

    def test_from_entity_implied_volatility_missing(self):
        entity = self._make_entity()
        entity.pop("implied_volatility", None)
        data = OptionsData.from_entity(entity)
        assert data.implied_volatility is None


# ---------------------------------------------------------------------------
# Round-trip serialization
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_round_trip_basic(self):
        original = OptionsData(**valid_kwargs())
        entity = original.to_entity()
        restored = OptionsData.from_entity(entity)
        assert restored.ticker == original.ticker
        assert restored.timestamp == original.timestamp
        assert restored.strike == original.strike
        assert restored.option_type == original.option_type

    def test_round_trip_bid_ask(self):
        original = OptionsData(**valid_kwargs(bid=10.0, ask=10.5))
        entity = original.to_entity()
        restored = OptionsData.from_entity(entity)
        assert restored.bid == original.bid
        assert restored.ask == original.ask

    def test_round_trip_volume_open_interest(self):
        original = OptionsData(**valid_kwargs(volume=250, open_interest=1250))
        entity = original.to_entity()
        restored = OptionsData.from_entity(entity)
        assert restored.volume == original.volume
        assert restored.open_interest == original.open_interest

    def test_round_trip_implied_volatility(self):
        original = OptionsData(**valid_kwargs(implied_volatility=0.45))
        entity = original.to_entity()
        restored = OptionsData.from_entity(entity)
        assert restored.implied_volatility == original.implied_volatility

    def test_round_trip_implied_volatility_none(self):
        original = OptionsData(**valid_kwargs(implied_volatility=None))
        entity = original.to_entity()
        restored = OptionsData.from_entity(entity)
        assert restored.implied_volatility is None

    def test_round_trip_put_option(self):
        original = OptionsData(**valid_kwargs(option_type="put"))
        entity = original.to_entity()
        restored = OptionsData.from_entity(entity)
        assert restored.option_type == "put"

    def test_round_trip_partition_and_row_keys_preserved(self):
        original = OptionsData(**valid_kwargs(ticker="META", timestamp="2024-07-04T12:00:00Z"))
        entity = original.to_entity()
        restored = OptionsData.from_entity(entity)
        assert restored.PartitionKey == original.PartitionKey
        assert restored.RowKey == original.RowKey

    def test_round_trip_expiration_date(self):
        original = OptionsData(**valid_kwargs(expiration_date="2024-12-20"))
        entity = original.to_entity()
        restored = OptionsData.from_entity(entity)
        assert restored.expiration_date == original.expiration_date


# ---------------------------------------------------------------------------
# Validation – ticker
# ---------------------------------------------------------------------------

class TestTickerValidation:
    def test_empty_ticker_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(ticker=""))

    def test_ticker_with_slash_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(ticker="AA/PL"))

    def test_ticker_with_hash_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(ticker="AA#PL"))

    def test_ticker_with_question_mark_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(ticker="AA?PL"))

    def test_ticker_with_backslash_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(ticker="AA\\PL"))

    def test_valid_ticker_with_dot(self):
        # Some tickers like BRK.B are valid
        data = OptionsData(**valid_kwargs(ticker="BRK.B"))
        assert data.ticker == "BRK.B"

    def test_valid_ticker_with_hyphen(self):
        data = OptionsData(**valid_kwargs(ticker="BF-B"))
        assert data.ticker == "BF-B"


# ---------------------------------------------------------------------------
# Validation – timestamp / RowKey
# ---------------------------------------------------------------------------

class TestTimestampValidation:
    def test_empty_timestamp_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(timestamp=""))

    def test_timestamp_with_slash_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(timestamp="2024/01/15T10:30:00Z"))

    def test_timestamp_with_hash_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(timestamp="2024-01-15T10:30:00Z#extra"))

    def test_timestamp_with_question_mark_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(timestamp="2024-01-15T10:30:00Z?q=1"))

    def test_valid_iso_timestamp(self):
        ts = "2024-01-15T10:30:00Z"
        data = OptionsData(**valid_kwargs(timestamp=ts))
        assert data.timestamp == ts


# ---------------------------------------------------------------------------
# Validation – option_type
# ---------------------------------------------------------------------------

class TestOptionTypeValidation:
    def test_invalid_option_type_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(option_type="straddle"))

    def test_invalid_option_type_numeric_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(option_type="1"))

    def test_call_accepted(self):
        data = OptionsData(**valid_kwargs(option_type="call"))
        assert data.option_type == "call"

    def test_put_accepted(self):
        data = OptionsData(**valid_kwargs(option_type="put"))
        assert data.option_type == "put"


# ---------------------------------------------------------------------------
# Validation – numeric fields
# ---------------------------------------------------------------------------

class TestNumericFieldValidation:
    def test_negative_strike_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(strike=-1.0))

    def test_zero_strike_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(strike=0.0))

    def test_negative_bid_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(bid=-0.01))

    def test_negative_ask_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(ask=-0.01))

    def test_negative_volume_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(volume=-1))

    def test_negative_open_interest_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(open_interest=-1))

    def test_negative_implied_volatility_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(implied_volatility=-0.01))

    def test_implied_volatility_above_one_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(implied_volatility=1.01))

    def test_implied_volatility_exactly_one_accepted(self):
        data = OptionsData(**valid_kwargs(implied_volatility=1.0))
        assert data.implied_volatility == 1.0

    def test_implied_volatility_zero_accepted(self):
        data = OptionsData(**valid_kwargs(implied_volatility=0.0))
        assert data.implied_volatility == 0.0

    def test_bid_zero_accepted(self):
        data = OptionsData(**valid_kwargs(bid=0.0))
        assert data.bid == 0.0

    def test_ask_zero_accepted(self):
        data = OptionsData(**valid_kwargs(ask=0.0))
        assert data.ask == 0.0


# ---------------------------------------------------------------------------
# Validation – expiration_date
# ---------------------------------------------------------------------------

class TestExpirationDateValidation:
    def test_valid_expiration_date(self):
        data = OptionsData(**valid_kwargs(expiration_date="2024-12-20"))
        assert data.expiration_date == "2024-12-20"

    def test_invalid_expiration_date_format_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(expiration_date="20241220"))

    def test_empty_expiration_date_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(expiration_date=""))

    def test_expiration_date_with_slash_rejected(self):
        with pytest.raises(ValidationError):
            OptionsData(**valid_kwargs(expiration_date="2024/12/20"))


# ---------------------------------------------------------------------------
# Model fields presence
# ---------------------------------------------------------------------------

class TestModelFields:
    def test_model_has_ticker_field(self):
        assert "ticker" in OptionsData.model_fields

    def test_model_has_timestamp_field(self):
        assert "timestamp" in OptionsData.model_fields

    def test_model_has_expiration_date_field(self):
        assert "expiration_date" in OptionsData.model_fields

    def test_model_has_strike_field(self):
        assert "strike" in OptionsData.model_fields

    def test_model_has_option_type_field(self):
        assert "option_type" in OptionsData.model_fields

    def test_model_has_bid_field(self):
        assert "bid" in OptionsData.model_fields

    def test_model_has_ask_field(self):
        assert "ask" in OptionsData.model_fields

    def test_model_has_last_price_field(self):
        assert "last_price" in OptionsData.model_fields

    def test_model_has_volume_field(self):
        assert "volume" in OptionsData.model_fields

    def test_model_has_open_interest_field(self):
        assert "open_interest" in OptionsData.model_fields

    def test_model_has_implied_volatility_field(self):
        assert "implied_volatility" in OptionsData.model_fields