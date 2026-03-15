import math
from typing import Optional
from backend.models.options_contract import OptionsContract
from backend.models.tradability_score import TradabilityScore
from backend.models.tradability_metrics import TradabilityMetrics


class TradesComparisonService:
    """
    Service for comparing and scoring options trades.
    Consolidates trade scoring logic previously spread across multiple services.
    """

    def compare_trades(
        self,
        contracts: list[OptionsContract],
    ) -> list[dict]:
        """
        Compare a list of options contracts and return ranked comparison results.

        Args:
            contracts: List of options contracts to compare.

        Returns:
            A list of dicts with contract and score, sorted descending by total score.
        """
        return self.rank_contracts(contracts)

    def score_trade(self, contract: OptionsContract) -> TradabilityScore:
        """
        Public alias for scoring a single options contract.

        Args:
            contract: The options contract to score.

        Returns:
            A TradabilityScore instance representing the contract's score.
        """
        return self._score_contract(contract)

    def _score_contract(self, contract: OptionsContract) -> TradabilityScore:
        """
        Score a single options contract based on tradability metrics.

        Args:
            contract: The options contract to score.

        Returns:
            A TradabilityScore instance representing the contract's score.
        """
        metrics = self._compute_metrics(contract)
        return self._compute_score(metrics)

    def _compute_metrics(self, contract: OptionsContract) -> TradabilityMetrics:
        """
        Compute tradability metrics for an options contract.

        Args:
            contract: The options contract to evaluate.

        Returns:
            A TradabilityMetrics instance with computed values.
        """
        bid = contract.bid if contract.bid is not None else 0.0
        ask = contract.ask if contract.ask is not None else 0.0
        volume = contract.volume if contract.volume is not None else 0
        open_interest = contract.open_interest if contract.open_interest is not None else 0
        delta = contract.delta if contract.delta is not None else 0.0
        implied_volatility = contract.implied_volatility if contract.implied_volatility is not None else 0.0

        mid = (bid + ask) / 2.0 if (bid + ask) > 0 else 0.0
        spread = ask - bid if ask >= bid else 0.0
        spread_pct = (spread / mid) if mid > 0 else 0.0

        return TradabilityMetrics(
            bid=bid,
            ask=ask,
            mid=mid,
            spread=spread,
            spread_pct=spread_pct,
            volume=volume,
            open_interest=open_interest,
            delta=delta,
            implied_volatility=implied_volatility,
        )

    def _compute_score(self, metrics: TradabilityMetrics) -> TradabilityScore:
        """
        Compute a tradability score from metrics.

        Scoring logic:
        - Spread score: lower spread percentage is better (max 40 points)
        - Volume score: higher volume is better (max 30 points)
        - Open interest score: higher open interest is better (max 20 points)
        - Delta score: delta closer to 0.3–0.4 range is better (max 10 points)

        Args:
            metrics: The tradability metrics to score.

        Returns:
            A TradabilityScore instance with component and total scores.
        """
        # Spread score: 0% spread = 40 pts, 100%+ spread = 0 pts
        spread_score = max(0.0, 40.0 * (1.0 - min(metrics.spread_pct, 1.0)))

        # Volume score: log-scale up to 30 pts, capped at volume=1000
        if metrics.volume > 0:
            volume_score = min(30.0, 30.0 * math.log10(metrics.volume + 1) / math.log10(1001))
        else:
            volume_score = 0.0

        # Open interest score: log-scale up to 20 pts, capped at oi=10000
        if metrics.open_interest > 0:
            oi_score = min(20.0, 20.0 * math.log10(metrics.open_interest + 1) / math.log10(10001))
        else:
            oi_score = 0.0

        # Delta score: ideal delta is 0.35 (absolute value), max 10 pts
        abs_delta = abs(metrics.delta)
        ideal_delta = 0.35
        delta_distance = abs(abs_delta - ideal_delta)
        delta_score = max(0.0, 10.0 * (1.0 - delta_distance / ideal_delta)) if ideal_delta > 0 else 0.0

        total = spread_score + volume_score + oi_score + delta_score

        return TradabilityScore(
            spread_score=round(spread_score, 4),
            volume_score=round(volume_score, 4),
            open_interest_score=round(oi_score, 4),
            delta_score=round(delta_score, 4),
            total=round(total, 4),
        )

    def rank_trades(
        self,
        contracts: list[OptionsContract],
    ) -> list[dict]:
        """
        Alias for rank_contracts. Rank a list of options contracts by their tradability score.

        Args:
            contracts: List of options contracts to rank.

        Returns:
            A list of dicts with contract and score, sorted descending by total score.
        """
        return self.rank_contracts(contracts)

    def rank_contracts(
        self,
        contracts: list[OptionsContract],
    ) -> list[dict]:
        """
        Rank a list of options contracts by their tradability score.

        Args:
            contracts: List of options contracts to rank.

        Returns:
            A list of dicts with contract and score, sorted descending by total score.
        """
        scored = [
            {
                "contract": contract,
                "score": self._score_contract(contract),
            }
            for contract in contracts
        ]
        scored.sort(key=lambda x: x["score"].total, reverse=True)
        return scored

    def get_best_contract(
        self,
        contracts: list[OptionsContract],
    ) -> Optional[dict]:
        """
        Return the highest-scoring options contract from a list.

        Args:
            contracts: List of options contracts to evaluate.

        Returns:
            A dict with 'contract' and 'score' for the best contract,
            or None if the list is empty.
        """
        if not contracts:
            return None
        ranked = self.rank_contracts(contracts)
        return ranked[0]
