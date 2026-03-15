from backend.agents.state import PipelineState
from backend.services.trades_comparison_service import TradesComparisonService

__all__ = ["OptionsDataAgent"]


class OptionsDataAgent:
    """Agent responsible for fetching and processing options market data."""

    def run(self, state: PipelineState) -> PipelineState:
        """Execute the options data retrieval step."""
        options_data = state.get("options_data")

        if options_data:
            state["options_data"] = TradesComparisonService.enrich_put_options_with_roi(options_data)

        return state

    def __call__(self, state: PipelineState) -> PipelineState:
        """Allow the agent instance to be used directly as a LangGraph node."""
        return self.run(state)
