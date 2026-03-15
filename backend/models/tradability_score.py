from pydantic import BaseModel, Field
from typing import Optional
from backend.models.options_contract import OptionsContract


class TradabilityScore(BaseModel):
    symbol: str
    score: float = Field(..., ge=0.0, le=1.0)
    recommendation: Optional[str] = None
    contract: Optional[OptionsContract] = None
    reasoning: Optional[str] = None
