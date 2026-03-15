backend/models/options_chain_response.py
from pydantic import BaseModel
from typing import Optional, List
from backend.models.options_contract import OptionsContract


class OptionsChainResponse(BaseModel):
    symbol: str
    status: str
    contracts: List[OptionsContract] = []
    error: Optional[str] = None