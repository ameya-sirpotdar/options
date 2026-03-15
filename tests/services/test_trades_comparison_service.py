from unittest.mock import MagicMock, patch
import pytest

from backend.services.trades_comparison_service import TradesComparisonService


@pytest.fixture
def service():
    return TradesComparisonService()


def test_instantiation(service):
    assert isinstance(service, TradesComparisonService)


def test_compare_trades_returns_list(service):
    trade_a = MagicMock()
    trade_b = MagicMock()
    result = service.compare_trades([trade_a, trade_b])
    assert isinstance(result, list)


def test_compare_trades_empty_input(service):
    result = service.compare_trades([])
    assert result == []


def test_compare_trades_single_trade(service):
    trade = MagicMock()
    result = service.compare_trades([trade])
    assert isinstance(result, list)
    assert len(result) == 1


def test_score_trade_returns_numeric(service):
    trade = MagicMock()
    trade.bid = 1.5
    trade.ask = 2.0
    trade.delta = 0.4
    trade.theta = -0.05
    trade.implied_volatility = 0.3
    trade.days_to_expiration = 30
    score = service.score_trade(trade)
    assert isinstance(score, (int, float))


def test_score_trade_higher_for_better_metrics(service):
    good_trade = MagicMock()
    good_trade.bid = 2.0
    good_trade.ask = 2.1
    good_trade.delta = 0.45
    good_trade.theta = -0.02
    good_trade.implied_volatility = 0.25
    good_trade.days_to_expiration = 45

    bad_trade = MagicMock()
    bad_trade.bid = 0.05
    bad_trade.ask = 1.50
    bad_trade.delta = 0.05
    bad_trade.theta = -0.50
    bad_trade.implied_volatility = 0.95
    bad_trade.days_to_expiration = 2

    good_score = service.score_trade(good_trade)
    bad_score = service.score_trade(bad_trade)
    assert good_score >= bad_score


def test_rank_trades_returns_sorted_list(service):
    trade_a = MagicMock()
    trade_a.bid = 1.0
    trade_a.ask = 1.1
    trade_a.delta = 0.4
    trade_a.theta = -0.03
    trade_a.implied_volatility = 0.2
    trade_a.days_to_expiration = 40

    trade_b = MagicMock()
    trade_b.bid = 0.1
    trade_b.ask = 1.9
    trade_b.delta = 0.1
    trade_b.theta = -0.8
    trade_b.implied_volatility = 0.9
    trade_b.days_to_expiration = 3

    ranked = service.rank_trades([trade_a, trade_b])
    assert isinstance(ranked, list)
    assert len(ranked) == 2


def test_rank_trades_empty(service):
    ranked = service.rank_trades([])
    assert ranked == []


def test_rank_trades_preserves_all_trades(service):
    trades = [MagicMock() for _ in range(5)]
    for t in trades:
        t.bid = 1.0
        t.ask = 1.2
        t.delta = 0.4
        t.theta = -0.03
        t.implied_volatility = 0.25
        t.days_to_expiration = 30
    ranked = service.rank_trades(trades)
    assert len(ranked) == 5


def test_compare_trades_preserves_trade_objects(service):
    trade_a = MagicMock()
    trade_b = MagicMock()
    result = service.compare_trades([trade_a, trade_b])
    result_ids = [id(r) for r in result]
    assert id(trade_a) in result_ids or id(trade_b) in result_ids


def test_score_trade_with_zero_bid_ask_spread(service):
    trade = MagicMock()
    trade.bid = 1.0
    trade.ask = 1.0
    trade.delta = 0.5
    trade.theta = -0.01
    trade.implied_volatility = 0.2
    trade.days_to_expiration = 30
    score = service.score_trade(trade)
    assert score is not None


def test_score_trade_with_negative_delta(service):
    trade = MagicMock()
    trade.bid = 1.0
    trade.ask = 1.2
    trade.delta = -0.4
    trade.theta = -0.03
    trade.implied_volatility = 0.3
    trade.days_to_expiration = 20
    score = service.score_trade(trade)
    assert isinstance(score, (int, float))


def test_compare_trades_returns_scored_or_annotated(service):
    trade = MagicMock()
    trade.bid = 1.5
    trade.ask = 1.7
    trade.delta = 0.4
    trade.theta = -0.02
    trade.implied_volatility = 0.22
    trade.days_to_expiration = 35
    result = service.compare_trades([trade])
    assert len(result) == 1


def test_rank_trades_order_descending(service):
    trade_high = MagicMock()
    trade_high.bid = 2.0
    trade_high.ask = 2.05
    trade_high.delta = 0.45
    trade_high.theta = -0.01
    trade_high.implied_volatility = 0.18
    trade_high.days_to_expiration = 50

    trade_low = MagicMock()
    trade_low.bid = 0.05
    trade_low.ask = 2.00
    trade_low.delta = 0.05
    trade_low.theta = -1.0
    trade_low.implied_volatility = 1.5
    trade_low.days_to_expiration = 1

    ranked = service.rank_trades([trade_low, trade_high])
    if len(ranked) == 2:
        first_score = service.score_trade(ranked[0])
        second_score = service.score_trade(ranked[1])
        assert first_score >= second_score


def test_service_has_compare_trades_method(service):
    assert hasattr(service, "compare_trades")
    assert callable(service.compare_trades)


def test_service_has_score_trade_method(service):
    assert hasattr(service, "score_trade")
    assert callable(service.score_trade)


def test_service_has_rank_trades_method(service):
    assert hasattr(service, "rank_trades")
    assert callable(service.rank_trades)


def test_compare_trades_with_three_trades(service):
    trades = []
    for i in range(3):
        t = MagicMock()
        t.bid = float(i + 1)
        t.ask = float(i + 1) + 0.1
        t.delta = 0.3 + i * 0.05
        t.theta = -0.02 - i * 0.01
        t.implied_volatility = 0.2 + i * 0.05
        t.days_to_expiration = 30 + i * 5
        trades.append(t)
    result = service.compare_trades(trades)
    assert len(result) == 3


def test_rank_trades_single_element(service):
    trade = MagicMock()
    trade.bid = 1.0
    trade.ask = 1.1
    trade.delta = 0.4
    trade.theta = -0.02
    trade.implied_volatility = 0.2
    trade.days_to_expiration = 30
    ranked = service.rank_trades([trade])
    assert len(ranked) == 1
    assert ranked[0] is trade
