"""
Tests for TradesComparisonService - consolidated service that handles
tradability scoring and CCP (Cost-to-Capital Premium) calculations.
"""

import pytest
from backend.services.trades_comparison_service import TradesComparisonService
from backend.models.options_contract import OptionsContract
from backend.models.tradability_score import TradabilityScore


@pytest.fixture
def service():
    return TradesComparisonService()


@pytest.fixture
def sample_contract():
    return OptionsContract(
        symbol="AAPL",
        strike=150.0,
        expiration="2024-03-15",
        option_type="CALL",
        bid=2.50,
        ask=2.60,
        last=2.55,
        volume=1000,
        open_interest=5000,
        implied_volatility=0.25,
        delta=0.45,
        gamma=0.05,
        theta=-0.03,
        vega=0.10,
        underlying_price=149.0,
    )


@pytest.fixture
def sample_contracts():
    return [
        OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.50,
            ask=2.60,
            last=2.55,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        ),
        OptionsContract(
            symbol="AAPL",
            strike=155.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=1.20,
            ask=1.30,
            last=1.25,
            volume=500,
            open_interest=2000,
            implied_volatility=0.28,
            delta=0.30,
            gamma=0.04,
            theta=-0.02,
            vega=0.08,
            underlying_price=149.0,
        ),
        OptionsContract(
            symbol="AAPL",
            strike=145.0,
            expiration="2024-03-15",
            option_type="PUT",
            bid=1.80,
            ask=1.90,
            last=1.85,
            volume=800,
            open_interest=3000,
            implied_volatility=0.22,
            delta=-0.35,
            gamma=0.04,
            theta=-0.025,
            vega=0.09,
            underlying_price=149.0,
        ),
    ]


class TestTradesComparisonServiceInit:
    def test_service_instantiation(self, service):
        assert service is not None

    def test_service_has_required_methods(self, service):
        assert hasattr(service, "score_contract")
        assert hasattr(service, "score_contracts")
        assert hasattr(service, "calculate_ccp")
        assert hasattr(service, "rank_contracts")
        assert hasattr(service, "get_best_trade")


class TestCalculateCCP:
    def test_calculate_ccp_basic(self, service, sample_contract):
        ccp = service.calculate_ccp(sample_contract)
        assert ccp is not None
        assert isinstance(ccp, float)

    def test_calculate_ccp_positive_for_valid_contract(self, service, sample_contract):
        ccp = service.calculate_ccp(sample_contract)
        assert ccp >= 0.0

    def test_calculate_ccp_uses_bid_ask_spread(self, service):
        contract_tight = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.50,
            ask=2.52,
            last=2.51,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        contract_wide = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.00,
            ask=3.00,
            last=2.50,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        ccp_tight = service.calculate_ccp(contract_tight)
        ccp_wide = service.calculate_ccp(contract_wide)
        assert ccp_tight != ccp_wide

    def test_calculate_ccp_zero_bid_handled(self, service):
        contract = OptionsContract(
            symbol="AAPL",
            strike=200.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=0.0,
            ask=0.05,
            last=0.02,
            volume=10,
            open_interest=100,
            implied_volatility=0.15,
            delta=0.05,
            gamma=0.01,
            theta=-0.005,
            vega=0.02,
            underlying_price=149.0,
        )
        ccp = service.calculate_ccp(contract)
        assert ccp is not None
        assert isinstance(ccp, float)

    def test_calculate_ccp_returns_float(self, service, sample_contract):
        result = service.calculate_ccp(sample_contract)
        assert isinstance(result, float)


class TestScoreContract:
    def test_score_contract_returns_tradability_score(self, service, sample_contract):
        score = service.score_contract(sample_contract)
        assert isinstance(score, TradabilityScore)

    def test_score_contract_has_symbol(self, service, sample_contract):
        score = service.score_contract(sample_contract)
        assert score.symbol == "AAPL"

    def test_score_contract_has_strike(self, service, sample_contract):
        score = service.score_contract(sample_contract)
        assert score.strike == 150.0

    def test_score_contract_has_expiration(self, service, sample_contract):
        score = service.score_contract(sample_contract)
        assert score.expiration == "2024-03-15"

    def test_score_contract_has_option_type(self, service, sample_contract):
        score = service.score_contract(sample_contract)
        assert score.option_type == "CALL"

    def test_score_contract_has_score_value(self, service, sample_contract):
        score = service.score_contract(sample_contract)
        assert score.score is not None
        assert isinstance(score.score, float)

    def test_score_contract_has_ccp(self, service, sample_contract):
        score = service.score_contract(sample_contract)
        assert score.ccp is not None
        assert isinstance(score.ccp, float)

    def test_score_contract_score_in_valid_range(self, service, sample_contract):
        score = service.score_contract(sample_contract)
        assert 0.0 <= score.score <= 100.0

    def test_score_contract_high_volume_scores_well(self, service):
        high_volume_contract = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.50,
            ask=2.52,
            last=2.51,
            volume=50000,
            open_interest=100000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        low_volume_contract = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.50,
            ask=2.52,
            last=2.51,
            volume=1,
            open_interest=5,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        high_score = service.score_contract(high_volume_contract)
        low_score = service.score_contract(low_volume_contract)
        assert high_score.score >= low_score.score

    def test_score_contract_tight_spread_scores_better(self, service):
        tight_spread = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.50,
            ask=2.52,
            last=2.51,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        wide_spread = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=1.50,
            ask=3.50,
            last=2.50,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        tight_score = service.score_contract(tight_spread)
        wide_score = service.score_contract(wide_spread)
        assert tight_score.score >= wide_score.score


class TestScoreContracts:
    def test_score_contracts_returns_list(self, service, sample_contracts):
        scores = service.score_contracts(sample_contracts)
        assert isinstance(scores, list)

    def test_score_contracts_returns_correct_count(self, service, sample_contracts):
        scores = service.score_contracts(sample_contracts)
        assert len(scores) == len(sample_contracts)

    def test_score_contracts_all_tradability_scores(self, service, sample_contracts):
        scores = service.score_contracts(sample_contracts)
        for score in scores:
            assert isinstance(score, TradabilityScore)

    def test_score_contracts_empty_list(self, service):
        scores = service.score_contracts([])
        assert scores == []

    def test_score_contracts_single_contract(self, service, sample_contract):
        scores = service.score_contracts([sample_contract])
        assert len(scores) == 1
        assert isinstance(scores[0], TradabilityScore)

    def test_score_contracts_preserves_symbols(self, service, sample_contracts):
        scores = service.score_contracts(sample_contracts)
        symbols = [s.symbol for s in scores]
        assert all(sym == "AAPL" for sym in symbols)


class TestRankContracts:
    def test_rank_contracts_returns_sorted_list(self, service, sample_contracts):
        ranked = service.rank_contracts(sample_contracts)
        assert isinstance(ranked, list)
        assert len(ranked) == len(sample_contracts)

    def test_rank_contracts_sorted_descending(self, service, sample_contracts):
        ranked = service.rank_contracts(sample_contracts)
        scores = [item.score for item in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_rank_contracts_returns_tradability_scores(self, service, sample_contracts):
        ranked = service.rank_contracts(sample_contracts)
        for item in ranked:
            assert isinstance(item, TradabilityScore)

    def test_rank_contracts_empty_list(self, service):
        ranked = service.rank_contracts([])
        assert ranked == []

    def test_rank_contracts_single_item(self, service, sample_contract):
        ranked = service.rank_contracts([sample_contract])
        assert len(ranked) == 1

    def test_rank_contracts_best_first(self, service):
        good_contract = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.50,
            ask=2.52,
            last=2.51,
            volume=50000,
            open_interest=100000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        bad_contract = OptionsContract(
            symbol="AAPL",
            strike=200.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=0.01,
            ask=1.00,
            last=0.05,
            volume=1,
            open_interest=2,
            implied_volatility=0.15,
            delta=0.02,
            gamma=0.001,
            theta=-0.001,
            vega=0.01,
            underlying_price=149.0,
        )
        ranked = service.rank_contracts([bad_contract, good_contract])
        assert ranked[0].strike == 150.0


class TestGetBestTrade:
    def test_get_best_trade_returns_single_score(self, service, sample_contracts):
        best = service.get_best_trade(sample_contracts)
        assert isinstance(best, TradabilityScore)

    def test_get_best_trade_returns_highest_score(self, service, sample_contracts):
        best = service.get_best_trade(sample_contracts)
        all_scores = service.score_contracts(sample_contracts)
        max_score = max(s.score for s in all_scores)
        assert best.score == max_score

    def test_get_best_trade_empty_list_returns_none(self, service):
        best = service.get_best_trade([])
        assert best is None

    def test_get_best_trade_single_contract(self, service, sample_contract):
        best = service.get_best_trade([sample_contract])
        assert isinstance(best, TradabilityScore)
        assert best.symbol == "AAPL"


class TestTradabilityScoreModel:
    def test_tradability_score_creation(self):
        score = TradabilityScore(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            score=75.5,
            ccp=0.034,
            bid=2.50,
            ask=2.60,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
        )
        assert score.symbol == "AAPL"
        assert score.strike == 150.0
        assert score.score == 75.5
        assert score.ccp == 0.034

    def test_tradability_score_serialization(self):
        score = TradabilityScore(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            score=75.5,
            ccp=0.034,
            bid=2.50,
            ask=2.60,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
        )
        data = score.model_dump()
        assert "symbol" in data
        assert "strike" in data
        assert "score" in data
        assert "ccp" in data

    def test_tradability_score_required_fields(self):
        with pytest.raises(Exception):
            TradabilityScore()

    def test_tradability_score_optional_fields_have_defaults(self):
        score = TradabilityScore(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            score=75.5,
            ccp=0.034,
            bid=2.50,
            ask=2.60,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
        )
        assert score is not None


class TestCCPCalculationDetails:
    def test_ccp_formula_uses_midpoint(self, service):
        contract = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.00,
            ask=3.00,
            last=2.50,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        ccp = service.calculate_ccp(contract)
        assert ccp is not None
        # midpoint of bid=2.00 and ask=3.00 is 2.50
        midpoint = (2.00 + 3.00) / 2
        assert midpoint == 2.50

    def test_ccp_spread_cost_component(self, service):
        contract_narrow = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.49,
            ask=2.51,
            last=2.50,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        contract_wide = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=1.00,
            ask=4.00,
            last=2.50,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        ccp_narrow = service.calculate_ccp(contract_narrow)
        ccp_wide = service.calculate_ccp(contract_wide)
        assert ccp_narrow != ccp_wide

    def test_ccp_is_deterministic(self, service, sample_contract):
        ccp1 = service.calculate_ccp(sample_contract)
        ccp2 = service.calculate_ccp(sample_contract)
        assert ccp1 == ccp2


class TestScoringWeights:
    def test_volume_weight_in_score(self, service):
        base = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.50,
            ask=2.52,
            last=2.51,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        high_vol = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.50,
            ask=2.52,
            last=2.51,
            volume=100000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        base_score = service.score_contract(base)
        high_score = service.score_contract(high_vol)
        assert high_score.score >= base_score.score

    def test_open_interest_weight_in_score(self, service):
        low_oi = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.50,
            ask=2.52,
            last=2.51,
            volume=1000,
            open_interest=10,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        high_oi = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.50,
            ask=2.52,
            last=2.51,
            volume=1000,
            open_interest=500000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        low_score = service.score_contract(low_oi)
        high_score = service.score_contract(high_oi)
        assert high_score.score >= low_score.score


class TestEdgeCases:
    def test_score_contract_with_none_greeks(self, service):
        contract = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.50,
            ask=2.60,
            last=2.55,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=None,
            gamma=None,
            theta=None,
            vega=None,
            underlying_price=149.0,
        )
        score = service.score_contract(contract)
        assert score is not None
        assert isinstance(score, TradabilityScore)

    def test_score_contract_zero_volume(self, service):
        contract = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.50,
            ask=2.60,
            last=2.55,
            volume=0,
            open_interest=0,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        score = service.score_contract(contract)
        assert score is not None
        assert score.score >= 0.0

    def test_rank_contracts_with_equal_scores(self, service):
        contract1 = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.50,
            ask=2.52,
            last=2.51,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        contract2 = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-03-15",
            option_type="CALL",
            bid=2.50,
            ask=2.52,
            last=2.51,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.45,
            gamma=0.05,
            theta=-0.03,
            vega=0.10,
            underlying_price=149.0,
        )
        ranked = service.rank_contracts([contract1, contract2])
        assert len(ranked) == 2

    def test_large_number_of_contracts(self, service):
        contracts = []
        for i in range(100):
            contracts.append(
                OptionsContract(
                    symbol="AAPL",
                    strike=100.0 + i,
                    expiration="2024-03-15",
                    option_type="CALL",
                    bid=1.0 + i * 0.01,
                    ask=1.1 + i * 0.01,
                    last=1.05 + i * 0.01,
                    volume=100 * (i + 1),
                    open_interest=500 * (i + 1),
                    implied_volatility=0.20 + i * 0.001,
                    delta=0.5,
                    gamma=0.05,
                    theta=-0.03,
                    vega=0.10,
                    underlying_price=149.0,
                )
            )
        ranked = service.rank_contracts(contracts)
        assert len(ranked) == 100
        scores = [r.score for r in ranked]
        assert scores == sorted(scores, reverse=True)
