from pydantic import BaseModel, Field
from typing import List, Optional

from backend.models.options_contract import OptionsContract


class OptionsChainResponse(BaseModel):
    symbol: str
    contracts: List[OptionsContract] = []
    underlying_price: Optional[float] = None
    status: Optional[str] = None
    error: Optional[str] = None


class BestTradeResponse(BaseModel):
    """Response payload for the GET /trades/best endpoint."""

    best_candidate: Optional[dict] = Field(
        None, description="The highest-scoring trade candidate, or null if none available."
    )
    ranked_candidates: List[dict] = Field(
        default_factory=list,
        description="All evaluated candidates ordered from highest to lowest score.",
    )
