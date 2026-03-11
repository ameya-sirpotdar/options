from pydantic import BaseModel, field_validator, model_validator
from typing import Any, Dict, List, Optional


class OptionsChainRequest(BaseModel):
    tickers: List[str]

    @field_validator("tickers")
    @classmethod
    def tickers_must_not_be_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("tickers list must not be empty")
        return v

    @field_validator("tickers")
    @classmethod
    def tickers_must_be_valid(cls, v: List[str]) -> List[str]:
        normalised = []
        for ticker in v:
            if not isinstance(ticker, str):
                raise ValueError(f"each ticker must be a string, got {type(ticker)}")
            stripped = ticker.strip()
            if not stripped:
                raise ValueError("ticker symbols must not be blank or whitespace-only")
            upper = stripped.upper()
            if len(upper) > 10:
                raise ValueError(
                    f"ticker symbol '{upper}' exceeds maximum length of 10 characters"
                )
            normalised.append(upper)
        return normalised

    @model_validator(mode="after")
    def deduplicate_and_limit(self) -> "OptionsChainRequest":
        seen = []
        for ticker in self.tickers:
            if ticker not in seen:
                seen.append(ticker)
        if len(seen) > 10:
            raise ValueError("cannot request more than 10 tickers at once")
        self.tickers = seen
        return self


# Backwards-compatible alias
PollOptionsRequest = OptionsChainRequest


class PollOptionsResponse(BaseModel):
    tickers: List[str]
    results: Dict[str, Any]
    run_id: Optional[str] = None
