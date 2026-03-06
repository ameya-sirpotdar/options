from backend.agents.options_agent import run_options_poll


class PollingService:
    def poll_options(self, tickers: list[str]) -> dict:
        normalized = [ticker.upper().strip() for ticker in tickers]
        result = run_options_poll(normalized)
        return result