from backend.agents.state import PipelineState
from backend.services.trades_comparison_service import TradesComparisonService

__all__ = ["TradabilityAgent"]


class TradabilityAgent:
    """
    Placeholder agent for assessing overall tradability of a given ticker.

    Intended role in the pipeline:
        Receives aggregated sentiment scores, options data, and computed
        metrics from upstream agents and synthesises them into a final
        tradability score and a human-readable recommendation (e.g.
        "strong buy", "hold", "avoid").  In the full implementation this
        node will apply a weighted scoring model and optional LLM
        reasoning before writing `tradability_score` and `recommendation`
        back into the shared LangGraph state.

    Current status:
        Stub — the `run` method returns the state dict unchanged so that
        the rest of the graph can be wired up and tested end-to-end before
        the scoring logic is implemented.
    """

    def run(self, state: PipelineState) -> PipelineState:
        """
        Execute the tradability assessment step.

        Parameters
        ----------
        state:
            The current LangGraph shared state dictionary.

        Returns
        -------
        PipelineState
            The state dictionary, returned unchanged by this stub.
        """
        # TODO: implement weighted scoring model and set state['tradability_score']
        return state

    def __call__(self, state: PipelineState) -> PipelineState:
        """Allow the agent to be used directly as a LangGraph node callable."""
        return self.run(state)