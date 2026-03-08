import pytest
from unittest.mock import MagicMock, patch
from backend.services.tradability_service import TradabilityService
from backend.models.tradability import TradabilityWeights, ScoredTrade


@pytest.fixture
def default_weights():
    return TradabilityWeights(
        liquidity=0.3,
        volatility=0.2,
        momentum=0.2,
        spread=0.15,
        volume_trend=0.15,
    )


@pytest.fixture
def service(default_weights):
    return TradabilityService(weights=default_weights)


@pytest.fixture
def sample_trade():
    return {
        "symbol": "AAPL",
        "price": 150.0,
        "bid": 149.9,
        "ask": 150.1,
        "volume": 1_000_000,
        "avg_volume": 800_000,
        "high_24h": 152.0,
        "low_24h": 148.0,
        "price_change_pct": 1.5,
        "market_cap": 2_500_000_000_000,
    }


@pytest.fixture
def sample_trades():
    return [
        {
            "symbol": "AAPL",
            "price": 150.0,
            "bid": 149.9,
            "ask": 150.1,
            "volume": 1_000_000,
            "avg_volume": 800_000,
            "high_24h": 152.0,
            "low_24h": 148.0,
            "price_change_pct": 1.5,
            "market_cap": 2_500_000_000_000,
        },
        {
            "symbol": "GOOG",
            "price": 2800.0,
            "bid": 2799.0,
            "ask": 2801.0,
            "volume": 500_000,
            "avg_volume": 600_000,
            "high_24h": 2850.0,
            "low_24h": 2750.0,
            "price_change_pct": -0.5,
            "market_cap": 1_800_000_000_000,
        },
        {
            "symbol": "TSLA",
            "price": 700.0,
            "bid": 699.0,
            "ask": 701.0,
            "volume": 2_000_000,
            "avg_volume": 1_500_000,
            "high_24h": 720.0,
            "low_24h": 680.0,
            "price_change_pct": 3.0,
            "market_cap": 700_000_000_000,
        },
    ]


class TestTradabilityWeights:
    def test_default_weights_sum_to_one(self):
        weights = TradabilityWeights()
        total = (
            weights.liquidity
            + weights.volatility
            + weights.momentum
            + weights.spread
            + weights.volume_trend
        )
        assert abs(total - 1.0) < 1e-9

    def test_custom_weights_accepted(self):
        weights = TradabilityWeights(
            liquidity=0.4,
            volatility=0.1,
            momentum=0.2,
            spread=0.1,
            volume_trend=0.2,
        )
        assert weights.liquidity == 0.4
        assert weights.volatility == 0.1

    def test_weights_must_be_non_negative(self):
        with pytest.raises(Exception):
            TradabilityWeights(
                liquidity=-0.1,
                volatility=0.3,
                momentum=0.3,
                spread=0.25,
                volume_trend=0.25,
            )

    def test_weights_must_not_exceed_one_each(self):
        with pytest.raises(Exception):
            TradabilityWeights(
                liquidity=1.5,
                volatility=0.1,
                momentum=0.1,
                spread=0.1,
                volume_trend=0.1,
            )


class TestScoredTrade:
    def test_scored_trade_creation(self):
        trade = ScoredTrade(
            symbol="AAPL",
            score=0.85,
            liquidity_score=0.9,
            volatility_score=0.8,
            momentum_score=0.75,
            spread_score=0.95,
            volume_trend_score=0.7,
            raw_data={"price": 150.0},
        )
        assert trade.symbol == "AAPL"
        assert trade.score == 0.85

    def test_scored_trade_score_range(self):
        with pytest.raises(Exception):
            ScoredTrade(
                symbol="AAPL",
                score=1.5,
                liquidity_score=0.9,
                volatility_score=0.8,
                momentum_score=0.75,
                spread_score=0.95,
                volume_trend_score=0.7,
                raw_data={},
            )

    def test_scored_trade_negative_score_rejected(self):
        with pytest.raises(Exception):
            ScoredTrade(
                symbol="AAPL",
                score=-0.1,
                liquidity_score=0.9,
                volatility_score=0.8,
                momentum_score=0.75,
                spread_score=0.95,
                volume_trend_score=0.7,
                raw_data={},
            )


class TestTradabilityServiceMetricExtraction:
    def test_extract_spread_metric(self, service, sample_trade):
        metrics = service.extract_metrics(sample_trade)
        assert "spread" in metrics
        assert metrics["spread"] >= 0

    def test_extract_volume_trend_metric(self, service, sample_trade):
        metrics = service.extract_metrics(sample_trade)
        assert "volume_trend" in metrics

    def test_extract_volatility_metric(self, service, sample_trade):
        metrics = service.extract_metrics(sample_trade)
        assert "volatility" in metrics
        assert metrics["volatility"] >= 0

    def test_extract_momentum_metric(self, service, sample_trade):
        metrics = service.extract_metrics(sample_trade)
        assert "momentum" in metrics

    def test_extract_liquidity_metric(self, service, sample_trade):
        metrics = service.extract_metrics(sample_trade)
        assert "liquidity" in metrics
        assert metrics["liquidity"] >= 0

    def test_spread_calculation_correctness(self, service):
        trade = {
            "symbol": "TEST",
            "price": 100.0,
            "bid": 99.0,
            "ask": 101.0,
            "volume": 100_000,
            "avg_volume": 100_000,
            "high_24h": 105.0,
            "low_24h": 95.0,
            "price_change_pct": 0.0,
            "market_cap": 1_000_000_000,
        }
        metrics = service.extract_metrics(trade)
        expected_spread = (101.0 - 99.0) / 100.0
        assert abs(metrics["spread"] - expected_spread) < 1e-9

    def test_volume_trend_above_average(self, service):
        trade = {
            "symbol": "TEST",
            "price": 100.0,
            "bid": 99.5,
            "ask": 100.5,
            "volume": 200_000,
            "avg_volume": 100_000,
            "high_24h": 105.0,
            "low_24h": 95.0,
            "price_change_pct": 1.0,
            "market_cap": 1_000_000_000,
        }
        metrics = service.extract_metrics(trade)
        assert metrics["volume_trend"] > 1.0

    def test_volume_trend_below_average(self, service):
        trade = {
            "symbol": "TEST",
            "price": 100.0,
            "bid": 99.5,
            "ask": 100.5,
            "volume": 50_000,
            "avg_volume": 100_000,
            "high_24h": 105.0,
            "low_24h": 95.0,
            "price_change_pct": 1.0,
            "market_cap": 1_000_000_000,
        }
        metrics = service.extract_metrics(trade)
        assert metrics["volume_trend"] < 1.0

    def test_volatility_calculation(self, service):
        trade = {
            "symbol": "TEST",
            "price": 100.0,
            "bid": 99.5,
            "ask": 100.5,
            "volume": 100_000,
            "avg_volume": 100_000,
            "high_24h": 110.0,
            "low_24h": 90.0,
            "price_change_pct": 0.0,
            "market_cap": 1_000_000_000,
        }
        metrics = service.extract_metrics(trade)
        expected_volatility = (110.0 - 90.0) / 100.0
        assert abs(metrics["volatility"] - expected_volatility) < 1e-9

    def test_missing_optional_fields_handled_gracefully(self, service):
        trade = {
            "symbol": "MINIMAL",
            "price": 100.0,
            "bid": 99.5,
            "ask": 100.5,
            "volume": 100_000,
            "avg_volume": 100_000,
            "high_24h": 105.0,
            "low_24h": 95.0,
            "price_change_pct": 0.5,
            "market_cap": 500_000_000,
        }
        metrics = service.extract_metrics(trade)
        assert isinstance(metrics, dict)
        assert len(metrics) > 0

    def test_zero_avg_volume_handled(self, service):
        trade = {
            "symbol": "TEST",
            "price": 100.0,
            "bid": 99.5,
            "ask": 100.5,
            "volume": 100_000,
            "avg_volume": 0,
            "high_24h": 105.0,
            "low_24h": 95.0,
            "price_change_pct": 0.0,
            "market_cap": 1_000_000_000,
        }
        metrics = service.extract_metrics(trade)
        assert "volume_trend" in metrics
        assert metrics["volume_trend"] >= 0

    def test_zero_price_handled(self, service):
        trade = {
            "symbol": "TEST",
            "price": 0.0,
            "bid": 0.0,
            "ask": 0.0,
            "volume": 100_000,
            "avg_volume": 100_000,
            "high_24h": 0.0,
            "low_24h": 0.0,
            "price_change_pct": 0.0,
            "market_cap": 0,
        }
        metrics = service.extract_metrics(trade)
        assert isinstance(metrics, dict)


class TestTradabilityServiceScoring:
    def test_score_single_trade_returns_scored_trade(self, service, sample_trade):
        scored = service.score_trade(sample_trade)
        assert isinstance(scored, ScoredTrade)

    def test_score_is_between_zero_and_one(self, service, sample_trade):
        scored = service.score_trade(sample_trade)
        assert 0.0 <= scored.score <= 1.0

    def test_individual_scores_between_zero_and_one(self, service, sample_trade):
        scored = service.score_trade(sample_trade)
        assert 0.0 <= scored.liquidity_score <= 1.0
        assert 0.0 <= scored.volatility_score <= 1.0
        assert 0.0 <= scored.momentum_score <= 1.0
        assert 0.0 <= scored.spread_score <= 1.0
        assert 0.0 <= scored.volume_trend_score <= 1.0

    def test_symbol_preserved_in_scored_trade(self, service, sample_trade):
        scored = service.score_trade(sample_trade)
        assert scored.symbol == sample_trade["symbol"]

    def test_raw_data_preserved_in_scored_trade(self, service, sample_trade):
        scored = service.score_trade(sample_trade)
        assert scored.raw_data == sample_trade

    def test_weighted_score_computation(self, service):
        trade = {
            "symbol": "PERFECT",
            "price": 100.0,
            "bid": 99.99,
            "ask": 100.01,
            "volume": 10_000_000,
            "avg_volume": 1_000_000,
            "high_24h": 101.0,
            "low_24h": 99.0,
            "price_change_pct": 5.0,
            "market_cap": 10_000_000_000_000,
        }
        scored = service.score_trade(trade)
        assert scored.score > 0.0

    def test_score_reflects_weights(self):
        weights_high_liquidity = TradabilityWeights(
            liquidity=0.8,
            volatility=0.05,
            momentum=0.05,
            spread=0.05,
            volume_trend=0.05,
        )
        weights_high_spread = TradabilityWeights(
            liquidity=0.05,
            volatility=0.05,
            momentum=0.05,
            spread=0.8,
            volume_trend=0.05,
        )
        service_liq = TradabilityService(weights=weights_high_liquidity)
        service_spread = TradabilityService(weights=weights_high_spread)

        trade_high_liq_low_spread = {
            "symbol": "TEST",
            "price": 100.0,
            "bid": 99.99,
            "ask": 100.01,
            "volume": 10_000_000,
            "avg_volume": 1_000_000,
            "high_24h": 101.0,
            "low_24h": 99.0,
            "price_change_pct": 1.0,
            "market_cap": 10_000_000_000_000,
        }

        score_liq = service_liq.score_trade(trade_high_liq_low_spread).score
        score_spread = service_spread.score_trade(trade_high_liq_low_spread).score
        assert score_liq != score_spread

    def test_score_trade_with_negative_momentum(self, service):
        trade = {
            "symbol": "BEAR",
            "price": 50.0,
            "bid": 49.5,
            "ask": 50.5,
            "volume": 500_000,
            "avg_volume": 600_000,
            "high_24h": 55.0,
            "low_24h": 45.0,
            "price_change_pct": -5.0,
            "market_cap": 500_000_000,
        }
        scored = service.score_trade(trade)
        assert 0.0 <= scored.score <= 1.0
        assert 0.0 <= scored.momentum_score <= 1.0


class TestTradabilityServiceRanking:
    def test_rank_trades_returns_list(self, service, sample_trades):
        ranked = service.rank_trades(sample_trades)
        assert isinstance(ranked, list)

    def test_rank_trades_returns_all_trades(self, service, sample_trades):
        ranked = service.rank_trades(sample_trades)
        assert len(ranked) == len(sample_trades)

    def test_rank_trades_sorted_descending(self, service, sample_trades):
        ranked = service.rank_trades(sample_trades)
        scores = [t.score for t in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_rank_trades_returns_scored_trades(self, service, sample_trades):
        ranked = service.rank_trades(sample_trades)
        for trade in ranked:
            assert isinstance(trade, ScoredTrade)

    def test_rank_empty_list(self, service):
        ranked = service.rank_trades([])
        assert ranked == []

    def test_rank_single_trade(self, service, sample_trade):
        ranked = service.rank_trades([sample_trade])
        assert len(ranked) == 1
        assert isinstance(ranked[0], ScoredTrade)

    def test_get_best_trades_returns_top_n(self, service, sample_trades):
        best = service.get_best_trades(sample_trades, top_n=2)
        assert len(best) == 2

    def test_get_best_trades_are_highest_scored(self, service, sample_trades):
        all_ranked = service.rank_trades(sample_trades)
        best = service.get_best_trades(sample_trades, top_n=2)
        assert best[0].score == all_ranked[0].score
        assert best[1].score == all_ranked[1].score

    def test_get_best_trades_top_n_exceeds_available(self, service, sample_trades):
        best = service.get_best_trades(sample_trades, top_n=100)
        assert len(best) == len(sample_trades)

    def test_get_best_trades_top_n_zero(self, service, sample_trades):
        best = service.get_best_trades(sample_trades, top_n=0)
        assert best == []

    def test_get_best_trades_default_top_n(self, service, sample_trades):
        best = service.get_best_trades(sample_trades)
        assert len(best) <= len(sample_trades)
        assert len(best) > 0

    def test_rank_trades_all_same_score(self, service):
        trades = [
            {
                "symbol": f"SYM{i}",
                "price": 100.0,
                "bid": 99.5,
                "ask": 100.5,
                "volume": 100_000,
                "avg_volume": 100_000,
                "high_24h": 105.0,
                "low_24h": 95.0,
                "price_change_pct": 0.0,
                "market_cap": 1_000_000_000,
            }
            for i in range(5)
        ]
        ranked = service.rank_trades(trades)
        assert len(ranked) == 5
        scores = [t.score for t in ranked]
        assert scores == sorted(scores, reverse=True)


class TestTradabilityServiceNormalization:
    def test_normalization_clamps_to_zero_one(self, service):
        extreme_trade = {
            "symbol": "EXTREME",
            "price": 0.001,
            "bid": 0.0,
            "ask": 1000.0,
            "volume": 999_999_999,
            "avg_volume": 1,
            "high_24h": 999_999.0,
            "low_24h": 0.001,
            "price_change_pct": 9999.0,
            "market_cap": 999_999_999_999_999,
        }
        scored = service.score_trade(extreme_trade)
        assert 0.0 <= scored.score <= 1.0
        assert 0.0 <= scored.liquidity_score <= 1.0
        assert 0.0 <= scored.volatility_score <= 1.0
        assert 0.0 <= scored.momentum_score <= 1.0
        assert 0.0 <= scored.spread_score <= 1.0
        assert 0.0 <= scored.volume_trend_score <= 1.0

    def test_normalization_with_reference_data(self, service, sample_trades):
        scored_trades = [service.score_trade(t) for t in sample_trades]
        for st in scored_trades:
            assert 0.0 <= st.score <= 1.0


class TestTradabilityServiceConfiguration:
    def test_service_uses_provided_weights(self):
        custom_weights = TradabilityWeights(
            liquidity=0.5,
            volatility=0.1,
            momentum=0.1,
            spread=0.2,
            volume_trend=0.1,
        )
        svc = TradabilityService(weights=custom_weights)
        assert svc.weights.liquidity == 0.5

    def test_service_default_weights(self):
        svc = TradabilityService()
        assert svc.weights is not None
        total = (
            svc.weights.liquidity
            + svc.weights.volatility
            + svc.weights.momentum
            + svc.weights.spread
            + svc.weights.volume_trend
        )
        assert abs(total - 1.0) < 1e-9

    def test_service_weights_immutable_after_creation(self):
        weights = TradabilityWeights(
            liquidity=0.3,
            volatility=0.2,
            momentum=0.2,
            spread=0.15,
            volume_trend=0.15,
        )
        svc = TradabilityService(weights=weights)
        original_liquidity = svc.weights.liquidity
        with pytest.raises(Exception):
            svc.weights.liquidity = 0.9
        assert svc.weights.liquidity == original_liquidity


class TestTradabilityServiceEdgeCases:
    def test_score_trade_with_equal_bid_ask(self, service):
        trade = {
            "symbol": "ZERO_SPREAD",
            "price": 100.0,
            "bid": 100.0,
            "ask": 100.0,
            "volume": 100_000,
            "avg_volume": 100_000,
            "high_24h": 105.0,
            "low_24h": 95.0,
            "price_change_pct": 0.0,
            "market_cap": 1_000_000_000,
        }
        scored = service.score_trade(trade)
        assert 0.0 <= scored.score <= 1.0

    def test_score_trade_with_equal_high_low(self, service):
        trade = {
            "symbol": "FLAT",
            "price": 100.0,
            "bid": 99.5,
            "ask": 100.5,
            "volume": 100_000,
            "avg_volume": 100_000,
            "high_24h": 100.0,
            "low_24h": 100.0,
            "price_change_pct": 0.0,
            "market_cap": 1_000_000_000,
        }
        scored = service.score_trade(trade)
        assert 0.0 <= scored.score <= 1.0

    def test_large_number_of_trades(self, service):
        trades = [
            {
                "symbol": f"SYM{i:04d}",
                "price": float(100 + i),
                "bid": float(99 + i),
                "ask": float(101 + i),
                "volume": 100_000 + i * 1000,
                "avg_volume": 100_000,
                "high_24h": float(110 + i),
                "low_24h": float(90 + i),
                "price_change_pct": float(i % 10),
                "market_cap": 1_000_000_000 + i * 1_000_000,
            }
            for i in range(500)
        ]
        ranked = service.rank_trades(trades)
        assert len(ranked) == 500
        scores = [t.score for t in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_score_trade_very_large_market_cap(self, service):
        trade = {
            "symbol": "HUGE",
            "price": 3000.0,
            "bid": 2999.0,
            "ask": 3001.0,
            "volume": 50_000_000,
            "avg_volume": 10_000_000,
            "high_24h": 3100.0,
            "low_24h": 2900.0,
            "price_change_pct": 2.0,
            "market_cap": 100_000_000_000_000,
        }
        scored = service.score_trade(trade)
        assert 0.0 <= scored.score <= 1.0

    def test_score_trade_very_small_market_cap(self, service):
        trade = {
            "symbol": "TINY",
            "price": 0.01,
            "bid": 0.009,
            "ask": 0.011,
            "volume": 1000,
            "avg_volume": 500,
            "high_24h": 0.012,
            "low_24h": 0.008,
            "price_change_pct": 0.1,
            "market_cap": 10_000,
        }
        scored = service.score_trade(trade)
        assert 0.0 <= scored.score <= 1.0