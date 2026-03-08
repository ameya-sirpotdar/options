# TODO(#XX): fetch real sentiment data — see follow-up issue for implementation.
from backend.agents.state import PipelineState

__all__ = ["MarketSentimentAgent"]


class MarketSentimentAgent:
    """
    Placeholder agent responsible for analyzing market sentiment for a given ticker.

    In the full pipeline this agent will:
    - Fetch recent news headlines and social media signals for the ticker
    - Run a sentiment model to produce a numeric sentiment score
    - Classify the score into a human-readable label (e.g. bullish, bearish, neutral)
    - Populate the market_sentiment field of PipelineState for downstream agents

    Currently implemented as a no-op stub that sets market_sentiment to None.
    """

    def run(self, state: PipelineState) -> PipelineState:
        """
        Execute the market sentiment analysis step.

        Parameters
        ----------
        state:
            The current shared pipeline state dictionary.

        Returns
        -------
        PipelineState
            The state dictionary with ``market_sentiment`` set to ``None``
            (stub behaviour).
        """
        state["market_sentiment"] = None
        return state

    def __call__(self, state: PipelineState) -> PipelineState:
        return self.run(state)