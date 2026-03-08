from typing import Any, Optional
from typing_extensions import TypedDict


class PipelineState(TypedDict):
    """Shared state passed between all agents in the LangGraph pipeline."""

    ticker: str
    options_data: Optional[Any]
    metrics: Optional[Any]
    market_sentiment: Optional[Any]
    tradability_score: Optional[Any]
    errors: list[str]
