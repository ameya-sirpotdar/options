import pytest
from unittest.mock import MagicMock, patch
from backend.models.tradability import TradabilityWeights, TradabilityScore
from backend.services.tradability_service import TradabilityService


@pytest.fixture
def default_weights():
    return TradabilityWeights(
        liquidity=0.3,
        volatility=0.25,
        momentum=0.2,
        spread=0.15,
        volume_consistency=0.1,
    )


@pytest.fixture
def service(default_weights):
    return TradabilityService(weights=default_weights)


@pytest.fixture
def sample_candidate():
    return {
        "symbol": "AAPL",
        "avg_volume": 80_000_000,
        "price": 175.0,
        "bid": 174.95,
        "ask": 175.05,
        "daily_returns": [0.01, -0.005, 0.02, 0.015, -0.01, 0.008, 0.012],
        "volume_history": [80_000_000, 82_000_000, 79_000_000, 81_000_000, 80_500_000],
    }


@pytest.fixture
def low_quality_candidate():
    return {
        "symbol": "LOWQ",
        "avg_volume": 5_000,
        "price": 1.0,
        "bid": 0.90,
        "ask": 1.10,
        "daily_returns": [0.15, -0.20, 0.30, -0.25, 0.18, -0.22, 0.28],
        "volume_history": [5_000, 100, 50_000, 200, 8_000],
    }


@pytest.fixture
def multiple_candidates():
    return [
        {
            "symbol": "AAPL",
            "avg_volume": 80_000_000,
            "price": 175.0,
            "bid": 174.95,
            "ask": 175.05,
            "daily_returns": [0.01, -0.005, 0.02, 0.015, -0.01],
            "volume_history": [80_000_000, 82_000_000, 79_000_000, 81_000_000, 80_500_000],
        },
        {
            "symbol": "MSFT",
            "avg_volume": 30_000_000,
            "price": 380.0,
            "bid": 379.90,
            "ask": 380.10,
            "daily_returns": [0.008, -0.003, 0.012, 0.009, -0.006],
            "volume_history": [30_000_000, 31_000_000, 29_500_000, 30_500_000, 30_200_000],
        },
        {
            "symbol": "TSLA",
            "avg_volume": 20_000_000,
            "price": 250.0,
            "bid": 249.80,
            "ask": 250.20,
            "daily_returns": [0.03, -0.025, 0.04, -0.035, 0.028],
            "volume_history": [20_000_000, 25_000_000, 15_000_000, 22_000_000, 18_000_000],
        },
        {
            "symbol": "LOWQ",
            "avg_volume": 5_000,
            "price": 1.0,
            "bid": 0.90,
            "ask": 1.10,
            "daily_returns": [0.15, -0.20, 0.30, -0.25, 0.18],
            "volume_history": [5_000, 100, 50_000, 200, 8_000],
        },
    ]


class TestTradabilityWeightsModel:
    def test_default_weights_sum_to_one(self):
        weights = TradabilityWeights()
        total = (
            weights.liquidity
            + weights.volatility
            + weights.momentum
            + weights.spread
            + weights.volume_consistency
        )
        assert abs(total - 1.0) < 1e-9

    def test_custom_weights_accepted(self):
        weights = TradabilityWeights(
            liquidity=0.4,
            volatility=0.2,
            momentum=0.2,
            spread=0.1,
            volume_consistency=0.1,
        )
        assert weights.liquidity == 0.4

    def test_weights_must_be_non_negative(self):
        with pytest.raises(Exception):
            TradabilityWeights(liquidity=-0.1, volatility=0.4, momentum=0.3, spread=0.2, volume_consistency=0.2)

    def test_weights_must_not_exceed_one(self):
        with pytest.raises(Exception):
            TradabilityWeights(liquidity=1.5, volatility=0.0, momentum=0.0, spread=0.0, volume_consistency=0.0)

    def test_individual_weight_fields_exist(self):
        weights = TradabilityWeights()
        assert hasattr(weights, "liquidity")
        assert hasattr(weights, "volatility")
        assert hasattr(weights, "momentum")
        assert hasattr(weights, "spread")
        assert hasattr(weights, "volume_consistency")


class TestTradabilityScoreModel:
    def test_score_model_fields(self):
        score = TradabilityScore(
            symbol="AAPL",
            total_score=0.85,
            liquidity_score=0.9,
            volatility_score=0.8,
            momentum_score=0.75,
            spread_score=0.95,
            volume_consistency_score=0.88,
        )
        assert score.symbol == "AAPL"
        assert score.total_score == 0.85

    def test_score_total_between_zero_and_one(self):
        with pytest.raises(Exception):
            TradabilityScore(
                symbol="BAD",
                total_score=1.5,
                liquidity_score=0.9,
                volatility_score=0.8,
                momentum_score=0.75,
                spread_score=0.95,
                volume_consistency_score=0.88,
            )

    def test_score_total_not_negative(self):
        with pytest.raises(Exception):
            TradabilityScore(
                symbol="BAD",
                total_score=-0.1,
                liquidity_score=0.9,
                volatility_score=0.8,
                momentum_score=0.75,
                spread_score=0.95,
                volume_consistency_score=0.88,
            )

    def test_component_scores_between_zero_and_one(self):
        with pytest.raises(Exception):
            TradabilityScore(
                symbol="BAD",
                total_score=0.5,
                liquidity_score=1.2,
                volatility_score=0.8,
                momentum_score=0.75,
                spread_score=0.95,
                volume_consistency_score=0.88,
            )

    def test_score_model_serialization(self):
        score = TradabilityScore(
            symbol="AAPL",
            total_score=0.85,
            liquidity_score=0.9,
            volatility_score=0.8,
            momentum_score=0.75,
            spread_score=0.95,
            volume_consistency_score=0.88,
        )
        data = score.model_dump()
        assert "symbol" in data
        assert "total_score" in data
        assert "liquidity_score" in data
        assert "volatility_score" in data
        assert "momentum_score" in data
        assert "spread_score" in data
        assert "volume_consistency_score" in data


class TestExtractMetrics:
    def test_extract_metrics_returns_dict(self, service, sample_candidate):
        metrics = service.extract_metrics(sample_candidate)
        assert isinstance(metrics, dict)

    def test_extract_metrics_contains_required_keys(self, service, sample_candidate):
        metrics = service.extract_metrics(sample_candidate)
        assert "liquidity" in metrics
        assert "volatility" in metrics
        assert "momentum" in metrics
        assert "spread" in metrics
        assert "volume_consistency" in metrics

    def test_extract_metrics_liquidity_from_volume(self, service, sample_candidate):
        metrics = service.extract_metrics(sample_candidate)
        assert metrics["liquidity"] > 0

    def test_extract_metrics_spread_calculation(self, service, sample_candidate):
        metrics = service.extract_metrics(sample_candidate)
        expected_spread = (sample_candidate["ask"] - sample_candidate["bid"]) / sample_candidate["price"]
        assert metrics["spread"] == pytest.approx(expected_spread, rel=1e-5)

    def test_extract_metrics_volatility_from_returns(self, service, sample_candidate):
        metrics = service.extract_metrics(sample_candidate)
        assert metrics["volatility"] >= 0

    def test_extract_metrics_momentum_from_returns(self, service, sample_candidate):
        metrics = service.extract_metrics(sample_candidate)
        assert isinstance(metrics["momentum"], float)

    def test_extract_metrics_volume_consistency(self, service, sample_candidate):
        metrics = service.extract_metrics(sample_candidate)
        assert metrics["volume_consistency"] >= 0

    def test_extract_metrics_missing_bid_ask_raises(self, service):
        bad_candidate = {
            "symbol": "BAD",
            "avg_volume": 1_000_000,
            "price": 100.0,
            "daily_returns": [0.01, -0.01],
            "volume_history": [1_000_000, 1_000_000],
        }
        with pytest.raises((KeyError, ValueError)):
            service.extract_metrics(bad_candidate)

    def test_extract_metrics_zero_price_raises(self, service):
        bad_candidate = {
            "symbol": "BAD",
            "avg_volume": 1_000_000,
            "price": 0.0,
            "bid": 0.0,
            "ask": 0.0,
            "daily_returns": [0.01, -0.01],
            "volume_history": [1_000_000, 1_000_000],
        }
        with pytest.raises((ZeroDivisionError, ValueError)):
            service.extract_metrics(bad_candidate)

    def test_extract_metrics_empty_returns_list(self, service):
        candidate = {
            "symbol": "EMPTY",
            "avg_volume": 1_000_000,
            "price": 100.0,
            "bid": 99.95,
            "ask": 100.05,
            "daily_returns": [],
            "volume_history": [1_000_000],
        }
        with pytest.raises((ValueError, ZeroDivisionError, Exception)):
            service.extract_metrics(candidate)


class TestComputeScore:
    def test_compute_score_returns_tradability_score(self, service, sample_candidate):
        score = service.compute_score(sample_candidate)
        assert isinstance(score, TradabilityScore)

    def test_compute_score_symbol_matches(self, service, sample_candidate):
        score = service.compute_score(sample_candidate)
        assert score.symbol == sample_candidate["symbol"]

    def test_compute_score_total_between_zero_and_one(self, service, sample_candidate):
        score = service.compute_score(sample_candidate)
        assert 0.0 <= score.total_score <= 1.0

    def test_compute_score_component_scores_between_zero_and_one(self, service, sample_candidate):
        score = service.compute_score(sample_candidate)
        assert 0.0 <= score.liquidity_score <= 1.0
        assert 0.0 <= score.volatility_score <= 1.0
        assert 0.0 <= score.momentum_score <= 1.0
        assert 0.0 <= score.spread_score <= 1.0
        assert 0.0 <= score.volume_consistency_score <= 1.0

    def test_compute_score_high_quality_candidate_scores_higher(self, service, sample_candidate, low_quality_candidate):
        high_score = service.compute_score(sample_candidate)
        low_score = service.compute_score(low_quality_candidate)
        assert high_score.total_score > low_score.total_score

    def test_compute_score_total_is_weighted_sum(self, service, sample_candidate):
        score = service.compute_score(sample_candidate)
        weights = service.weights
        expected = (
            weights.liquidity * score.liquidity_score
            + weights.volatility * score.volatility_score
            + weights.momentum * score.momentum_score
            + weights.spread * score.spread_score
            + weights.volume_consistency * score.volume_consistency_score
        )
        assert score.total_score == pytest.approx(expected, rel=1e-5)

    def test_compute_score_different_weights_change_result(self, sample_candidate):
        weights_a = TradabilityWeights(
            liquidity=0.5,
            volatility=0.1,
            momentum=0.2,
            spread=0.1,
            volume_consistency=0.1,
        )
        weights_b = TradabilityWeights(
            liquidity=0.1,
            volatility=0.5,
            momentum=0.2,
            spread=0.1,
            volume_consistency=0.1,
        )
        service_a = TradabilityService(weights=weights_a)
        service_b = TradabilityService(weights=weights_b)
        score_a = service_a.compute_score(sample_candidate)
        score_b = service_b.compute_score(sample_candidate)
        assert score_a.total_score != score_b.total_score

    def test_compute_score_liquidity_score_higher_for_high_volume(self, service):
        high_vol = {
            "symbol": "HIGH",
            "avg_volume": 100_000_000,
            "price": 100.0,
            "bid": 99.95,
            "ask": 100.05,
            "daily_returns": [0.01, -0.01, 0.01, -0.01, 0.01],
            "volume_history": [100_000_000] * 5,
        }
        low_vol = {
            "symbol": "LOW",
            "avg_volume": 1_000,
            "price": 100.0,
            "bid": 99.95,
            "ask": 100.05,
            "daily_returns": [0.01, -0.01, 0.01, -0.01, 0.01],
            "volume_history": [1_000] * 5,
        }
        high_score = service.compute_score(high_vol)
        low_score = service.compute_score(low_vol)
        assert high_score.liquidity_score > low_score.liquidity_score

    def test_compute_score_spread_score_higher_for_tight_spread(self, service):
        tight = {
            "symbol": "TIGHT",
            "avg_volume": 10_000_000,
            "price": 100.0,
            "bid": 99.99,
            "ask": 100.01,
            "daily_returns": [0.01, -0.01, 0.01, -0.01, 0.01],
            "volume_history": [10_000_000] * 5,
        }
        wide = {
            "symbol": "WIDE",
            "avg_volume": 10_000_000,
            "price": 100.0,
            "bid": 95.0,
            "ask": 105.0,
            "daily_returns": [0.01, -0.01, 0.01, -0.01, 0.01],
            "volume_history": [10_000_000] * 5,
        }
        tight_score = service.compute_score(tight)
        wide_score = service.compute_score(wide)
        assert tight_score.spread_score > wide_score.spread_score

    def test_compute_score_volatility_score_higher_for_low_volatility(self, service):
        stable = {
            "symbol": "STABLE",
            "avg_volume": 10_000_000,
            "price": 100.0,
            "bid": 99.95,
            "ask": 100.05,
            "daily_returns": [0.001, -0.001, 0.001, -0.001, 0.001],
            "volume_history": [10_000_000] * 5,
        }
        volatile = {
            "symbol": "VOLATILE",
            "avg_volume": 10_000_000,
            "price": 100.0,
            "bid": 99.95,
            "ask": 100.05,
            "daily_returns": [0.15, -0.20, 0.18, -0.22, 0.25],
            "volume_history": [10_000_000] * 5,
        }
        stable_score = service.compute_score(stable)
        volatile_score = service.compute_score(volatile)
        assert stable_score.volatility_score > volatile_score.volatility_score


class TestRankCandidates:
    def test_rank_candidates_returns_list(self, service, multiple_candidates):
        ranked = service.rank_candidates(multiple_candidates)
        assert isinstance(ranked, list)

    def test_rank_candidates_returns_all_candidates(self, service, multiple_candidates):
        ranked = service.rank_candidates(multiple_candidates)
        assert len(ranked) == len(multiple_candidates)

    def test_rank_candidates_returns_tradability_scores(self, service, multiple_candidates):
        ranked = service.rank_candidates(multiple_candidates)
        for item in ranked:
            assert isinstance(item, TradabilityScore)

    def test_rank_candidates_sorted_descending(self, service, multiple_candidates):
        ranked = service.rank_candidates(multiple_candidates)
        scores = [item.total_score for item in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_rank_candidates_first_is_best(self, service, multiple_candidates):
        ranked = service.rank_candidates(multiple_candidates)
        assert ranked[0].total_score >= ranked[-1].total_score

    def test_rank_candidates_low_quality_last(self, service, multiple_candidates):
        ranked = service.rank_candidates(multiple_candidates)
        symbols = [item.symbol for item in ranked]
        assert symbols[-1] == "LOWQ"

    def test_rank_candidates_empty_list_returns_empty(self, service):
        ranked = service.rank_candidates([])
        assert ranked == []

    def test_rank_candidates_single_candidate(self, service, sample_candidate):
        ranked = service.rank_candidates([sample_candidate])
        assert len(ranked) == 1
        assert ranked[0].symbol == sample_candidate["symbol"]

    def test_rank_candidates_all_symbols_present(self, service, multiple_candidates):
        ranked = service.rank_candidates(multiple_candidates)
        ranked_symbols = {item.symbol for item in ranked}
        expected_symbols = {c["symbol"] for c in multiple_candidates}
        assert ranked_symbols == expected_symbols

    def test_rank_candidates_stable_sort_equal_scores(self, service):
        identical_a = {
            "symbol": "AAA",
            "avg_volume": 10_000_000,
            "price": 100.0,
            "bid": 99.95,
            "ask": 100.05,
            "daily_returns": [0.01, -0.01, 0.01, -0.01, 0.01],
            "volume_history": [10_000_000] * 5,
        }
        identical_b = {
            "symbol": "BBB",
            "avg_volume": 10_000_000,
            "price": 100.0,
            "bid": 99.95,
            "ask": 100.05,
            "daily_returns": [0.01, -0.01, 0.01, -0.01, 0.01],
            "volume_history": [10_000_000] * 5,
        }
        ranked = service.rank_candidates([identical_a, identical_b])
        assert len(ranked) == 2
        assert ranked[0].total_score == ranked[1].total_score


class TestGetBestTrade:
    def test_get_best_trade_returns_tradability_score(self, service, multiple_candidates):
        best = service.get_best_trade(multiple_candidates)
        assert isinstance(best, TradabilityScore)

    def test_get_best_trade_returns_highest_score(self, service, multiple_candidates):
        best = service.get_best_trade(multiple_candidates)
        ranked = service.rank_candidates(multiple_candidates)
        assert best.symbol == ranked[0].symbol
        assert best.total_score == ranked[0].total_score

    def test_get_best_trade_not_low_quality(self, service, multiple_candidates):
        best = service.get_best_trade(multiple_candidates)
        assert best.symbol != "LOWQ"

    def test_get_best_trade_empty_list_raises(self, service):
        with pytest.raises((ValueError, IndexError, Exception)):
            service.get_best_trade([])

    def test_get_best_trade_single_candidate(self, service, sample_candidate):
        best = service.get_best_trade([sample_candidate])
        assert best.symbol == sample_candidate["symbol"]

    def test_get_best_trade_score_between_zero_and_one(self, service, multiple_candidates):
        best = service.get_best_trade(multiple_candidates)
        assert 0.0 <= best.total_score <= 1.0

    def test_get_best_trade_consistent_with_rank(self, service, multiple_candidates):
        best = service.get_best_trade(multiple_candidates)
        ranked = service.rank_candidates(multiple_candidates)
        assert best.total_score == ranked[0].total_score

    def test_get_best_trade_two_candidates_returns_better(self, service):
        good = {
            "symbol": "GOOD",
            "avg_volume": 80_000_000,
            "price": 175.0,
            "bid": 174.95,
            "ask": 175.05,
            "daily_returns": [0.01, -0.005, 0.02, 0.015, -0.01],
            "volume_history": [80_000_000, 82_000_000, 79_000_000, 81_000_000, 80_500_000],
        }
        bad = {
            "symbol": "BAD",
            "avg_volume": 1_000,
            "price": 1.0,
            "bid": 0.80,
            "ask": 1.20,
            "daily_returns": [0.20, -0.25, 0.30, -0.28, 0.22],
            "volume_history": [1_000, 100, 5_000, 50, 2_000],
        }
        best = service.get_best_trade([good, bad])
        assert best.symbol == "GOOD"


class TestTradabilityServiceInitialization:
    def test_service_accepts_custom_weights(self, default_weights):
        svc = TradabilityService(weights=default_weights)
        assert svc.weights == default_weights

    def test_service_uses_default_weights_when_none_provided(self):
        svc = TradabilityService()
        assert isinstance(svc.weights, TradabilityWeights)

    def test_service_weights_are_tradability_weights_instance(self, service):
        assert isinstance(service.weights, TradabilityWeights)

    def test_service_stores_weights_correctly(self, default_weights):
        svc = TradabilityService(weights=default_weights)
        assert svc.weights.liquidity == default_weights.liquidity
        assert svc.weights.volatility == default_weights.volatility
        assert svc.weights.momentum == default_weights.momentum
        assert svc.weights.spread == default_weights.spread
        assert svc.weights.volume_consistency == default_weights.volume_consistency


class TestNormalizationEdgeCases:
    def test_very_high_volume_capped_at_one(self, service):
        candidate = {
            "symbol": "HUGE",
            "avg_volume": 10_000_000_000,
            "price": 100.0,
            "bid": 99.99,
            "ask": 100.01,
            "daily_returns": [0.001, -0.001, 0.001, -0.001, 0.001],
            "volume_history": [10_000_000_000] * 5,
        }
        score = service.compute_score(candidate)
        assert score.liquidity_score <= 1.0

    def test_very_high_volatility_capped_at_zero(self, service):
        candidate = {
            "symbol": "CRAZY",
            "avg_volume": 1_000_000,
            "price": 100.0,
            "bid": 99.0,
            "ask": 101.0,
            "daily_returns": [0.5, -0.5, 0.5, -0.5, 0.5],
            "volume_history": [1_000_000] * 5,
        }
        score = service.compute_score(candidate)
        assert score.volatility_score >= 0.0

    def test_perfect_volume_consistency_scores_high(self, service):
        candidate = {
            "symbol": "PERFECT",
            "avg_volume": 10_000_000,
            "price": 100.0,
            "bid": 99.99,
            "ask": 100.01,
            "daily_returns": [0.005, -0.005, 0.005, -0.005, 0.005],
            "volume_history": [10_000_000, 10_000_000, 10_000_000, 10_000_000, 10_000_000],
        }
        score = service.compute_score(candidate)
        assert score.volume_consistency_score > 0.8

    def test_all_scores_are_floats(self, service, sample_candidate):
        score = service.compute_score(sample_candidate)
        assert isinstance(score.total_score, float)
        assert isinstance(score.liquidity_score, float)
        assert isinstance(score.volatility_score, float)
        assert isinstance(score.momentum_score, float)
        assert isinstance(score.spread_score, float)
        assert isinstance(score.volume_consistency_score, float)