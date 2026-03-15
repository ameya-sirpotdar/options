"""
Tests for model imports and structure validation.
Ensures all models are importable and have the expected fields/structure.
"""

import pytest
from pydantic import ValidationError


class TestOptionsContractImport:
    """Tests for OptionsContract model import and structure."""

    def test_import_options_contract(self):
        """Test that OptionsContract can be imported."""
        from backend.models.options_contract import OptionsContract
        assert OptionsContract is not None

    def test_options_contract_is_pydantic_model(self):
        """Test that OptionsContract is a Pydantic BaseModel."""
        from pydantic import BaseModel
        from backend.models.options_contract import OptionsContract
        assert issubclass(OptionsContract, BaseModel)

    def test_options_contract_required_fields(self):
        """Test that OptionsContract has expected fields."""
        from backend.models.options_contract import OptionsContract
        fields = OptionsContract.model_fields
        assert "symbol" in fields
        assert "strike" in fields
        assert "expiration" in fields
        assert "option_type" in fields

    def test_options_contract_instantiation(self):
        """Test that OptionsContract can be instantiated with valid data."""
        from backend.models.options_contract import OptionsContract
        contract = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-01-19",
            option_type="call",
        )
        assert contract.symbol == "AAPL"
        assert contract.strike == 150.0
        assert contract.expiration == "2024-01-19"
        assert contract.option_type == "call"

    def test_options_contract_optional_fields(self):
        """Test that OptionsContract optional fields default correctly."""
        from backend.models.options_contract import OptionsContract
        contract = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-01-19",
            option_type="call",
        )
        # Optional fields should be None or have defaults
        assert hasattr(contract, "bid")
        assert hasattr(contract, "ask")
        assert hasattr(contract, "volume")
        assert hasattr(contract, "open_interest")
        assert hasattr(contract, "implied_volatility")
        assert hasattr(contract, "delta")
        assert hasattr(contract, "gamma")
        assert hasattr(contract, "theta")
        assert hasattr(contract, "vega")

    def test_options_contract_with_all_fields(self):
        """Test OptionsContract instantiation with all fields."""
        from backend.models.options_contract import OptionsContract
        contract = OptionsContract(
            symbol="TSLA",
            strike=200.0,
            expiration="2024-02-16",
            option_type="put",
            bid=1.50,
            ask=1.75,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.45,
            delta=-0.35,
            gamma=0.02,
            theta=-0.05,
            vega=0.10,
        )
        assert contract.symbol == "TSLA"
        assert contract.strike == 200.0
        assert contract.option_type == "put"
        assert contract.bid == 1.50
        assert contract.ask == 1.75
        assert contract.volume == 1000
        assert contract.open_interest == 5000
        assert contract.implied_volatility == 0.45
        assert contract.delta == -0.35

    def test_options_contract_invalid_option_type(self):
        """Test that OptionsContract raises error for invalid option_type."""
        from backend.models.options_contract import OptionsContract
        with pytest.raises((ValidationError, ValueError)):
            OptionsContract(
                symbol="AAPL",
                strike=150.0,
                expiration="2024-01-19",
                option_type="invalid_type",
            )


class TestOptionsChainRequestImport:
    """Tests for OptionsChainRequest model import and structure."""

    def test_import_options_chain_request(self):
        """Test that OptionsChainRequest can be imported."""
        from backend.models.options_chain_request import OptionsChainRequest
        assert OptionsChainRequest is not None

    def test_options_chain_request_is_pydantic_model(self):
        """Test that OptionsChainRequest is a Pydantic BaseModel."""
        from pydantic import BaseModel
        from backend.models.options_chain_request import OptionsChainRequest
        assert issubclass(OptionsChainRequest, BaseModel)

    def test_options_chain_request_required_fields(self):
        """Test that OptionsChainRequest has expected fields."""
        from backend.models.options_chain_request import OptionsChainRequest
        fields = OptionsChainRequest.model_fields
        assert "symbol" in fields

    def test_options_chain_request_instantiation(self):
        """Test that OptionsChainRequest can be instantiated with valid data."""
        from backend.models.options_chain_request import OptionsChainRequest
        request = OptionsChainRequest(symbol="AAPL")
        assert request.symbol == "AAPL"

    def test_options_chain_request_optional_fields(self):
        """Test that OptionsChainRequest has optional fields with defaults."""
        from backend.models.options_chain_request import OptionsChainRequest
        request = OptionsChainRequest(symbol="AAPL")
        assert hasattr(request, "contract_type")
        assert hasattr(request, "strike_count")
        assert hasattr(request, "include_underlying_quote")

    def test_options_chain_request_with_all_fields(self):
        """Test OptionsChainRequest instantiation with all fields."""
        from backend.models.options_chain_request import OptionsChainRequest
        request = OptionsChainRequest(
            symbol="AAPL",
            contract_type="CALL",
            strike_count=10,
            include_underlying_quote=True,
        )
        assert request.symbol == "AAPL"
        assert request.contract_type == "CALL"
        assert request.strike_count == 10
        assert request.include_underlying_quote is True

    def test_options_chain_request_missing_symbol(self):
        """Test that OptionsChainRequest raises error when symbol is missing."""
        from backend.models.options_chain_request import OptionsChainRequest
        with pytest.raises(ValidationError):
            OptionsChainRequest()


class TestOptionsChainResponseImport:
    """Tests for OptionsChainResponse model import and structure."""

    def test_import_options_chain_response(self):
        """Test that OptionsChainResponse can be imported."""
        from backend.models.options_chain_response import OptionsChainResponse
        assert OptionsChainResponse is not None

    def test_options_chain_response_is_pydantic_model(self):
        """Test that OptionsChainResponse is a Pydantic BaseModel."""
        from pydantic import BaseModel
        from backend.models.options_chain_response import OptionsChainResponse
        assert issubclass(OptionsChainResponse, BaseModel)

    def test_options_chain_response_required_fields(self):
        """Test that OptionsChainResponse has expected fields."""
        from backend.models.options_chain_response import OptionsChainResponse
        fields = OptionsChainResponse.model_fields
        assert "symbol" in fields
        assert "contracts" in fields

    def test_options_chain_response_instantiation(self):
        """Test that OptionsChainResponse can be instantiated with valid data."""
        from backend.models.options_chain_response import OptionsChainResponse
        response = OptionsChainResponse(symbol="AAPL", contracts=[])
        assert response.symbol == "AAPL"
        assert response.contracts == []

    def test_options_chain_response_with_contracts(self):
        """Test OptionsChainResponse with a list of contracts."""
        from backend.models.options_chain_response import OptionsChainResponse
        from backend.models.options_contract import OptionsContract
        contract = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-01-19",
            option_type="call",
        )
        response = OptionsChainResponse(symbol="AAPL", contracts=[contract])
        assert len(response.contracts) == 1
        assert response.contracts[0].symbol == "AAPL"

    def test_options_chain_response_optional_fields(self):
        """Test that OptionsChainResponse has optional fields."""
        from backend.models.options_chain_response import OptionsChainResponse
        response = OptionsChainResponse(symbol="AAPL", contracts=[])
        assert hasattr(response, "underlying_price")
        assert hasattr(response, "status")


class TestTradabilityScoreImport:
    """Tests for TradabilityScore model import and structure."""

    def test_import_tradability_score(self):
        """Test that TradabilityScore can be imported."""
        from backend.models.tradability_score import TradabilityScore
        assert TradabilityScore is not None

    def test_tradability_score_is_pydantic_model(self):
        """Test that TradabilityScore is a Pydantic BaseModel."""
        from pydantic import BaseModel
        from backend.models.tradability_score import TradabilityScore
        assert issubclass(TradabilityScore, BaseModel)

    def test_tradability_score_required_fields(self):
        """Test that TradabilityScore has expected fields."""
        from backend.models.tradability_score import TradabilityScore
        fields = TradabilityScore.model_fields
        assert "symbol" in fields
        assert "score" in fields

    def test_tradability_score_instantiation(self):
        """Test that TradabilityScore can be instantiated with valid data."""
        from backend.models.tradability_score import TradabilityScore
        score = TradabilityScore(symbol="AAPL", score=0.85)
        assert score.symbol == "AAPL"
        assert score.score == 0.85

    def test_tradability_score_range_validation(self):
        """Test that TradabilityScore validates score range."""
        from backend.models.tradability_score import TradabilityScore
        # Valid scores
        score_min = TradabilityScore(symbol="AAPL", score=0.0)
        score_max = TradabilityScore(symbol="AAPL", score=1.0)
        assert score_min.score == 0.0
        assert score_max.score == 1.0
        # Invalid scores outside [0.0, 1.0] should raise a validation error
        with pytest.raises((ValidationError, ValueError)):
            TradabilityScore(symbol="AAPL", score=-0.1)
        with pytest.raises((ValidationError, ValueError)):
            TradabilityScore(symbol="AAPL", score=1.1)

    def test_tradability_score_optional_fields(self):
        """Test that TradabilityScore has optional fields."""
        from backend.models.tradability_score import TradabilityScore
        score = TradabilityScore(symbol="AAPL", score=0.75)
        assert hasattr(score, "contract")
        assert hasattr(score, "reasoning")

    def test_tradability_score_with_contract(self):
        """Test TradabilityScore with an associated contract."""
        from backend.models.tradability_score import TradabilityScore
        from backend.models.options_contract import OptionsContract
        contract = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-01-19",
            option_type="call",
        )
        score = TradabilityScore(
            symbol="AAPL",
            score=0.90,
            contract=contract,
            reasoning="High volume and favorable IV",
        )
        assert score.score == 0.90
        assert score.contract is not None
        assert score.contract.symbol == "AAPL"
        assert score.reasoning == "High volume and favorable IV"


class TestTradabilityMetricsImport:
    """Tests for TradabilityMetrics model import and structure."""

    def test_import_tradability_metrics(self):
        """Test that TradabilityMetrics can be imported."""
        from backend.models.tradability_metrics import TradabilityMetrics
        assert TradabilityMetrics is not None

    def test_tradability_metrics_is_pydantic_model(self):
        """Test that TradabilityMetrics is a Pydantic BaseModel."""
        from pydantic import BaseModel
        from backend.models.tradability_metrics import TradabilityMetrics
        assert issubclass(TradabilityMetrics, BaseModel)

    def test_tradability_metrics_required_fields(self):
        """Test that TradabilityMetrics has expected fields."""
        from backend.models.tradability_metrics import TradabilityMetrics
        fields = TradabilityMetrics.model_fields
        assert "symbol" in fields

    def test_tradability_metrics_instantiation(self):
        """Test that TradabilityMetrics can be instantiated with valid data."""
        from backend.models.tradability_metrics import TradabilityMetrics
        metrics = TradabilityMetrics(symbol="AAPL")
        assert metrics.symbol == "AAPL"

    def test_tradability_metrics_optional_fields(self):
        """Test that TradabilityMetrics has optional metric fields."""
        from backend.models.tradability_metrics import TradabilityMetrics
        metrics = TradabilityMetrics(symbol="AAPL")
        assert hasattr(metrics, "liquidity_score")
        assert hasattr(metrics, "volatility_score")
        assert hasattr(metrics, "momentum_score")
        assert hasattr(metrics, "overall_score")

    def test_tradability_metrics_with_all_fields(self):
        """Test TradabilityMetrics instantiation with all metric fields."""
        from backend.models.tradability_metrics import TradabilityMetrics
        metrics = TradabilityMetrics(
            symbol="AAPL",
            liquidity_score=0.80,
            volatility_score=0.70,
            momentum_score=0.65,
            overall_score=0.72,
        )
        assert metrics.symbol == "AAPL"
        assert metrics.liquidity_score == 0.80
        assert metrics.volatility_score == 0.70
        assert metrics.momentum_score == 0.65
        assert metrics.overall_score == 0.72


class TestModelsInitImport:
    """Tests for the models __init__.py package exports."""

    def test_import_models_package(self):
        """Test that the models package can be imported."""
        import backend.models
        assert backend.models is not None

    def test_models_init_exports_options_contract(self):
        """Test that models __init__ exports OptionsContract."""
        from backend.models import OptionsContract
        assert OptionsContract is not None

    def test_models_init_exports_options_chain_request(self):
        """Test that models __init__ exports OptionsChainRequest."""
        from backend.models import OptionsChainRequest
        assert OptionsChainRequest is not None

    def test_models_init_exports_options_chain_response(self):
        """Test that models __init__ exports OptionsChainResponse."""
        from backend.models import OptionsChainResponse
        assert OptionsChainResponse is not None

    def test_models_init_exports_tradability_score(self):
        """Test that models __init__ exports TradabilityScore."""
        from backend.models import TradabilityScore
        assert TradabilityScore is not None

    def test_models_init_exports_tradability_metrics(self):
        """Test that models __init__ exports TradabilityMetrics."""
        from backend.models import TradabilityMetrics
        assert TradabilityMetrics is not None

    def test_models_are_distinct_classes(self):
        """Test that all exported models are distinct classes."""
        from backend.models import (
            OptionsContract,
            OptionsChainRequest,
            OptionsChainResponse,
            TradabilityScore,
            TradabilityMetrics,
        )
        models = [
            OptionsContract,
            OptionsChainRequest,
            OptionsChainResponse,
            TradabilityScore,
            TradabilityMetrics,
        ]
        # Ensure all are unique
        assert len(set(models)) == len(models)


class TestModelFileStructure:
    """Tests to verify one-model-per-file layout."""

    def test_options_contract_module_path(self):
        """Test that OptionsContract lives in its own module."""
        from backend.models.options_contract import OptionsContract
        assert OptionsContract.__module__ == "backend.models.options_contract"

    def test_options_chain_request_module_path(self):
        """Test that OptionsChainRequest lives in its own module."""
        from backend.models.options_chain_request import OptionsChainRequest
        assert OptionsChainRequest.__module__ == "backend.models.options_chain_request"

    def test_options_chain_response_module_path(self):
        """Test that OptionsChainResponse lives in its own module."""
        from backend.models.options_chain_response import OptionsChainResponse
        assert OptionsChainResponse.__module__ == "backend.models.options_chain_response"

    def test_tradability_score_module_path(self):
        """Test that TradabilityScore lives in its own module."""
        from backend.models.tradability_score import TradabilityScore
        assert TradabilityScore.__module__ == "backend.models.tradability_score"

    def test_tradability_metrics_module_path(self):
        """Test that TradabilityMetrics lives in its own module."""
        from backend.models.tradability_metrics import TradabilityMetrics
        assert TradabilityMetrics.__module__ == "backend.models.tradability_metrics"


class TestModelSerialization:
    """Tests for model serialization and deserialization."""

    def test_options_contract_to_dict(self):
        """Test that OptionsContract can be serialized to dict."""
        from backend.models.options_contract import OptionsContract
        contract = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-01-19",
            option_type="call",
        )
        data = contract.model_dump()
        assert isinstance(data, dict)
        assert data["symbol"] == "AAPL"
        assert data["strike"] == 150.0

    def test_options_contract_to_json(self):
        """Test that OptionsContract can be serialized to JSON."""
        from backend.models.options_contract import OptionsContract
        contract = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-01-19",
            option_type="call",
        )
        json_str = contract.model_dump_json()
        assert isinstance(json_str, str)
        assert "AAPL" in json_str

    def test_options_contract_from_dict(self):
        """Test that OptionsContract can be deserialized from dict."""
        from backend.models.options_contract import OptionsContract
        data = {
            "symbol": "AAPL",
            "strike": 150.0,
            "expiration": "2024-01-19",
            "option_type": "call",
        }
        contract = OptionsContract.model_validate(data)
        assert contract.symbol == "AAPL"
        assert contract.strike == 150.0

    def test_tradability_score_to_dict(self):
        """Test that TradabilityScore can be serialized to dict."""
        from backend.models.tradability_score import TradabilityScore
        score = TradabilityScore(symbol="AAPL", score=0.85)
        data = score.model_dump()
        assert isinstance(data, dict)
        assert data["symbol"] == "AAPL"
        assert data["score"] == 0.85

    def test_tradability_metrics_to_dict(self):
        """Test that TradabilityMetrics can be serialized to dict."""
        from backend.models.tradability_metrics import TradabilityMetrics
        metrics = TradabilityMetrics(
            symbol="AAPL",
            liquidity_score=0.80,
            overall_score=0.75,
        )
        data = metrics.model_dump()
        assert isinstance(data, dict)
        assert data["symbol"] == "AAPL"
        assert data["liquidity_score"] == 0.80

    def test_options_chain_response_nested_serialization(self):
        """Test that OptionsChainResponse serializes nested contracts."""
        from backend.models.options_chain_response import OptionsChainResponse
        from backend.models.options_contract import OptionsContract
        contract = OptionsContract(
            symbol="AAPL",
            strike=150.0,
            expiration="2024-01-19",
            option_type="call",
        )
        response = OptionsChainResponse(symbol="AAPL", contracts=[contract])
        data = response.model_dump()
        assert isinstance(data, dict)
        assert len(data["contracts"]) == 1
        assert data["contracts"][0]["symbol"] == "AAPL"
