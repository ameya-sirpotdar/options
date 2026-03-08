from typing import TypedDict


class MetricsState(TypedDict, total=False):
    """Typed state dictionary for the MetricsAgent pipeline node."""

    ticker: str
    metrics: dict


class MetricsAgent:
    """Agent responsible for computing financial and options metrics.

    In the full pipeline this agent will calculate Greeks, implied
    volatility surfaces, historical volatility, and other quantitative
    metrics required downstream by the TradabilityAgent.  For now it
    is a stub that returns the state dict unchanged.
    """

    def run(self, state: MetricsState) -> MetricsState:
        """Execute the metrics computation step.

        Parameters
        ----------
        state:
            The current pipeline state passed in from the preceding node.

        Returns
        -------
        MetricsState
            The state dict returned unchanged until this agent is fully
            implemented.
        """
        return state