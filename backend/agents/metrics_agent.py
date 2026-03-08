from backend.agents.state import PipelineState


class MetricsAgent:
    """Agent responsible for computing financial and options metrics.

    In the full pipeline this agent will calculate Greeks, implied
    volatility surfaces, historical volatility, and other quantitative
    metrics required downstream by the TradabilityAgent.  For now it
    is a stub that returns the state dict with ``metrics`` set to None.
    """

    def run(self, state: PipelineState) -> PipelineState:
        """Execute the metrics computation step.

        Parameters
        ----------
        state:
            The current pipeline state passed in from the preceding node.

        Returns
        -------
        PipelineState
            The state dict with ``metrics`` set to None until this agent
            is fully implemented.
        """
        # TODO: implement Greeks, IV surface, and historical volatility.
        state["metrics"] = None
        return state

    def __call__(self, state: PipelineState) -> PipelineState:
        """Allow the agent instance to be used directly as a LangGraph node."""
        return self.run(state)