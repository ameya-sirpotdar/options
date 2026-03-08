from typing import Any, Dict, List

from backend.agents.options_agent import run_options_poll


class PollingService:
    def poll_options(self, tickers: List[str]) -> Dict[str, Any]:
        return run_options_poll(tickers)
