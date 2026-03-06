from pydantic import BaseModel, field_validator, model_validator
from typing import List


MAX_TICKERS = 50
MAX_TICKER_LENGTH = 10


class PollOptionsRequest(BaseModel):
    tickers: List[str]

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("tickers list must not be empty")
        if len(v) > MAX_TICKERS:
            raise ValueError(
                f"tickers list must not exceed {MAX_TICKERS} items, got {len(v)}"
            )
        normalised = []
        for ticker in v:
            if not isinstance(ticker, str):
                raise ValueError(f"each ticker must be a string, got {type(ticker)}")
            stripped = ticker.strip().upper()
            if not stripped:
                raise ValueError("ticker must not be blank or whitespace only")
            if len(stripped) > MAX_TICKER_LENGTH:
                raise ValueError(
                    f"ticker '{stripped}' exceeds maximum length of {MAX_TICKER_LENGTH} characters"
                )
            if not stripped.isalpha():
                raise ValueError(
                    f"ticker '{stripped}' must contain only alphabetic characters"
                )
            normalised.append(stripped)
        return normalised

    @model_validator(mode="after")
    def validate_unique_tickers(self) -> "PollOptionsRequest":
        seen = set()
        duplicates = []
        for ticker in self.tickers:
            if ticker in seen:
                duplicates.append(ticker)
            seen.add(ticker)
        if duplicates:
            raise ValueError(
                f"tickers list must not contain duplicates, found: {duplicates}"
            )
        return self


class TickerResult(BaseModel):
    ticker: str
    status: str
    data: dict | None = None
    error: str | None = None


class PollOptionsResponse(BaseModel):
    results: List[TickerResult]
    total: int
    succeeded: int
    failed: int

    @model_validator(mode="after")
    def validate_counts(self) -> "PollOptionsResponse":
        if self.total != len(self.results):
            raise ValueError(
                f"total ({self.total}) does not match number of results ({len(self.results)})"
            )
        succeeded_count = sum(1 for r in self.results if r.status == "success")
        failed_count = sum(1 for r in self.results if r.status == "error")
        if self.succeeded != succeeded_count:
            raise ValueError(
                f"succeeded count ({self.succeeded}) does not match actual successes ({succeeded_count})"
            )
        if self.failed != failed_count:
            raise ValueError(
                f"failed count ({self.failed}) does not match actual failures ({failed_count})"
            )
        return self