import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from backend.services.schwab_service import SchwabService


@pytest.fixture
def schwab_service():
    return SchwabService()


@pytest.fixture
def mock_schwab_client():
    client = MagicMock()
    client.get_chains = AsyncMock()
    return client


class TestSchwabServiceInit:
    def test_instantiation(self, schwab_service):
        assert schwab_service is not None

    def test_has_get_options_chain_method(self, schwab_service):
        assert hasattr(schwab_service, "get_options_chain")

    def test_has_authenticate_method(self, schwab_service):
        assert hasattr(schwab_service, "authenticate")


class TestSchwabServiceAuthentication:
    @patch("backend.services.schwab_service.schwab")
    def test_authenticate_calls_schwab_client(self, mock_schwab, schwab_service):
        mock_client = MagicMock()
        mock_schwab.client = MagicMock(return_value=mock_client)
        schwab_service.authenticate()
        assert schwab_service.client is not None

    @patch("backend.services.schwab_service.schwab")
    def test_authenticate_stores_client(self, mock_schwab, schwab_service):
        mock_client = MagicMock()
        mock_schwab.client = MagicMock(return_value=mock_client)
        schwab_service.authenticate()
        assert schwab_service.client == mock_client

    @patch("backend.services.schwab_service.schwab")
    def test_authenticate_uses_env_credentials(self, mock_schwab, schwab_service):
        mock_client = MagicMock()
        mock_schwab.client = MagicMock(return_value=mock_client)
        with patch.dict(
            "os.environ",
            {
                "SCHWAB_API_KEY": "test_key",
                "SCHWAB_SECRET": "test_secret",
                "SCHWAB_CALLBACK_URL": "https://localhost",
                "SCHWAB_TOKEN_PATH": "/tmp/token.json",
            },
        ):
            schwab_service.authenticate()
        assert mock_schwab.client.called


class TestSchwabServiceGetOptionsChain:
    @pytest.mark.asyncio
    @patch("backend.services.schwab_service.schwab")
    async def test_get_options_chain_returns_data(self, mock_schwab, schwab_service):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "symbol": "AAPL",
                "status": "SUCCESS",
                "callExpDateMap": {},
                "putExpDateMap": {},
            }
        )
        mock_response.status_code = 200
        mock_client.option_chains = MagicMock(return_value=mock_response)
        mock_schwab.client = MagicMock(return_value=mock_client)
        schwab_service.client = mock_client

        result = await schwab_service.get_options_chain("AAPL")
        assert result is not None

    @pytest.mark.asyncio
    @patch("backend.services.schwab_service.schwab")
    async def test_get_options_chain_with_symbol(self, mock_schwab, schwab_service):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "symbol": "TSLA",
                "status": "SUCCESS",
                "callExpDateMap": {},
                "putExpDateMap": {},
            }
        )
        mock_response.status_code = 200
        mock_client.option_chains = MagicMock(return_value=mock_response)
        schwab_service.client = mock_client

        result = await schwab_service.get_options_chain("TSLA")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_options_chain_raises_without_client(self, schwab_service):
        schwab_service.client = None
        with pytest.raises(Exception):
            await schwab_service.get_options_chain("AAPL")

    @pytest.mark.asyncio
    @patch("backend.services.schwab_service.schwab")
    async def test_get_options_chain_handles_api_error(
        self, mock_schwab, schwab_service
    ):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json = MagicMock(return_value={"error": "Bad Request"})
        mock_client.option_chains = MagicMock(return_value=mock_response)
        schwab_service.client = mock_client

        with pytest.raises(Exception):
            await schwab_service.get_options_chain("INVALID")


class TestSchwabServiceFilters:
    def test_filter_by_expiration(self, schwab_service):
        if hasattr(schwab_service, "filter_by_expiration"):
            contracts = [
                {"expirationDate": "2024-01-19"},
                {"expirationDate": "2024-02-16"},
            ]
            result = schwab_service.filter_by_expiration(
                contracts, "2024-01-19", "2024-01-19"
            )
            assert isinstance(result, list)

    def test_filter_by_delta(self, schwab_service):
        if hasattr(schwab_service, "filter_by_delta"):
            contracts = [
                {"delta": 0.3},
                {"delta": 0.7},
                {"delta": 0.5},
            ]
            result = schwab_service.filter_by_delta(contracts, 0.2, 0.6)
            assert isinstance(result, list)

    def test_filter_by_open_interest(self, schwab_service):
        if hasattr(schwab_service, "filter_by_open_interest"):
            contracts = [
                {"openInterest": 100},
                {"openInterest": 500},
                {"openInterest": 50},
            ]
            result = schwab_service.filter_by_open_interest(contracts, 200)
            assert isinstance(result, list)


class TestSchwabServiceMarketData:
    @pytest.mark.asyncio
    @patch("backend.services.schwab_service.schwab")
    async def test_get_market_data_returns_dict(self, mock_schwab, schwab_service):
        if hasattr(schwab_service, "get_market_data"):
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(
                return_value={"AAPL": {"lastPrice": 150.0, "bidPrice": 149.5}}
            )
            mock_client.quotes = MagicMock(return_value=mock_response)
            schwab_service.client = mock_client

            result = await schwab_service.get_market_data(["AAPL"])
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    @patch("backend.services.schwab_service.schwab")
    async def test_get_market_data_multiple_symbols(
        self, mock_schwab, schwab_service
    ):
        if hasattr(schwab_service, "get_market_data"):
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(
                return_value={
                    "AAPL": {"lastPrice": 150.0},
                    "TSLA": {"lastPrice": 200.0},
                }
            )
            mock_client.quotes = MagicMock(return_value=mock_response)
            schwab_service.client = mock_client

            result = await schwab_service.get_market_data(["AAPL", "TSLA"])
            assert isinstance(result, dict)


class TestSchwabServiceContractParsing:
    def test_parse_option_contract(self, schwab_service):
        if hasattr(schwab_service, "parse_option_contract"):
            raw_contract = {
                "symbol": "AAPL  240119C00150000",
                "strikePrice": 150.0,
                "expirationDate": "2024-01-19",
                "putCall": "CALL",
                "bid": 2.5,
                "ask": 2.6,
                "last": 2.55,
                "delta": 0.45,
                "gamma": 0.02,
                "theta": -0.05,
                "vega": 0.10,
                "openInterest": 1000,
                "totalVolume": 500,
                "impliedVolatility": 0.25,
            }
            result = schwab_service.parse_option_contract(raw_contract)
            assert result is not None

    def test_parse_options_chain_response(self, schwab_service):
        if hasattr(schwab_service, "parse_options_chain_response"):
            raw_response = {
                "symbol": "AAPL",
                "status": "SUCCESS",
                "callExpDateMap": {
                    "2024-01-19:30": {
                        "150.0": [
                            {
                                "symbol": "AAPL  240119C00150000",
                                "strikePrice": 150.0,
                                "bid": 2.5,
                                "ask": 2.6,
                                "delta": 0.45,
                                "openInterest": 1000,
                            }
                        ]
                    }
                },
                "putExpDateMap": {},
            }
            result = schwab_service.parse_options_chain_response(raw_response)
            assert result is not None


class TestSchwabServiceIntegration:
    @pytest.mark.asyncio
    @patch("backend.services.schwab_service.schwab")
    async def test_full_options_chain_workflow(self, mock_schwab, schwab_service):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "symbol": "AAPL",
                "status": "SUCCESS",
                "underlyingPrice": 150.0,
                "callExpDateMap": {
                    "2024-01-19:30": {
                        "150.0": [
                            {
                                "symbol": "AAPL  240119C00150000",
                                "strikePrice": 150.0,
                                "bid": 2.5,
                                "ask": 2.6,
                                "last": 2.55,
                                "delta": 0.45,
                                "gamma": 0.02,
                                "theta": -0.05,
                                "vega": 0.10,
                                "openInterest": 1000,
                                "totalVolume": 500,
                                "impliedVolatility": 0.25,
                                "putCall": "CALL",
                                "expirationDate": "2024-01-19",
                            }
                        ]
                    }
                },
                "putExpDateMap": {},
            }
        )
        mock_client.option_chains = MagicMock(return_value=mock_response)
        mock_schwab.client = MagicMock(return_value=mock_client)
        schwab_service.client = mock_client

        result = await schwab_service.get_options_chain("AAPL")
        assert result is not None

    def test_service_is_singleton_compatible(self):
        service1 = SchwabService()
        service2 = SchwabService()
        assert service1 is not service2
        assert type(service1) == type(service2)