from pydantic import BaseModel, Field
from typing import List, Optional
from backend.models.options_contract import OptionsContract


class OptionsChainResponse(BaseModel):
    symbol: str = Field(..., description="The underlying ticker symbol")
    status: str = Field(default="SUCCESS", description="Status of the options chain response")
    underlying_price: Optional[float] = Field(
        None, description="Current price of the underlying asset"
    )
    contracts: List[OptionsContract] = Field(
        default_factory=list, description="List of options contracts"
    )
    best_call: Optional[OptionsContract] = Field(
        None, description="The best call option contract"
    )
    best_put: Optional[OptionsContract] = Field(
        None, description="The best put option contract"
    )

    model_config = {"populate_by_name": True}
