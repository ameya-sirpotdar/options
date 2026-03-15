from datetime import date, timedelta
import pytest
from backend.services.trades_comparison_service import (
    compute_days_to_expiration,
    compute_annualized_roi,
    enrich_put_options_with_roi,
)


# ---------------------------------------------------------------------------
# compute_days_to_expiration
# ---------------------------------------------------------------------------

class TestComputeDaysToExpiration:
    def test_future_expiration_returns_positive_days(self):
        today = date(2024, 1, 1)
        expiration = date(2024, 2, 1)
        result = compute_days_to_expiration(expiration, today=today)
        assert result == 31

    def test_same_day_expiration_returns_zero(self):
        today = date(2024, 6, 15)
        result = compute_days_to_expiration(today, today=today)
        assert result == 0

    def test_past_expiration_returns_negative_days(self):
        today = date(2024, 6, 15)
        expiration = date(2024, 6, 10)
        result = compute_days_to_expiration(expiration, today=today)
        assert result == -5

    def test_exactly_one_year_away(self):
        # Use a non-leap year span: 2023-01-01 to 2024-01-01 = 365 days
        today = date(2023, 1, 1)
        expiration = date(2024, 1, 1)
        result = compute_days_to_expiration(expiration, today=today)
        assert result == 365

    def test_leap_year_handling(self):
        today = date(2024, 2, 28)
        expiration = date(2024, 3, 1)
        result = compute_days_to_expiration(expiration, today=today)
        assert result == 2

    def test_uses_actual_today_when_not_provided(self):
        expiration = date.today() + timedelta(days=10)
        result = compute_days_to_expiration(expiration)
        assert result == 10

    def test_returns_integer(self):
        today = date(2024, 1, 1)
        expiration = date(2024, 1, 15)
        result = compute_days_to_expiration(expiration, today=today)
        assert isinstance(result, int)


# ---------------------------------------------------------------------------
# compute_annualized_roi
# ---------------------------------------------------------------------------

class TestComputeAnnualizedRoi:
    def test_standard_calculation(self):
        # premium=2.00, strike=50.00, days=30
        # roi = (2.00 / 50.00) * (365 / 30) = 0.04 * 12.1667 = 0.48667
        result = compute_annualized_roi(premium=2.00, strike=50.00, days_to_expiration=30)
        expected = (2.00 / 50.00) * (365 / 30)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_one_year_to_expiration(self):
        # premium=5, strike=100, days=365 → roi = 5/100 = 0.05
        result = compute_annualized_roi(premium=5.0, strike=100.0, days_to_expiration=365)
        assert result == pytest.approx(0.05, rel=1e-6)

    def test_zero_days_raises_value_error(self):
        with pytest.raises(ValueError, match="days_to_expiration"):
            compute_annualized_roi(premium=1.0, strike=50.0, days_to_expiration=0)

    def test_negative_days_raises_value_error(self):
        with pytest.raises(ValueError, match="days_to_expiration"):
            compute_annualized_roi(premium=1.0, strike=50.0, days_to_expiration=-5)

    def test_zero_strike_raises_value_error(self):
        with pytest.raises(ValueError, match="strike"):
            compute_annualized_roi(premium=1.0, strike=0.0, days_to_expiration=30)

    def test_negative_strike_raises_value_error(self):
        with pytest.raises(ValueError, match="strike"):
            compute_annualized_roi(premium=1.0, strike=-10.0, days_to_expiration=30)

    def test_zero_premium_returns_zero(self):
        result = compute_annualized_roi(premium=0.0, strike=50.0, days_to_expiration=30)
        assert result == pytest.approx(0.0)

    def test_negative_premium_returns_negative_roi(self):
        result = compute_annualized_roi(premium=-1.0, strike=50.0, days_to_expiration=30)
        assert result < 0

    def test_high_premium_relative_to_strike(self):
        # premium=10, strike=10, days=365 → roi = 1.0 (100%)
        result = compute_annualized_roi(premium=10.0, strike=10.0, days_to_expiration=365)
        assert result == pytest.approx(1.0, rel=1e-6)

    def test_returns_float(self):
        result = compute_annualized_roi(premium=1.0, strike=50.0, days_to_expiration=30)
        assert isinstance(result, float)

    def test_small_premium_large_strike(self):
        result = compute_annualized_roi(premium=0.05, strike=500.0, days_to_expiration=7)
        expected = (0.05 / 500.0) * (365 / 7)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_fractional_days_not_accepted_as_zero(self):
        # days=1 should work fine
        result = compute_annualized_roi(premium=1.0, strike=100.0, days_to_expiration=1)
        expected = (1.0 / 100.0) * 365
        assert result == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# enrich_put_options_with_roi
# ---------------------------------------------------------------------------

class TestEnrichPutOptionsWithRoi:
    def _make_put(self, strike, premium, expiration_date):
        return {
            "option_type": "put",
            "strike": strike,
            "premium": premium,
            "expiration_date": expiration_date,
        }

    def _make_call(self, strike, premium, expiration_date):
        return {
            "option_type": "call",
            "strike": strike,
            "premium": premium,
            "expiration_date": expiration_date,
        }

    def test_single_put_gets_enriched(self):
        today = date(2024, 1, 1)
        expiration = date(2024, 2, 1)
        options = [self._make_put(50.0, 2.0, expiration)]
        result = enrich_put_options_with_roi(options, today=today)
        assert len(result) == 1
        assert "annualized_roi" in result[0]
        assert "days_to_expiration" in result[0]

    def test_days_to_expiration_correct(self):
        today = date(2024, 1, 1)
        expiration = date(2024, 2, 1)
        options = [self._make_put(50.0, 2.0, expiration)]
        result = enrich_put_options_with_roi(options, today=today)
        assert result[0]["days_to_expiration"] == 31

    def test_annualized_roi_correct(self):
        today = date(2024, 1, 1)
        expiration = date(2024, 2, 1)
        options = [self._make_put(50.0, 2.0, expiration)]
        result = enrich_put_options_with_roi(options, today=today)
        expected = (2.0 / 50.0) * (365 / 31)
        assert result[0]["annualized_roi"] == pytest.approx(expected, rel=1e-6)

    def test_call_options_not_enriched(self):
        today = date(2024, 1, 1)
        expiration = date(2024, 2, 1)
        options = [self._make_call(50.0, 2.0, expiration)]
        result = enrich_put_options_with_roi(options, today=today)
        assert "annualized_roi" not in result[0]
        assert "days_to_expiration" not in result[0]

    def test_mixed_options_only_puts_enriched(self):
        today = date(2024, 1, 1)
        expiration = date(2024, 2, 1)
        options = [
            self._make_put(50.0, 2.0, expiration),
            self._make_call(55.0, 1.5, expiration),
            self._make_put(45.0, 1.0, expiration),
        ]
        result = enrich_put_options_with_roi(options, today=today)
        assert "annualized_roi" in result[0]
        assert "annualized_roi" not in result[1]
        assert "annualized_roi" in result[2]

    def test_empty_list_returns_empty_list(self):
        result = enrich_put_options_with_roi([], today=date(2024, 1, 1))
        assert result == []

    def test_original_fields_preserved(self):
        today = date(2024, 1, 1)
        expiration = date(2024, 2, 1)
        options = [self._make_put(50.0, 2.0, expiration)]
        result = enrich_put_options_with_roi(options, today=today)
        assert result[0]["option_type"] == "put"
        assert result[0]["strike"] == 50.0
        assert result[0]["premium"] == 2.0
        assert result[0]["expiration_date"] == expiration

    def test_does_not_mutate_original_list(self):
        today = date(2024, 1, 1)
        expiration = date(2024, 2, 1)
        original = [self._make_put(50.0, 2.0, expiration)]
        original_copy = [dict(opt) for opt in original]
        enrich_put_options_with_roi(original, today=today)
        assert original == original_copy

    def test_expired_put_gets_none_roi(self):
        today = date(2024, 6, 15)
        expiration = date(2024, 6, 10)
        options = [self._make_put(50.0, 2.0, expiration)]
        result = enrich_put_options_with_roi(options, today=today)
        assert result[0]["annualized_roi"] is None
        assert result[0]["days_to_expiration"] == -5

    def test_same_day_expiration_put_gets_none_roi(self):
        today = date(2024, 6, 15)
        expiration = date(2024, 6, 15)
        options = [self._make_put(50.0, 2.0, expiration)]
        result = enrich_put_options_with_roi(options, today=today)
        assert result[0]["annualized_roi"] is None
        assert result[0]["days_to_expiration"] == 0

    def test_multiple_puts_all_enriched(self):
        today = date(2024, 1, 1)
        options = [
            self._make_put(50.0, 2.0, date(2024, 2, 1)),
            self._make_put(100.0, 5.0, date(2024, 3, 1)),
            self._make_put(75.0, 3.0, date(2024, 4, 1)),
        ]
        result = enrich_put_options_with_roi(options, today=today)
        for opt in result:
            assert "annualized_roi" in opt
            assert "days_to_expiration" in opt
            assert opt["annualized_roi"] is not None

    def test_uses_actual_today_when_not_provided(self):
        expiration = date.today() + timedelta(days=30)
        options = [self._make_put(50.0, 2.0, expiration)]
        result = enrich_put_options_with_roi(options)
        assert result[0]["days_to_expiration"] == 30
        assert result[0]["annualized_roi"] is not None

    def test_put_with_zero_premium_returns_zero_roi(self):
        today = date(2024, 1, 1)
        expiration = date(2024, 2, 1)
        options = [self._make_put(50.0, 0.0, expiration)]
        result = enrich_put_options_with_roi(options, today=today)
        assert result[0]["annualized_roi"] == pytest.approx(0.0)

    def test_option_type_case_insensitive_put(self):
        today = date(2024, 1, 1)
        expiration = date(2024, 2, 1)
        options = [
            {
                "option_type": "PUT",
                "strike": 50.0,
                "premium": 2.0,
                "expiration_date": expiration,
            }
        ]
        result = enrich_put_options_with_roi(options, today=today)
        assert "annualized_roi" in result[0]

    def test_returns_new_list_not_same_reference(self):
        today = date(2024, 1, 1)
        expiration = date(2024, 2, 1)
        original = [self._make_put(50.0, 2.0, expiration)]
        result = enrich_put_options_with_roi(original, today=today)
        assert result is not original

    def test_roi_value_is_float_for_valid_put(self):
        today = date(2024, 1, 1)
        expiration = date(2024, 2, 1)
        options = [self._make_put(50.0, 2.0, expiration)]
        result = enrich_put_options_with_roi(options, today=today)
        assert isinstance(result[0]["annualized_roi"], float)

    def test_days_to_expiration_is_int_for_put(self):
        today = date(2024, 1, 1)
        expiration = date(2024, 2, 1)
        options = [self._make_put(50.0, 2.0, expiration)]
        result = enrich_put_options_with_roi(options, today=today)
        assert isinstance(result[0]["days_to_expiration"], int)