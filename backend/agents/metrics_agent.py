from backend.agents.state import PipelineState
from backend.services.trades_comparison_service import TradesComparisonService

__all__ = ["MetricsAgent"]


class MetricsAgent:
    """Agent responsible for computing financial and options metrics.

    Delegates tradability scoring and CCP calculation to
    :class:`~backend.services.trades_comparison_service.TradesComparisonService`.
    Greeks, implied-volatility surfaces, and historical volatility are
    planned for a future iteration.
    """

    def __init__(self) -> None:
        self._service = TradesComparisonService()

    def run(self, state: PipelineState) -> PipelineState:
        """Execute the metrics computation step.

        Parameters
        ----------
        state:
            The current pipeline state passed in from the preceding node.

        Returns
        -------
        PipelineState
            The updated state dict.  ``metrics`` is populated with the
            tradability scores returned by
            :class:`~backend.services.trades_comparison_service.TradesComparisonService`
            when options data is present, otherwise it is set to ``None``.
        """
        options_data = state.get("options_data")
        if options_data:
            try:
                state["metrics"] = self._service.score_trades(options_data)
            except Exception:  # noqa: BLE001
                state["metrics"] = None
        else:
            # TODO: implement Greeks, IV surface, and historical volatility.
            state["metrics"] = None
        return state

    def __call__(self, state: PipelineState) -> PipelineState:
        """Allow the agent instance to be used directly as a LangGraph node."""
        return self.run(state)