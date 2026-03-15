from backend.agents.state import PipelineState
from backend.services.trades_comparison_service import TradesComparisonService

__all__ = ["TradabilityAgent"]


class TradabilityAgent:
    """
    Agent for assessing overall tradability of a given ticker.

    Delegates to TradesComparisonService.compute_tradability_score and
    writes ``tradability_score`` into the pipeline state.
    """

    def __init__(self) -> None:
        self._service = TradesComparisonService()

    def run(self, state: PipelineState) -> PipelineState:
        """
        Execute the tradability assessment step.

        Returns a new state dict with ``tradability_score`` populated.
        The original *state* dict is not mutated.
        """
        result = dict(state)
        trades = state.get("trades") or []
        try:
            score = self._service.compute_tradability_score(trades)
        except Exception:  # noqa: BLE001
            score = None
        result["tradability_score"] = score
        return result

    def __call__(self, state: PipelineState) -> PipelineState:
        """Allow the agent to be used directly as a LangGraph node callable."""
        return self.run(state)
