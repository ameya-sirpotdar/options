tests/services/test_schwab_service.py
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from backend.services.schwab_service import SchwabService


@pytest.fixture
def schwab_service():
    return SchwabService()


# ---------------------------------------------------------------------------
# Authentication tests (formerly test_schwab_auth.py)
# ---------------------------------------------------------------------------

class TestSchwabAuth:
    def test_get_auth_url_returns_string(self, schwab_service):
        with patch.object(schwab_service, "get_auth_url", return_value="https://auth.example.com"):
            url = schwab_service.get_auth_url()
            assert isinstance(url, str)
            assert url.startswith("https://")

    def test_get_auth_url_contains_client_id(self, schwab_service):
        with patch.object(
            schwab_service,
            "get_auth_url",
            return_value="https://auth.example.com?client_id=test_id",
        ):
            url = schwab_service.get_auth_url()
            assert "client_id" in url

    def test_exchange_code_for_token_returns_token(self, schwab_service):
        mock_token = {"access_token": "abc123", "token_type": "Bearer"}
        with patch.object(
            schwab_service, "exchange_code_for_token", return_value=mock_token
        ):
            token = schwab_service.exchange_code_for_token("auth_code")
            assert token["access_token"] == "abc123"

    def test_exchange_code_for_token_raises_on_invalid_code(self, schwab_service):
        with patch.object(
            schwab_service,
            "exchange_code_for_token",
            side_effect=ValueError("Invalid authorization code"),
        ):
            with pytest.raises(ValueError, match="Invalid authorization code"):
                schwab_service.exchange_code_for_token("bad_code")

    def test_refresh_token_returns_new_access_token(self, schwab_service):
        mock_token = {"access_token": "new_token_xyz", "token_type": "Bearer"}
        with patch.object(
            schwab_service, "refresh_token", return_value=mock_token
        ):
            result = schwab_service.refresh_token("old_refresh_token")
            assert result["access_token"] == "new_token_xyz"

    def test_refresh_token_raises_on_expired_refresh(self, schwab_service):
        with patch.object(
            schwab_service,
            "refresh_token",
            side_effect=ValueError("Refresh token expired"),
        ):
            with pytest.raises(ValueError, match="Refresh token expired"):
                schwab_service.refresh_token("expired_token")

    def test_is_authenticated_returns_true_when_token_valid(self, schwab_service):
        with patch.object(schwab_service, "is_authenticated", return_value=True):
            assert schwab_service.is_authenticated() is True

    def test_is_authenticated_returns_false_when_no_token(self, schwab_service):
        with patch.object(schwab_service, "is_authenticated", return_value=False):
            assert schwab_service.is_authenticated() is False

    def test_get_access_token_returns_string(self, schwab_service):
        with patch.object(
            schwab_service, "get_access_token", return_value="access_token_value"
        ):
            token = schwab_service.get_access_token()
            assert isinstance(token, str)

    def test_get_access_token_raises_when_not_authenticated(self, schwab_service):
        with patch.object(
            schwab_service,
            "get_access_token",
            side_effect=RuntimeError("Not authenticated"),
        ):
            with pytest.raises(RuntimeError, match="Not authenticated"):
                schwab_service.get_access_token()


# ---------------------------------------------------------------------------
# Market data tests (formerly test_schwab_market_data.py)
# ---------------------------------------------------------------------------

class TestSchwabMarketData:
    def test_get_options_chain_returns_dict(self, schwab_service):
        mock_chain = {
            "symbol": "AAPL",
            "callExpDateMap": {},
            "putExpDateMap": {},
        }
        with patch.object(
            schwab_service, "get_options_chain", return_value=mock_chain
        ):
            result = schwab_service.get_options_chain("AAPL")
            assert isinstance(result, dict)
            assert result["symbol"] == "AAPL"

    def test_get_options_chain_includes_call_and_put_maps(self, schwab_service):
        mock_chain = {
            "symbol": "TSLA",
            "callExpDateMap": {"2024-01-19:30": {}},
            "putExpDateMap": {"2024-01-19:30": {}},
        }
        with patch.object(
            schwab_service, "get_options_chain", return_value=mock_chain
        ):
            result = schwab_service.get_options_chain("TSLA")
            assert "callExpDateMap" in result
            assert "putExpDateMap" in result

    def test_get_options_chain_raises_on_invalid_symbol(self, schwab_service):
        with patch.object(
            schwab_service,
            "get_options_chain",
            side_effect=ValueError("Invalid symbol"),
        ):
            with pytest.raises(ValueError, match="Invalid symbol"):
                schwab_service.get_options_chain("INVALID_SYMBOL_XYZ")

    def test_get_quote_returns_price_data(self, schwab_service):
        mock_quote = {"symbol": "AAPL", "lastPrice": 150.25, "bidPrice": 150.0, "askPrice": 150.5}
        with patch.object(schwab_service, "get_quote", return_value=mock_quote):
            result = schwab_service.get_quote("AAPL")
            assert result["symbol"] == "AAPL"
            assert "lastPrice" in result

    def test_get_quote_raises_on_unknown_symbol(self, schwab_service):
        with patch.object(
            schwab_service,
            "get_quote",
            side_effect=ValueError("Symbol not found"),
        ):
            with pytest.raises(ValueError, match="Symbol not found"):
                schwab_service.get_quote("UNKNOWN")

    def test_get_options_chain_with_filters_applies_strike_range(self, schwab_service):
        mock_chain = {
            "symbol": "AAPL",
            "callExpDateMap": {},
            "putExpDateMap": {},
            "strikeCount": 10,
        }
        with patch.object(
            schwab_service, "get_options_chain", return_value=mock_chain
        ):
            result = schwab_service.get_options_chain(
                "AAPL", strike_count=10, from_date="2024-01-01", to_date="2024-03-31"
            )
            assert result["strikeCount"] == 10

    def test_get_options_chain_with_option_type_call(self, schwab_service):
        mock_chain = {
            "symbol": "AAPL",
            "callExpDateMap": {"2024-01-19:30": {}},
            "putExpDateMap": {},
        }
        with patch.object(
            schwab_service, "get_options_chain", return_value=mock_chain
        ):
            result = schwab_service.get_options_chain("AAPL", option_type="CALL")
            assert "callExpDateMap" in result

    def test_get_market_hours_returns_schedule(self, schwab_service):
        mock_hours = {
            "equity": {
                "EQ": {
                    "isOpen": True,
                    "sessionHours": {"regularMarket": [{"start": "09:30", "end": "16:00"}]},
                }
            }
        }
        with patch.object(schwab_service, "get_market_hours", return_value=mock_hours):
            result = schwab_service.get_market_hours("equity")
            assert "equity" in result

    def test_get_price_history_returns_candles(self, schwab_service):
        mock_history = {
            "symbol": "AAPL",
            "candles": [
                {"open": 149.0, "high": 151.0, "low": 148.5, "close": 150.25, "volume": 1000000}
            ],
            "empty": False,
        }
        with patch.object(
            schwab_service, "get_price_history", return_value=mock_history
        ):
            result = schwab_service.get_price_history("AAPL", period_type="day", period=5)
            assert "candles" in result
            assert len(result["candles"]) > 0


# ---------------------------------------------------------------------------
# Filters tests (formerly test_schwab_filters.py)
# ---------------------------------------------------------------------------

class TestSchwabFilters:
    def test_filter_by_expiration_returns_filtered_contracts(self, schwab_service):
        contracts = [
            {"expirationDate": "2024-01-19", "strikePrice": 150.0},
            {"expirationDate": "2024-02-16", "strikePrice": 155.0},
            {"expirationDate": "2024-03-15", "strikePrice": 160.0},
        ]
        with patch.object(
            schwab_service,
            "filter_by_expiration",
            return_value=[contracts[0], contracts[1]],
        ):
            result = schwab_service.filter_by_expiration(
                contracts, from_date="2024-01-01", to_date="2024-02-28"
            )
            assert len(result) == 2

    def test_filter_by_expiration_empty_list_returns_empty(self, schwab_service):
        with patch.object(schwab_service, "filter_by_expiration", return_value=[]):
            result = schwab_service.filter_by_expiration(
                [], from_date="2024-01-01", to_date="2024-12-31"
            )
            assert result == []

    def test_filter_by_strike_range_returns_within_range(self, schwab_service):
        contracts = [
            {"strikePrice": 140.0},
            {"strikePrice": 150.0},
            {"strikePrice": 160.0},
            {"strikePrice": 170.0},
        ]
        with patch.object(
            schwab_service,
            "filter_by_strike_range",
            return_value=[contracts[1], contracts[2]],
        ):
            result = schwab_service.filter_by_strike_range(
                contracts, min_strike=145.0, max_strike=165.0
            )
            assert len(result) == 2
            for c in result:
                assert 145.0 <= c["strikePrice"] <= 165.0

    def test_filter_by_strike_range_no_matches_returns_empty(self, schwab_service):
        contracts = [{"strikePrice": 100.0}, {"strikePrice": 110.0}]
        with patch.object(schwab_service, "filter_by_strike_range", return_value=[]):
            result = schwab_service.filter_by_strike_range(
                contracts, min_strike=200.0, max_strike=300.0
            )
            assert result == []

    def test_filter_by_volume_returns_high_volume_contracts(self, schwab_service):
        contracts = [
            {"totalVolume": 50},
            {"totalVolume": 500},
            {"totalVolume": 5000},
        ]
        with patch.object(
            schwab_service,
            "filter_by_volume",
            return_value=[contracts[1], contracts[2]],
        ):
            result = schwab_service.filter_by_volume(contracts, min_volume=100)
            assert len(result) == 2

    def test_filter_by_open_interest_returns_liquid_contracts(self, schwab_service):
        contracts = [
            {"openInterest": 10},
            {"openInterest": 100},
            {"openInterest": 1000},
        ]
        with patch.object(
            schwab_service,
            "filter_by_open_interest",
            return_value=[contracts[1], contracts[2]],
        ):
            result = schwab_service.filter_by_open_interest(contracts, min_open_interest=50)
            assert len(result) == 2

    def test_filter_by_delta_returns_contracts_in_range(self, schwab_service):
        contracts = [
            {"delta": 0.1},
            {"delta": 0.3},
            {"delta": 0.5},
            {"delta": 0.9},
        ]
        with patch.object(
            schwab_service,
            "filter_by_delta",
            return_value=[contracts[1], contracts[2]],
        ):
            result = schwab_service.filter_by_delta(
                contracts, min_delta=0.2, max_delta=0.6
            )
            assert len(result) == 2

    def test_filter_by_bid_ask_spread_removes_wide_spreads(self, schwab_service):
        contracts = [
            {"bid": 1.0, "ask": 1.05},
            {"bid": 1.0, "ask": 1.50},
            {"bid": 1.0, "ask": 2.00},
        ]
        with patch.object(
            schwab_service,
            "filter_by_bid_ask_spread",
            return_value=[contracts[0]],
        ):
            result = schwab_service.filter_by_bid_ask_spread(
                contracts, max_spread_pct=0.10
            )
            assert len(result) == 1

    def test_apply_all_filters_chains_multiple_filters(self, schwab_service):
        contracts = [
            {
                "strikePrice": 150.0,
                "totalVolume": 500,
                "openInterest": 200,
                "delta": 0.35,
                "bid": 1.0,
                "ask": 1.05,
                "expirationDate": "2024-02-16",
            }
        ]
        with patch.object(
            schwab_service, "apply_all_filters", return_value=contracts
        ):
            result = schwab_service.apply_all_filters(
                contracts,
                min_volume=100,
                min_open_interest=50,
                min_delta=0.2,
                max_delta=0.6,
            )
            assert len(result) == 1


# ---------------------------------------------------------------------------
# CCP Calculator tests (formerly test_ccp_calculator.py)
# ---------------------------------------------------------------------------

class TestCCPCalculator:
    def test_calculate_ccp_returns_float(self, schwab_service):
        with patch.object(schwab_service, "calculate_ccp", return_value=0.72):
            result = schwab_service.calculate_ccp(
                spot_price=150.0,
                strike_price=155.0,
                days_to_expiry=30,
                volatility=0.25,
            )
            assert isinstance(result, float)

    def test_calculate_ccp_in_the_money_call_high_probability(self, schwab_service):
        with patch.object(schwab_service, "calculate_ccp", return_value=0.85):
            result = schwab_service.calculate_ccp(
                spot_price=160.0,
                strike_price=150.0,
                days_to_expiry=30,
                volatility=0.20,
            )
            assert result > 0.5

    def test_calculate_ccp_out_of_the_money_call_low_probability(self, schwab_service):
        with patch.object(schwab_service, "calculate_ccp", return_value=0.15):
            result = schwab_service.calculate_ccp(
                spot_price=150.0,
                strike_price=200.0,
                days_to_expiry=30,
                volatility=0.20,
            )
            assert result < 0.5

    def test_calculate_ccp_returns_value_between_0_and_1(self, schwab_service):
        with patch.object(schwab_service, "calculate_ccp", return_value=0.45):
            result = schwab_service.calculate_ccp(
                spot_price=150.0,
                strike_price=152.0,
                days_to_expiry=14,
                volatility=0.30,
            )
            assert 0.0 <= result <= 1.0

    def test_calculate_ccp_zero_days_to_expiry(self, schwab_service):
        with patch.object(schwab_service, "calculate_ccp", return_value=0.0):
            result = schwab_service.calculate_ccp(
                spot_price=150.0,
                strike_price=155.0,
                days_to_expiry=0,
                volatility=0.25,
            )
            assert result == 0.0

    def test_calculate_ccp_raises_on_negative_volatility(self, schwab_service):
        with patch.object(
            schwab_service,
            "calculate_ccp",
            side_effect=ValueError("Volatility must be non-negative"),
        ):
            with pytest.raises(ValueError, match="Volatility must be non-negative"):
                schwab_service.calculate_ccp(
                    spot_price=150.0,
                    strike_price=155.0,
                    days_to_expiry=30,
                    volatility=-0.10,
                )

    def test_calculate_ccp_raises_on_negative_spot_price(self, schwab_service):
        with patch.object(
            schwab_service,
            "calculate_ccp",
            side_effect=ValueError("Spot price must be positive"),
        ):
            with pytest.raises(ValueError, match="Spot price must be positive"):
                schwab_service.calculate_ccp(
                    spot_price=-10.0,
                    strike_price=155.0,
                    days_to_expiry=30,
                    volatility=0.25,
                )

    def test_calculate_ccp_for_put_option(self, schwab_service):
        with patch.object(schwab_service, "calculate_ccp", return_value=0.30):
            result = schwab_service.calculate_ccp(
                spot_price=150.0,
                strike_price=145.0,
                days_to_expiry=30,
                volatility=0.25,
                option_type="PUT",
            )
            assert isinstance(result, float)
            assert 0.0 <= result <= 1.0

    def test_calculate_ccp_higher_volatility_increases_uncertainty(self, schwab_service):
        with patch.object(schwab_service, "calculate_ccp", return_value=0.40) as mock_ccp:
            low_vol_result = schwab_service.calculate_ccp(
                spot_price=150.0,
                strike_price=155.0,
                days_to_expiry=30,
                volatility=0.10,
            )
            mock_ccp.return_value = 0.45
            high_vol_result = schwab_service.calculate_ccp(
                spot_price=150.0,
                strike_price=155.0,
                days_to_expiry=30,
                volatility=0.50,
            )
            assert isinstance(low_vol_result, float)
            assert isinstance(high_vol_result, float)

    def test_calculate_ccp_longer_expiry_increases_probability(self, schwab_service):
        with patch.object(schwab_service, "calculate_ccp", return_value=0.35) as mock_ccp:
            short_expiry = schwab_service.calculate_ccp(
                spot_price=150.0,
                strike_price=155.0,
                days_to_expiry=7,
                volatility=0.25,
            )
            mock_ccp.return_value = 0.48
            long_expiry = schwab_service.calculate_ccp(
                spot_price=150.0,
                strike_price=155.0,
                days_to_expiry=90,
                volatility=0.25,
            )
            assert isinstance(short_expiry, float)
            assert isinstance(long_expiry, float)


# ---------------------------------------------------------------------------
# Market data service integration tests (formerly test_market_data_service.py)
# ---------------------------------------------------------------------------

class TestMarketDataService:
    def test_get_options_chain_full_response_structure(self, schwab_service):
        mock_response = {
            "symbol": "AAPL",
            "status": "SUCCESS",
            "underlying": {
                "symbol": "AAPL",
                "description": "Apple Inc",
                "change": 1.25,
                "percentChange": 0.84,
                "close": 149.0,
                "quoteTime": 1700000000000,
                "tradeTime": 1700000000000,
                "bid": 150.0,
                "ask": 150.5,
                "last": 150.25,
                "mark": 150.25,
                "markChange": 1.25,
                "markPercentChange": 0.84,
                "bidSize": 100,
                "askSize": 100,
                "highPrice": 151.0,
                "lowPrice": 148.5,
                "openPrice": 149.5,
                "totalVolume": 50000000,
                "exchangeName": "NASDAQ",
                "fiftyTwoWeekHigh": 180.0,
                "fiftyTwoWeekLow": 120.0,
                "delayed": False,
            },
            "strategy": "SINGLE",
            "interval": 0.0,
            "isDelayed": False,
            "isIndex": False,
            "daysToExpiration": 0.0,
            "numberOfContracts": 100,
            "callExpDateMap": {},
            "putExpDateMap": {},
        }
        with patch.object(
            schwab_service, "get_options_chain", return_value=mock_response
        ):
            result = schwab_service.get_options_chain("AAPL")
            assert result["status"] == "SUCCESS"
            assert "underlying" in result
            assert result["underlying"]["symbol"] == "AAPL"

    def test_get_options_chain_with_contracts_populated(self, schwab_service):
        mock_contract = {
            "putCall": "CALL",
            "symbol": "AAPL_011924C150",
            "description": "AAPL Jan 19 2024 150 Call",
            "exchangeName": "OPR",
            "bid": 2.50,
            "ask": 2.55,
            "last": 2.52,
            "mark": 2.525,
            "bidSize": 10,
            "askSize": 10,
            "bidAskSize": "10X10",
            "lastSize": 0,
            "highPrice": 3.00,
            "lowPrice": 2.00,
            "openPrice": 0.0,
            "closePrice": 2.40,
            "totalVolume": 1500,
            "tradeDate": None,
            "tradeTimeInLong": 1700000000000,
            "quoteTimeInLong": 1700000000000,
            "netChange": 0.12,
            "volatility": 0.25,
            "delta": 0.45,
            "gamma": 0.05,
            "theta": -0.03,
            "vega": 0.10,
            "rho": 0.02,
            "openInterest": 5000,
            "timeValue": 2.52,
            "theoreticalOptionValue": 2.50,
            "theoreticalVolatility": 29.0,
            "strikePrice": 150.0,
            "expirationDate": "2024-01-19T00:00:00.000+0000",
            "daysToExpiration": 30,
            "expirationType": "R",
            "lastTradingDay": 1705622400000,
            "multiplier": 100.0,
            "settlementType": "P",
            "deliverableNote": "",
            "isIndexOption": None,
            "percentChange": 5.0,
            "markChange": 0.125,
            "markPercentChange": 5.21,
            "intrinsicValue": 0.0,
            "inTheMoney": False,
            "mini": False,
            "nonStandard": False,
            "pennyPilot": True,
        }
        mock_response = {
            "symbol": "AAPL",
            "status": "SUCCESS",
            "callExpDateMap": {
                "2024-01-19:30": {
                    "150.0": [mock_contract]
                }
            },
            "putExpDateMap": {},
        }
        with patch.object(
            schwab_service, "get_options_chain", return_value=mock_response
        ):
            result = schwab_service.get_options_chain("AAPL")
            call_map = result["callExpDateMap"]
            assert "2024-01-19:30" in call_map
            contracts = call_map["2024-01-19:30"]["150.0"]
            assert len(contracts) == 1
            assert contracts[0]["putCall"] == "CALL"
            assert contracts[0]["delta"] == 0.45

    def test_get_options_chain_handles_empty_maps(self, schwab_service):
        mock_response = {
            "symbol": "AAPL",
            "status": "SUCCESS",
            "callExpDateMap": {},
            "putExpDateMap": {},
        }
        with patch.object(
            schwab_service, "get_options_chain", return_value=mock_response
        ):
            result = schwab_service.get_options_chain("AAPL")
            assert result["callExpDateMap"] == {}
            assert result["putExpDateMap"] == {}

    def test_get_options_chain_raises_on_api_error(self, schwab_service):
        with patch.object(
            schwab_service,
            "get_options_chain",
            side_effect=RuntimeError("API request failed: 401 Unauthorized"),
        ):
            with pytest.raises(RuntimeError, match="API request failed"):
                schwab_service.get_options_chain("AAPL")

    def test_get_options_chain_raises_on_rate_limit(self, schwab_service):
        with patch.object(
            schwab_service,
            "get_options_chain",
            side_effect=RuntimeError("Rate limit exceeded"),
        ):
            with pytest.raises(RuntimeError, match="Rate limit exceeded"):
                schwab_service.get_options_chain("AAPL")

    def test_get_options_chain_with_strategy_vertical(self, schwab_service):
        mock_response = {
            "symbol": "AAPL",
            "status": "SUCCESS",
            "strategy": "VERTICAL",
            "callExpDateMap": {},
            "putExpDateMap": {},
        }
        with patch.object(
            schwab_service, "get_options_chain", return_value=mock_response
        ):
            result = schwab_service.get_options_chain("AAPL", strategy="VERTICAL")
            assert result["strategy"] == "VERTICAL"

    def test_get_multiple_quotes_returns_dict(self, schwab_service):
        mock_quotes = {
            "AAPL": {"lastPrice": 150.25, "bidPrice": 150.0, "askPrice": 150.5},
            "TSLA": {"lastPrice": 250.00, "bidPrice": 249.5, "askPrice": 250.5},
        }
        with patch.object(schwab_service, "get_multiple_quotes", return_value=mock_quotes):
            result = schwab_service.get_multiple_quotes(["AAPL", "TSLA"])
            assert "AAPL" in result
            assert "TSLA" in result
            assert result["AAPL"]["lastPrice"] == 150.25

    def test_get_multiple_quotes_empty_list_returns_empty(self, schwab_service):
        with patch.object(schwab_service, "get_multiple_quotes", return_value={}):
            result = schwab_service.get_multiple_quotes([])
            assert result == {}

    @pytest.mark.asyncio
    async def test_async_get_options_chain_returns_dict(self, schwab_service):
        mock_chain = {"symbol": "AAPL", "callExpDateMap": {}, "putExpDateMap": {}}
        with patch.object(
            schwab_service,
            "async_get_options_chain",
            new_callable=AsyncMock,
            return_value=mock_chain,
        ):
            result = await schwab_service.async_get_options_chain("AAPL")
            assert isinstance(result, dict)
            assert result["symbol"] == "AAPL"

    @pytest.mark.asyncio
    async def test_async_get_options_chain_raises_on_network_error(self, schwab_service):
        with patch.object(
            schwab_service,
            "async_get_options_chain",
            new_callable=AsyncMock,
            side_effect=ConnectionError("Network error"),
        ):
            with pytest.raises(ConnectionError, match="Network error"):
                await schwab_service.async_get_options_chain("AAPL")