tests/services/test_tradability_service.py
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from backend.models.tradability import TradabilityScore, TradabilityWeights
from backend.services.tradability_service import TradabilityService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def default_weights() -> TradabilityWeights:
    return TradabilityWeights(
        liquidity=0.30,
        volatility=0.25,
        momentum=0.20,
        spread=0.15,
        volume_trend=0.10,
    )


@pytest.fixture()
def service(default_weights) -> TradabilityService:
    return TradabilityService(weights=default_weights)


# ---------------------------------------------------------------------------
# Sample market-data payloads
# ---------------------------------------------------------------------------

def _make_ticker(
    symbol: str = "AAPL",
    bid: float = 149.90,
    ask: float = 150.10,
    last: float = 150.00,
    volume: float = 1_000_000,
    avg_volume: float = 900_000,
    high_52w: float = 180.00,
    low_52w: float = 120.00,
    price_change_pct: float = 1.5,
) -> dict:
    return {
        "symbol": symbol,
        "bid": bid,
        "ask": ask,
        "last": last,
        "volume": volume,
        "avg_volume": avg_volume,
        "high_52w": high_52w,
        "low_52w": low_52w,
        "price_change_pct": price_change_pct,
    }


# ===========================================================================
# TradabilityWeights model
# ===========================================================================

class TestTradabilityWeights:
    def test_default_weights_sum_to_one(self, default_weights):
        total = (
            default_weights.liquidity
            + default_weights.volatility
            + default_weights.momentum
            + default_weights.spread
            + default_weights.volume_trend
        )
        assert abs(total - 1.0) < 1e-9

    def test_custom_weights_accepted(self):
        w = TradabilityWeights(
            liquidity=0.20,
            volatility=0.20,
            momentum=0.20,
            spread=0.20,
            volume_trend=0.20,
        )
        assert w.liquidity == 0.20

    def test_negative_weight_raises(self):
        with pytest.raises(Exception):
            TradabilityWeights(
                liquidity=-0.10,
                volatility=0.30,
                momentum=0.30,
                spread=0.25,
                volume_trend=0.25,
            )

    def test_weight_exceeding_one_raises(self):
        with pytest.raises(Exception):
            TradabilityWeights(
                liquidity=1.10,
                volatility=0.10,
                momentum=0.10,
                spread=0.10,
                volume_trend=0.10,
            )


# ===========================================================================
# TradabilityScore model
# ===========================================================================

class TestTradabilityScore:
    def test_score_fields_present(self):
        score = TradabilityScore(
            symbol="AAPL",
            total_score=0.75,
            liquidity_score=0.80,
            volatility_score=0.70,
            momentum_score=0.75,
            spread_score=0.85,
            volume_trend_score=0.60,
        )
        assert score.symbol == "AAPL"
        assert score.total_score == pytest.approx(0.75)

    def test_score_out_of_range_raises(self):
        with pytest.raises(Exception):
            TradabilityScore(
                symbol="AAPL",
                total_score=1.50,  # > 1.0
                liquidity_score=0.80,
                volatility_score=0.70,
                momentum_score=0.75,
                spread_score=0.85,
                volume_trend_score=0.60,
            )

    def test_negative_score_raises(self):
        with pytest.raises(Exception):
            TradabilityScore(
                symbol="AAPL",
                total_score=-0.10,
                liquidity_score=0.80,
                volatility_score=0.70,
                momentum_score=0.75,
                spread_score=0.85,
                volume_trend_score=0.60,
            )


# ===========================================================================
# TradabilityService.extract_metrics
# ===========================================================================

class TestExtractMetrics:
    def test_returns_dict_with_required_keys(self, service):
        ticker = _make_ticker()
        metrics = service.extract_metrics(ticker)
        required_keys = {
            "liquidity",
            "volatility",
            "momentum",
            "spread",
            "volume_trend",
        }
        assert required_keys.issubset(metrics.keys())

    def test_spread_is_relative(self, service):
        ticker = _make_ticker(bid=99.0, ask=101.0, last=100.0)
        metrics = service.extract_metrics(ticker)
        # spread = (ask - bid) / last = 2 / 100 = 0.02
        assert metrics["spread"] == pytest.approx(0.02)

    def test_volume_trend_positive_when_above_average(self, service):
        ticker = _make_ticker(volume=1_200_000, avg_volume=1_000_000)
        metrics = service.extract_metrics(ticker)
        assert metrics["volume_trend"] > 0

    def test_volume_trend_negative_when_below_average(self, service):
        ticker = _make_ticker(volume=800_000, avg_volume=1_000_000)
        metrics = service.extract_metrics(ticker)
        assert metrics["volume_trend"] < 0

    def test_volatility_uses_52w_range(self, service):
        ticker = _make_ticker(high_52w=200.0, low_52w=100.0, last=150.0)
        metrics = service.extract_metrics(ticker)
        # volatility = (high - low) / last = 100 / 150
        assert metrics["volatility"] == pytest.approx(100 / 150)

    def test_momentum_reflects_price_change(self, service):
        ticker = _make_ticker(price_change_pct=5.0)
        metrics = service.extract_metrics(ticker)
        assert metrics["momentum"] == pytest.approx(5.0)

    def test_missing_avg_volume_defaults_gracefully(self, service):
        ticker = _make_ticker()
        ticker.pop("avg_volume")
        # Should not raise; volume_trend defaults to 0 or similar
        metrics = service.extract_metrics(ticker)
        assert "volume_trend" in metrics

    def test_zero_last_price_handled(self, service):
        ticker = _make_ticker(bid=0.0, ask=0.0, last=0.0)
        # Should not raise ZeroDivisionError
        metrics = service.extract_metrics(ticker)
        assert "spread" in metrics


# ===========================================================================
# TradabilityService.compute_score
# ===========================================================================

class TestComputeScore:
    def test_returns_tradability_score_instance(self, service):
        ticker = _make_ticker()
        score = service.compute_score(ticker)
        assert isinstance(score, TradabilityScore)

    def test_symbol_propagated(self, service):
        ticker = _make_ticker(symbol="TSLA")
        score = service.compute_score(ticker)
        assert score.symbol == "TSLA"

    def test_total_score_between_zero_and_one(self, service):
        ticker = _make_ticker()
        score = service.compute_score(ticker)
        assert 0.0 <= score.total_score <= 1.0

    def test_component_scores_between_zero_and_one(self, service):
        ticker = _make_ticker()
        score = service.compute_score(ticker)
        for field in (
            score.liquidity_score,
            score.volatility_score,
            score.momentum_score,
            score.spread_score,
            score.volume_trend_score,
        ):
            assert 0.0 <= field <= 1.0

    def test_total_score_is_weighted_sum(self, service, default_weights):
        ticker = _make_ticker()
        score = service.compute_score(ticker)
        expected = (
            default_weights.liquidity * score.liquidity_score
            + default_weights.volatility * score.volatility_score
            + default_weights.momentum * score.momentum_score
            + default_weights.spread * score.spread_score
            + default_weights.volume_trend * score.volume_trend_score
        )
        assert score.total_score == pytest.approx(expected, abs=1e-6)

    def test_high_volume_increases_liquidity_score(self, service):
        low_vol = _make_ticker(volume=10_000)
        high_vol = _make_ticker(volume=10_000_000)
        score_low = service.compute_score(low_vol)
        score_high = service.compute_score(high_vol)
        assert score_high.liquidity_score >= score_low.liquidity_score

    def test_tight_spread_increases_spread_score(self, service):
        wide = _make_ticker(bid=98.0, ask=102.0, last=100.0)
        tight = _make_ticker(bid=99.9, ask=100.1, last=100.0)
        score_wide = service.compute_score(wide)
        score_tight = service.compute_score(tight)
        assert score_tight.spread_score >= score_wide.spread_score

    def test_positive_momentum_increases_momentum_score(self, service):
        neg = _make_ticker(price_change_pct=-5.0)
        pos = _make_ticker(price_change_pct=5.0)
        score_neg = service.compute_score(neg)
        score_pos = service.compute_score(pos)
        assert score_pos.momentum_score >= score_neg.momentum_score

    def test_custom_weights_affect_total_score(self, default_weights):
        # Give all weight to liquidity
        heavy_liquidity = TradabilityWeights(
            liquidity=1.0,
            volatility=0.0,
            momentum=0.0,
            spread=0.0,
            volume_trend=0.0,
        )
        svc = TradabilityService(weights=heavy_liquidity)
        ticker = _make_ticker()
        score = svc.compute_score(ticker)
        assert score.total_score == pytest.approx(score.liquidity_score, abs=1e-6)


# ===========================================================================
# TradabilityService.rank_candidates
# ===========================================================================

class TestRankCandidates:
    def _make_candidates(self):
        return [
            _make_ticker(symbol="LOW", volume=50_000, price_change_pct=-2.0),
            _make_ticker(symbol="HIGH", volume=5_000_000, price_change_pct=4.0),
            _make_ticker(symbol="MID", volume=500_000, price_change_pct=1.0),
        ]

    def test_returns_list_of_tradability_scores(self, service):
        candidates = self._make_candidates()
        ranked = service.rank_candidates(candidates)
        assert isinstance(ranked, list)
        assert all(isinstance(s, TradabilityScore) for s in ranked)

    def test_ranked_in_descending_order(self, service):
        candidates = self._make_candidates()
        ranked = service.rank_candidates(candidates)
        scores = [s.total_score for s in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_length_matches_input(self, service):
        candidates = self._make_candidates()
        ranked = service.rank_candidates(candidates)
        assert len(ranked) == len(candidates)

    def test_empty_list_returns_empty(self, service):
        assert service.rank_candidates([]) == []

    def test_single_candidate_returned(self, service):
        ranked = service.rank_candidates([_make_ticker()])
        assert len(ranked) == 1

    def test_best_candidate_is_first(self, service):
        candidates = self._make_candidates()
        ranked = service.rank_candidates(candidates)
        assert ranked[0].symbol == "HIGH"

    def test_worst_candidate_is_last(self, service):
        candidates = self._make_candidates()
        ranked = service.rank_candidates(candidates)
        assert ranked[-1].symbol == "LOW"

    def test_duplicate_symbols_handled(self, service):
        candidates = [_make_ticker(symbol="AAPL"), _make_ticker(symbol="AAPL")]
        ranked = service.rank_candidates(candidates)
        assert len(ranked) == 2


# ===========================================================================
# TradabilityService.get_best_trade
# ===========================================================================

class TestGetBestTrade:
    def _make_candidates(self):
        return [
            _make_ticker(symbol="LOW", volume=50_000, price_change_pct=-2.0),
            _make_ticker(symbol="HIGH", volume=5_000_000, price_change_pct=4.0),
            _make_ticker(symbol="MID", volume=500_000, price_change_pct=1.0),
        ]

    def test_returns_single_tradability_score(self, service):
        result = service.get_best_trade(self._make_candidates())
        assert isinstance(result, TradabilityScore)

    def test_returns_highest_scoring_candidate(self, service):
        result = service.get_best_trade(self._make_candidates())
        assert result.symbol == "HIGH"

    def test_raises_on_empty_candidates(self, service):
        with pytest.raises((ValueError, IndexError)):
            service.get_best_trade([])

    def test_single_candidate_is_best(self, service):
        ticker = _make_ticker(symbol="ONLY")
        result = service.get_best_trade([ticker])
        assert result.symbol == "ONLY"

    def test_best_trade_score_equals_top_ranked(self, service):
        candidates = self._make_candidates()
        best = service.get_best_trade(candidates)
        ranked = service.rank_candidates(candidates)
        assert best.total_score == pytest.approx(ranked[0].total_score)

    def test_best_trade_symbol_equals_top_ranked(self, service):
        candidates = self._make_candidates()
        best = service.get_best_trade(candidates)
        ranked = service.rank_candidates(candidates)
        assert best.symbol == ranked[0].symbol


# ===========================================================================
# Weight configuration integration
# ===========================================================================

class TestWeightConfiguration:
    def test_service_accepts_weights_from_settings(self):
        mock_settings = MagicMock()
        mock_settings.tradability_weights = {
            "liquidity": 0.25,
            "volatility": 0.25,
            "momentum": 0.20,
            "spread": 0.15,
            "volume_trend": 0.15,
        }
        weights = TradabilityWeights(**mock_settings.tradability_weights)
        svc = TradabilityService(weights=weights)
        assert svc.weights.liquidity == 0.25

    def test_different_weight_configs_produce_different_rankings(self):
        momentum_heavy = TradabilityWeights(
            liquidity=0.10,
            volatility=0.10,
            momentum=0.60,
            spread=0.10,
            volume_trend=0.10,
        )
        liquidity_heavy = TradabilityWeights(
            liquidity=0.60,
            volatility=0.10,
            momentum=0.10,
            spread=0.10,
            volume_trend=0.10,
        )
        svc_momentum = TradabilityService(weights=momentum_heavy)
        svc_liquidity = TradabilityService(weights=liquidity_heavy)

        # High momentum, low volume vs low momentum, high volume
        high_momentum = _make_ticker(symbol="MOMO", volume=100_000, price_change_pct=10.0)
        high_liquidity = _make_ticker(symbol="LIQD", volume=10_000_000, price_change_pct=0.1)

        best_momentum = svc_momentum.get_best_trade([high_momentum, high_liquidity])
        best_liquidity = svc_liquidity.get_best_trade([high_momentum, high_liquidity])

        assert best_momentum.symbol == "MOMO"
        assert best_liquidity.symbol == "LIQD"


# ===========================================================================
# Edge cases and robustness
# ===========================================================================

class TestEdgeCases:
    def test_all_identical_tickers_same_score(self, service):
        tickers = [_make_ticker(symbol=f"SYM{i}") for i in range(5)]
        ranked = service.rank_candidates(tickers)
        scores = [s.total_score for s in ranked]
        assert len(set(round(s, 8) for s in scores)) == 1

    def test_extreme_high_volume_clamped_to_one(self, service):
        ticker = _make_ticker(volume=999_999_999_999)
        score = service.compute_score(ticker)
        assert score.liquidity_score <= 1.0

    def test_extreme_low_volume_clamped_to_zero(self, service):
        ticker = _make_ticker(volume=1)
        score = service.compute_score(ticker)
        assert score.liquidity_score >= 0.0

    def test_extreme_positive_momentum_clamped(self, service):
        ticker = _make_ticker(price_change_pct=10_000.0)
        score = service.compute_score(ticker)
        assert score.momentum_score <= 1.0

    def test_extreme_negative_momentum_clamped(self, service):
        ticker = _make_ticker(price_change_pct=-10_000.0)
        score = service.compute_score(ticker)
        assert score.momentum_score >= 0.0

    def test_zero_volume_handled(self, service):
        ticker = _make_ticker(volume=0, avg_volume=0)
        score = service.compute_score(ticker)
        assert 0.0 <= score.total_score <= 1.0

    def test_equal_bid_ask_zero_spread(self, service):
        ticker = _make_ticker(bid=100.0, ask=100.0, last=100.0)
        metrics = service.extract_metrics(ticker)
        assert metrics["spread"] == pytest.approx(0.0)

    def test_large_number_of_candidates_performance(self, service):
        import time
        candidates = [_make_ticker(symbol=f"SYM{i}") for i in range(1000)]
        start = time.time()
        ranked = service.rank_candidates(candidates)
        elapsed = time.time() - start
        assert len(ranked) == 1000
        assert elapsed < 5.0  # Should complete well within 5 seconds

    def test_non_string_symbol_coerced(self, service):
        ticker = _make_ticker()
        ticker["symbol"] = 12345
        # Should either coerce to string or raise a clear error
        try:
            score = service.compute_score(ticker)
            assert isinstance(score.symbol, str)
        except (TypeError, ValueError):
            pass  # Acceptable to raise

    def test_missing_symbol_raises(self, service):
        ticker = _make_ticker()
        ticker.pop("symbol")
        with pytest.raises((KeyError, ValueError, TypeError)):
            service.compute_score(ticker)