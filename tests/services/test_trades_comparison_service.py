"""Tests for TradesComparisonService."""
import pytest
from backend.services.trades_comparison_service import TradesComparisonService


@pytest.fixture
def service():
    return TradesComparisonService()


@pytest.fixture
def sample_options_chain():
    return {
        "symbol": "AAPL",
        "underlyingPrice": 150.0,
        "callExpDateMap": {
            "2024-01-19:30": {
                "150.0": [
                    {
                        "strikePrice": 150.0,
                        "expirationDate": "2024-01-19",
                        "daysToExpiration": 30,
                        "bid": 5.0,
                        "ask": 5.5,
                        "last": 5.25,
                        "volume": 1000,
                        "openInterest": 5000,
                        "volatility": 0.25,
                        "delta": 0.5,
                        "gamma": 0.05,
                        "theta": -0.1,
                        "vega": 0.2,
                        "inTheMoney": True,
                        "optionType": "CALL",
                    }
                ]
            }
        },
        "putExpDateMap": {
            "2024-01-19:30": {
                "150.0": [
                    {
                        "strikePrice": 150.0,
                        "expirationDate": "2024-01-19",
                        "daysToExpiration": 30,
                        "bid": 4.0,
                        "ask": 4.5,
                        "last": 4.25,
                        "volume": 800,
                        "openInterest": 4000,
                        "volatility": 0.25,
                        "delta": -0.5,
                        "gamma": 0.05,
                        "theta": -0.1,
                        "vega": 0.2,
                        "inTheMoney": False,
                        "optionType": "PUT",
                    }
                ]
            }
        },
    }


@pytest.fixture
def sample_contract():
    return {
        "strikePrice": 150.0,
        "expirationDate": "2024-01-19",
        "daysToExpiration": 30,
        "bid": 5.0,
        "ask": 5.5,
        "last": 5.25,
        "volume": 1000,
        "openInterest": 5000,
        "volatility": 0.25,
        "delta": 0.5,
        "gamma": 0.05,
        "theta": -0.1,
        "vega": 0.2,
        "inTheMoney": True,
        "optionType": "CALL",
        "underlyingPrice": 150.0,
    }


class TestTradesComparisonServiceInit:
    def test_service_initializes(self, service):
        assert service is not None

    def test_service_is_trades_comparison_service(self, service):
        assert isinstance(service, TradesComparisonService)


class TestScoreContract:
    def test_score_contract_returns_dict(self, service, sample_contract):
        result = service.score_contract(sample_contract)
        assert isinstance(result, dict)

    def test_score_contract_has_score_field(self, service, sample_contract):
        result = service.score_contract(sample_contract)
        assert "score" in result

    def test_score_contract_has_metrics_field(self, service, sample_contract):
        result = service.score_contract(sample_contract)
        assert "metrics" in result

    def test_score_contract_score_is_numeric(self, service, sample_contract):
        result = service.score_contract(sample_contract)
        assert isinstance(result["score"], (int, float))

    def test_score_contract_score_is_non_negative(self, service, sample_contract):
        result = service.score_contract(sample_contract)
        assert result["score"] >= 0

    def test_score_contract_metrics_is_dict(self, service, sample_contract):
        result = service.score_contract(sample_contract)
        assert isinstance(result["metrics"], dict)

    def test_score_contract_with_high_volume(self, service, sample_contract):
        sample_contract["volume"] = 100000
        result = service.score_contract(sample_contract)
        assert result["score"] > 0

    def test_score_contract_with_low_volume(self, service, sample_contract):
        sample_contract["volume"] = 1
        result = service.score_contract(sample_contract)
        assert result["score"] >= 0

    def test_score_contract_with_high_open_interest(self, service, sample_contract):
        sample_contract["openInterest"] = 100000
        result = service.score_contract(sample_contract)
        assert result["score"] > 0

    def test_score_contract_with_zero_volume(self, service, sample_contract):
        sample_contract["volume"] = 0
        result = service.score_contract(sample_contract)
        assert result["score"] >= 0

    def test_score_contract_with_zero_open_interest(self, service, sample_contract):
        sample_contract["openInterest"] = 0
        result = service.score_contract(sample_contract)
        assert result["score"] >= 0

    def test_score_contract_with_itm_call(self, service, sample_contract):
        sample_contract["inTheMoney"] = True
        sample_contract["optionType"] = "CALL"
        result = service.score_contract(sample_contract)
        assert "score" in result

    def test_score_contract_with_otm_put(self, service, sample_contract):
        sample_contract["inTheMoney"] = False
        sample_contract["optionType"] = "PUT"
        result = service.score_contract(sample_contract)
        assert "score" in result

    def test_score_contract_with_tight_spread(self, service, sample_contract):
        sample_contract["bid"] = 5.0
        sample_contract["ask"] = 5.1
        result = service.score_contract(sample_contract)
        assert result["score"] >= 0

    def test_score_contract_with_wide_spread(self, service, sample_contract):
        sample_contract["bid"] = 1.0
        sample_contract["ask"] = 10.0
        result = service.score_contract(sample_contract)
        assert result["score"] >= 0

    def test_score_contract_metrics_contains_volume(self, service, sample_contract):
        result = service.score_contract(sample_contract)
        assert "volume" in result["metrics"]

    def test_score_contract_with_near_expiration(self, service, sample_contract):
        sample_contract["daysToExpiration"] = 1
        result = service.score_contract(sample_contract)
        assert "score" in result

    def test_score_contract_with_far_expiration(self, service, sample_contract):
        sample_contract["daysToExpiration"] = 365
        result = service.score_contract(sample_contract)
        assert "score" in result

    def test_score_contract_with_high_volatility(self, service, sample_contract):
        sample_contract["volatility"] = 0.8
        result = service.score_contract(sample_contract)
        assert "score" in result

    def test_score_contract_with_low_volatility(self, service, sample_contract):
        sample_contract["volatility"] = 0.05
        result = service.score_contract(sample_contract)
        assert "score" in result


class TestRankContracts:
    def test_rank_contracts_returns_list(self, service, sample_options_chain):
        result = service.rank_contracts(sample_options_chain)
        assert isinstance(result, list)

    def test_rank_contracts_with_empty_chain(self, service):
        empty_chain = {
            "symbol": "AAPL",
            "underlyingPrice": 150.0,
            "callExpDateMap": {},
            "putExpDateMap": {},
        }
        result = service.rank_contracts(empty_chain)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_rank_contracts_returns_scored_contracts(self, service, sample_options_chain):
        result = service.rank_contracts(sample_options_chain)
        for item in result:
            assert "score" in item

    def test_rank_contracts_sorted_by_score_descending(self, service, sample_options_chain):
        result = service.rank_contracts(sample_options_chain)
        if len(result) > 1:
            for i in range(len(result) - 1):
                assert result[i]["score"] >= result[i + 1]["score"]

    def test_rank_contracts_includes_calls(self, service, sample_options_chain):
        result = service.rank_contracts(sample_options_chain)
        option_types = [r.get("optionType") for r in result]
        assert "CALL" in option_types

    def test_rank_contracts_includes_puts(self, service, sample_options_chain):
        result = service.rank_contracts(sample_options_chain)
        option_types = [r.get("optionType") for r in result]
        assert "PUT" in option_types

    def test_rank_contracts_with_multiple_expirations(self, service):
        chain = {
            "symbol": "AAPL",
            "underlyingPrice": 150.0,
            "callExpDateMap": {
                "2024-01-19:30": {
                    "150.0": [
                        {
                            "strikePrice": 150.0,
                            "expirationDate": "2024-01-19",
                            "daysToExpiration": 30,
                            "bid": 5.0,
                            "ask": 5.5,
                            "last": 5.25,
                            "volume": 1000,
                            "openInterest": 5000,
                            "volatility": 0.25,
                            "delta": 0.5,
                            "gamma": 0.05,
                            "theta": -0.1,
                            "vega": 0.2,
                            "inTheMoney": True,
                            "optionType": "CALL",
                        }
                    ]
                },
                "2024-02-16:58": {
                    "155.0": [
                        {
                            "strikePrice": 155.0,
                            "expirationDate": "2024-02-16",
                            "daysToExpiration": 58,
                            "bid": 3.0,
                            "ask": 3.5,
                            "last": 3.25,
                            "volume": 500,
                            "openInterest": 2500,
                            "volatility": 0.22,
                            "delta": 0.4,
                            "gamma": 0.04,
                            "theta": -0.08,
                            "vega": 0.18,
                            "inTheMoney": False,
                            "optionType": "CALL",
                        }
                    ]
                },
            },
            "putExpDateMap": {},
        }
        result = service.rank_contracts(chain)
        assert len(result) == 2

    def test_rank_contracts_with_multiple_strikes(self, service):
        chain = {
            "symbol": "AAPL",
            "underlyingPrice": 150.0,
            "callExpDateMap": {
                "2024-01-19:30": {
                    "145.0": [
                        {
                            "strikePrice": 145.0,
                            "expirationDate": "2024-01-19",
                            "daysToExpiration": 30,
                            "bid": 7.0,
                            "ask": 7.5,
                            "last": 7.25,
                            "volume": 2000,
                            "openInterest": 8000,
                            "volatility": 0.25,
                            "delta": 0.7,
                            "gamma": 0.04,
                            "theta": -0.12,
                            "vega": 0.18,
                            "inTheMoney": True,
                            "optionType": "CALL",
                        }
                    ],
                    "150.0": [
                        {
                            "strikePrice": 150.0,
                            "expirationDate": "2024-01-19",
                            "daysToExpiration": 30,
                            "bid": 5.0,
                            "ask": 5.5,
                            "last": 5.25,
                            "volume": 1000,
                            "openInterest": 5000,
                            "volatility": 0.25,
                            "delta": 0.5,
                            "gamma": 0.05,
                            "theta": -0.1,
                            "vega": 0.2,
                            "inTheMoney": True,
                            "optionType": "CALL",
                        }
                    ],
                }
            },
            "putExpDateMap": {},
        }
        result = service.rank_contracts(chain)
        assert len(result) == 2

    def test_rank_contracts_each_item_has_metrics(self, service, sample_options_chain):
        result = service.rank_contracts(sample_options_chain)
        for item in result:
            assert "metrics" in item

    def test_rank_contracts_each_item_has_strike_price(self, service, sample_options_chain):
        result = service.rank_contracts(sample_options_chain)
        for item in result:
            assert "strikePrice" in item

    def test_rank_contracts_each_item_has_expiration_date(self, service, sample_options_chain):
        result = service.rank_contracts(sample_options_chain)
        for item in result:
            assert "expirationDate" in item

    def test_rank_contracts_each_item_has_option_type(self, service, sample_options_chain):
        result = service.rank_contracts(sample_options_chain)
        for item in result:
            assert "optionType" in item


class TestGetTopTrades:
    def test_get_top_trades_returns_list(self, service, sample_options_chain):
        result = service.get_top_trades(sample_options_chain)
        assert isinstance(result, list)

    def test_get_top_trades_default_limit(self, service, sample_options_chain):
        result = service.get_top_trades(sample_options_chain)
        assert len(result) <= 10

    def test_get_top_trades_custom_limit(self, service, sample_options_chain):
        result = service.get_top_trades(sample_options_chain, limit=1)
        assert len(result) <= 1

    def test_get_top_trades_with_zero_limit(self, service, sample_options_chain):
        result = service.get_top_trades(sample_options_chain, limit=0)
        assert len(result) == 0

    def test_get_top_trades_with_large_limit(self, service, sample_options_chain):
        result = service.get_top_trades(sample_options_chain, limit=1000)
        assert isinstance(result, list)

    def test_get_top_trades_sorted_by_score(self, service, sample_options_chain):
        result = service.get_top_trades(sample_options_chain)
        if len(result) > 1:
            for i in range(len(result) - 1):
                assert result[i]["score"] >= result[i + 1]["score"]

    def test_get_top_trades_with_empty_chain(self, service):
        empty_chain = {
            "symbol": "AAPL",
            "underlyingPrice": 150.0,
            "callExpDateMap": {},
            "putExpDateMap": {},
        }
        result = service.get_top_trades(empty_chain)
        assert result == []

    def test_get_top_trades_each_item_has_score(self, service, sample_options_chain):
        result = service.get_top_trades(sample_options_chain)
        for item in result:
            assert "score" in item

    def test_get_top_trades_each_item_has_metrics(self, service, sample_options_chain):
        result = service.get_top_trades(sample_options_chain)
        for item in result:
            assert "metrics" in item


class TestCalculateCCP:
    def test_calculate_ccp_returns_float(self, service, sample_contract):
        result = service.calculate_ccp(sample_contract)
        assert isinstance(result, float)

    def test_calculate_ccp_between_zero_and_one(self, service, sample_contract):
        result = service.calculate_ccp(sample_contract)
        assert 0.0 <= result <= 1.0

    def test_calculate_ccp_call_itm(self, service, sample_contract):
        sample_contract["optionType"] = "CALL"
        sample_contract["inTheMoney"] = True
        sample_contract["delta"] = 0.7
        result = service.calculate_ccp(sample_contract)
        assert result > 0.5

    def test_calculate_ccp_put_otm(self, service, sample_contract):
        sample_contract["optionType"] = "PUT"
        sample_contract["inTheMoney"] = False
        sample_contract["delta"] = -0.3
        result = service.calculate_ccp(sample_contract)
        assert 0.0 <= result <= 1.0

    def test_calculate_ccp_with_delta_near_one(self, service, sample_contract):
        sample_contract["delta"] = 0.99
        result = service.calculate_ccp(sample_contract)
        assert result > 0.5

    def test_calculate_ccp_with_delta_near_zero(self, service, sample_contract):
        sample_contract["delta"] = 0.01
        result = service.calculate_ccp(sample_contract)
        assert result < 0.5

    def test_calculate_ccp_with_missing_delta(self, service, sample_contract):
        del sample_contract["delta"]
        result = service.calculate_ccp(sample_contract)
        assert isinstance(result, float)


class TestCalculateLiquidityScore:
    def test_calculate_liquidity_score_returns_float(self, service, sample_contract):
        result = service.calculate_liquidity_score(sample_contract)
        assert isinstance(result, float)

    def test_calculate_liquidity_score_non_negative(self, service, sample_contract):
        result = service.calculate_liquidity_score(sample_contract)
        assert result >= 0.0

    def test_calculate_liquidity_score_high_volume_high_oi(self, service, sample_contract):
        sample_contract["volume"] = 100000
        sample_contract["openInterest"] = 500000
        result = service.calculate_liquidity_score(sample_contract)
        assert result > 0

    def test_calculate_liquidity_score_zero_volume_zero_oi(self, service, sample_contract):
        sample_contract["volume"] = 0
        sample_contract["openInterest"] = 0
        result = service.calculate_liquidity_score(sample_contract)
        assert result == 0.0

    def test_calculate_liquidity_score_tight_spread_increases_score(self, service, sample_contract):
        tight_contract = dict(sample_contract)
        tight_contract["bid"] = 5.0
        tight_contract["ask"] = 5.1

        wide_contract = dict(sample_contract)
        wide_contract["bid"] = 1.0
        wide_contract["ask"] = 10.0

        tight_score = service.calculate_liquidity_score(tight_contract)
        wide_score = service.calculate_liquidity_score(wide_contract)
        assert tight_score >= wide_score

    def test_calculate_liquidity_score_with_zero_ask(self, service, sample_contract):
        sample_contract["ask"] = 0
        result = service.calculate_liquidity_score(sample_contract)
        assert isinstance(result, float)


class TestCompareContracts:
    def test_compare_contracts_returns_dict(self, service, sample_contract):
        contract_a = dict(sample_contract)
        contract_b = dict(sample_contract)
        contract_b["strikePrice"] = 155.0
        contract_b["volume"] = 2000
        result = service.compare_contracts(contract_a, contract_b)
        assert isinstance(result, dict)

    def test_compare_contracts_has_winner_field(self, service, sample_contract):
        contract_a = dict(sample_contract)
        contract_b = dict(sample_contract)
        contract_b["volume"] = 2000
        result = service.compare_contracts(contract_a, contract_b)
        assert "winner" in result

    def test_compare_contracts_has_scores_field(self, service, sample_contract):
        contract_a = dict(sample_contract)
        contract_b = dict(sample_contract)
        result = service.compare_contracts(contract_a, contract_b)
        assert "scores" in result

    def test_compare_contracts_winner_is_a_or_b(self, service, sample_contract):
        contract_a = dict(sample_contract)
        contract_b = dict(sample_contract)
        contract_b["volume"] = 99999
        result = service.compare_contracts(contract_a, contract_b)
        assert result["winner"] in ["a", "b", "tie"]

    def test_compare_contracts_scores_has_a_and_b(self, service, sample_contract):
        contract_a = dict(sample_contract)
        contract_b = dict(sample_contract)
        result = service.compare_contracts(contract_a, contract_b)
        assert "a" in result["scores"]
        assert "b" in result["scores"]

    def test_compare_contracts_identical_contracts_is_tie(self, service, sample_contract):
        contract_a = dict(sample_contract)
        contract_b = dict(sample_contract)
        result = service.compare_contracts(contract_a, contract_b)
        assert result["winner"] == "tie"

    def test_compare_contracts_higher_volume_wins(self, service, sample_contract):
        contract_a = dict(sample_contract)
        contract_a["volume"] = 100
        contract_a["openInterest"] = 100

        contract_b = dict(sample_contract)
        contract_b["volume"] = 100000
        contract_b["openInterest"] = 500000

        result = service.compare_contracts(contract_a, contract_b)
        assert result["winner"] == "b"


class TestEdgeCases:
    def test_score_contract_with_none_values(self, service):
        contract = {
            "strikePrice": 150.0,
            "expirationDate": "2024-01-19",
            "daysToExpiration": 30,
            "bid": None,
            "ask": None,
            "last": None,
            "volume": None,
            "openInterest": None,
            "volatility": None,
            "delta": None,
            "gamma": None,
            "theta": None,
            "vega": None,
            "inTheMoney": False,
            "optionType": "CALL",
            "underlyingPrice": 150.0,
        }
        result = service.score_contract(contract)
        assert isinstance(result, dict)
        assert "score" in result

    def test_rank_contracts_missing_keys(self, service):
        chain = {
            "underlyingPrice": 150.0,
        }
        result = service.rank_contracts(chain)
        assert isinstance(result, list)

    def test_get_top_trades_missing_keys(self, service):
        chain = {
            "underlyingPrice": 150.0,
        }
        result = service.get_top_trades(chain)
        assert isinstance(result, list)

    def test_score_contract_negative_delta(self, service, sample_contract):
        sample_contract["delta"] = -0.5
        result = service.score_contract(sample_contract)
        assert "score" in result

    def test_score_contract_zero_bid_ask(self, service, sample_contract):
        sample_contract["bid"] = 0.0
        sample_contract["ask"] = 0.0
        result = service.score_contract(sample_contract)
        assert "score" in result

    def test_rank_contracts_preserves_underlying_price(self, service, sample_options_chain):
        result = service.rank_contracts(sample_options_chain)
        for item in result:
            if "underlyingPrice" in item:
                assert item["underlyingPrice"] == 150.0

    def test_service_methods_exist(self, service):
        assert hasattr(service, "score_contract")
        assert hasattr(service, "rank_contracts")
        assert hasattr(service, "get_top_trades")
        assert hasattr(service, "calculate_ccp")
        assert hasattr(service, "calculate_liquidity_score")
        assert hasattr(service, "compare_contracts")

    def test_all_methods_callable(self, service):
        assert callable(service.score_contract)
        assert callable(service.rank_contracts)
        assert callable(service.get_top_trades)
        assert callable(service.calculate_ccp)
        assert callable(service.calculate_liquidity_score)
        assert callable(service.compare_contracts)
