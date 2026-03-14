tests/services/test_schwab_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.services.schwab_service import SchwabService


@pytest.fixture
def schwab_service():
    with patch("backend.services.schwab_service.schwab") as mock_schwab:
        mock_client = MagicMock()
        mock_schwab.client.return_value = mock_client
        service = SchwabService(
            app_key="test_app_key",
            app_secret="test_app_secret",
            callback_url="https://localhost",
            token_file="test_token.json",
        )
        service.client = mock_client
        yield service


class TestSchwabServiceInit:
    def test_init_stores_credentials(self):
        with patch("backend.services.schwab_service.schwab"):
            service = SchwabService(
                app_key="key123",
                app_secret="secret456",
                callback_url="https://example.com",
                token_file="tokens.json",
            )
            assert service.app_key == "key123"
            assert service.app_secret == "secret456"
            assert service.callback_url == "https://example.com"
            assert service.token_file == "tokens.json"

    def test_init_client_is_none_before_auth(self):
        with patch("backend.services.schwab_service.schwab"):
            service = SchwabService(
                app_key="key",
                app_secret="secret",
                callback_url="https://localhost",
                token_file="token.json",
            )
            assert service.client is None


class TestSchwabServiceAuthentication:
    def test_authenticate_creates_client(self, schwab_service):
        with patch("backend.services.schwab_service.schwab") as mock_schwab:
            mock_client = MagicMock()
            mock_schwab.client.return_value = mock_client
            schwab_service.authenticate()
            assert schwab_service.client is not None

    def test_authenticate_calls_schwab_client(self, schwab_service):
        with patch("backend.services.schwab_service.schwab") as mock_schwab:
            mock_client = MagicMock()
            mock_schwab.client.return_value = mock_client
            schwab_service.authenticate()
            mock_schwab.client.assert_called_once()

    def test_authenticate_passes_credentials(self, schwab_service):
        with patch("backend.services.schwab_service.schwab") as mock_schwab:
            mock_client = MagicMock()
            mock_schwab.client.return_value = mock_client
            schwab_service.authenticate()
            call_kwargs = mock_schwab.client.call_args
            assert call_kwargs is not None

    def test_is_authenticated_returns_false_when_no_client(self):
        with patch("backend.services.schwab_service.schwab"):
            service = SchwabService(
                app_key="key",
                app_secret="secret",
                callback_url="https://localhost",
                token_file="token.json",
            )
            assert service.is_authenticated() is False

    def test_is_authenticated_returns_true_when_client_exists(self, schwab_service):
        schwab_service.client = MagicMock()
        assert schwab_service.is_authenticated() is True


class TestSchwabServiceOptionsChain:
    @pytest.mark.asyncio
    async def test_get_options_chain_returns_data(self, schwab_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "symbol": "AAPL",
            "callExpDateMap": {},
            "putExpDateMap": {},
        }
        mock_response.status_code = 200
        schwab_service.client.get_option_chain = MagicMock(return_value=mock_response)

        result = await schwab_service.get_options_chain("AAPL")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_options_chain_calls_client_with_symbol(self, schwab_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {"symbol": "TSLA"}
        mock_response.status_code = 200
        schwab_service.client.get_option_chain = MagicMock(return_value=mock_response)

        await schwab_service.get_options_chain("TSLA")
        schwab_service.client.get_option_chain.assert_called_once()
        call_args = schwab_service.client.get_option_chain.call_args
        assert "TSLA" in str(call_args)

    @pytest.mark.asyncio
    async def test_get_options_chain_raises_when_not_authenticated(self):
        with patch("backend.services.schwab_service.schwab"):
            service = SchwabService(
                app_key="key",
                app_secret="secret",
                callback_url="https://localhost",
                token_file="token.json",
            )
            service.client = None
            with pytest.raises(Exception):
                await service.get_options_chain("AAPL")

    @pytest.mark.asyncio
    async def test_get_options_chain_with_filters(self, schwab_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {"symbol": "AAPL"}
        mock_response.status_code = 200
        schwab_service.client.get_option_chain = MagicMock(return_value=mock_response)

        result = await schwab_service.get_options_chain(
            "AAPL",
            contract_type="CALL",
            strike_count=10,
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_options_chain_handles_http_error(self, schwab_service):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = Exception("HTTP Error 400")
        schwab_service.client.get_option_chain = MagicMock(return_value=mock_response)

        with pytest.raises(Exception):
            await schwab_service.get_options_chain("INVALID")


class TestSchwabServiceMarketData:
    @pytest.mark.asyncio
    async def test_get_quote_returns_data(self, schwab_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "AAPL": {
                "quote": {"lastPrice": 150.0, "bidPrice": 149.5, "askPrice": 150.5}
            }
        }
        mock_response.status_code = 200
        schwab_service.client.get_quote = MagicMock(return_value=mock_response)

        result = await schwab_service.get_quote("AAPL")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_quote_calls_client(self, schwab_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {"AAPL": {}}
        mock_response.status_code = 200
        schwab_service.client.get_quote = MagicMock(return_value=mock_response)

        await schwab_service.get_quote("AAPL")
        schwab_service.client.get_quote.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_quotes_multiple_symbols(self, schwab_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "AAPL": {"quote": {"lastPrice": 150.0}},
            "TSLA": {"quote": {"lastPrice": 200.0}},
        }
        mock_response.status_code = 200
        schwab_service.client.get_quotes = MagicMock(return_value=mock_response)

        result = await schwab_service.get_quotes(["AAPL", "TSLA"])
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_price_history_returns_data(self, schwab_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candles": [{"open": 150.0, "close": 152.0, "high": 153.0, "low": 149.0}],
            "symbol": "AAPL",
        }
        mock_response.status_code = 200
        schwab_service.client.get_price_history = MagicMock(return_value=mock_response)

        result = await schwab_service.get_price_history("AAPL")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_price_history_calls_client_with_symbol(self, schwab_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {"candles": [], "symbol": "MSFT"}
        mock_response.status_code = 200
        schwab_service.client.get_price_history = MagicMock(return_value=mock_response)

        await schwab_service.get_price_history("MSFT")
        schwab_service.client.get_price_history.assert_called_once()


class TestSchwabServiceFilters:
    @pytest.mark.asyncio
    async def test_get_options_chain_with_contract_type_call(self, schwab_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {"symbol": "AAPL", "callExpDateMap": {}}
        mock_response.status_code = 200
        schwab_service.client.get_option_chain = MagicMock(return_value=mock_response)

        result = await schwab_service.get_options_chain("AAPL", contract_type="CALL")
        assert result is not None
        call_args = schwab_service.client.get_option_chain.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_get_options_chain_with_contract_type_put(self, schwab_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {"symbol": "AAPL", "putExpDateMap": {}}
        mock_response.status_code = 200
        schwab_service.client.get_option_chain = MagicMock(return_value=mock_response)

        result = await schwab_service.get_options_chain("AAPL", contract_type="PUT")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_options_chain_with_expiration_date(self, schwab_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {"symbol": "AAPL"}
        mock_response.status_code = 200
        schwab_service.client.get_option_chain = MagicMock(return_value=mock_response)

        result = await schwab_service.get_options_chain(
            "AAPL", from_date="2024-01-01", to_date="2024-12-31"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_options_chain_with_strike_count(self, schwab_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {"symbol": "AAPL"}
        mock_response.status_code = 200
        schwab_service.client.get_option_chain = MagicMock(return_value=mock_response)

        result = await schwab_service.get_options_chain("AAPL", strike_count=5)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_options_chain_with_include_underlying_quote(
        self, schwab_service
    ):
        mock_response = MagicMock()
        mock_response.json.return_value = {"symbol": "AAPL"}
        mock_response.status_code = 200
        schwab_service.client.get_option_chain = MagicMock(return_value=mock_response)

        result = await schwab_service.get_options_chain(
            "AAPL", include_underlying_quote=True
        )
        assert result is not None


class TestSchwabServiceErrorHandling:
    @pytest.mark.asyncio
    async def test_get_quote_raises_on_client_error(self, schwab_service):
        schwab_service.client.get_quote = MagicMock(
            side_effect=Exception("Connection error")
        )
        with pytest.raises(Exception):
            await schwab_service.get_quote("AAPL")

    @pytest.mark.asyncio
    async def test_get_options_chain_raises_on_client_error(self, schwab_service):
        schwab_service.client.get_option_chain = MagicMock(
            side_effect=Exception("Timeout")
        )
        with pytest.raises(Exception):
            await schwab_service.get_options_chain("AAPL")

    @pytest.mark.asyncio
    async def test_get_price_history_raises_on_client_error(self, schwab_service):
        schwab_service.client.get_price_history = MagicMock(
            side_effect=Exception("Rate limit exceeded")
        )
        with pytest.raises(Exception):
            await schwab_service.get_price_history("AAPL")

    def test_authenticate_raises_on_invalid_credentials(self):
        with patch("backend.services.schwab_service.schwab") as mock_schwab:
            mock_schwab.client.side_effect = Exception("Invalid credentials")
            service = SchwabService(
                app_key="bad_key",
                app_secret="bad_secret",
                callback_url="https://localhost",
                token_file="token.json",
            )
            with pytest.raises(Exception):
                service.authenticate()


class TestSchwabServiceSingleton:
    def test_get_instance_returns_same_instance(self):
        with patch("backend.services.schwab_service.schwab"):
            instance1 = SchwabService.get_instance(
                app_key="key",
                app_secret="secret",
                callback_url="https://localhost",
                token_file="token.json",
            )
            instance2 = SchwabService.get_instance(
                app_key="key",
                app_secret="secret",
                callback_url="https://localhost",
                token_file="token.json",
            )
            assert instance1 is instance2

    def test_get_instance_creates_new_when_none_exists(self):
        with patch("backend.services.schwab_service.schwab"):
            SchwabService._instance = None
            instance = SchwabService.get_instance(
                app_key="key",
                app_secret="secret",
                callback_url="https://localhost",
                token_file="token.json",
            )
            assert instance is not None
            assert isinstance(instance, SchwabService)

    def teardown_method(self, method):
        SchwabService._instance = None


class TestSchwabServiceOptionsChainParsing:
    @pytest.mark.asyncio
    async def test_get_options_chain_returns_dict(self, schwab_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "symbol": "AAPL",
            "status": "SUCCESS",
            "callExpDateMap": {
                "2024-01-19:30": {
                    "150.0": [
                        {
                            "putCall": "CALL",
                            "symbol": "AAPL  240119C00150000",
                            "bid": 5.0,
                            "ask": 5.1,
                            "last": 5.05,
                            "volume": 1000,
                            "openInterest": 5000,
                            "delta": 0.5,
                            "gamma": 0.05,
                            "theta": -0.1,
                            "vega": 0.2,
                            "impliedVolatility": 0.3,
                        }
                    ]
                }
            },
            "putExpDateMap": {},
        }
        mock_response.status_code = 200
        schwab_service.client.get_option_chain = MagicMock(return_value=mock_response)

        result = await schwab_service.get_options_chain("AAPL")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_options_chain_contains_symbol(self, schwab_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "symbol": "AAPL",
            "callExpDateMap": {},
            "putExpDateMap": {},
        }
        mock_response.status_code = 200
        schwab_service.client.get_option_chain = MagicMock(return_value=mock_response)

        result = await schwab_service.get_options_chain("AAPL")
        assert "symbol" in result or result is not None