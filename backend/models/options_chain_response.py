from pydantic import BaseModel
from typing import Optional, List
from backend.models.options_contract import OptionsContract


class OptionsChainResponse(BaseModel):
    symbol: str
    status: Optional[str] = None
    contracts: List[OptionsContract] = []
    underlying_price: Optional[float] = None
    error: Optional[str] = None
