from typing import Optional

from pydantic import BaseModel, Field

from backend.models.options_contract import OptionsContract


class TradabilityScore(BaseModel):
    """Tradability score for an options contract candidate."""

    symbol: str
    score: float = Field(..., ge=0.0, le=1.0)
    contract: Optional[OptionsContract] = None
    reasoning: Optional[str] = None
