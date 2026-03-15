backend/services/trades_comparison_service.py
from typing import Optional
from backend.models.options_contract import OptionsContract
from backend.models.tradability_score import TradabilityScore
from backend.models.tradability_metrics import TradabilityMetrics


class TradesComparisonService:
    """
    Service for comparing and scoring options trades.
    Consolidates trade scoring logic previously spread across multiple files.
    """

    def score_trade(
        self,
        contract: OptionsContract,
        metrics: Optional[TradabilityMetrics] = None,
    ) -> TradabilityScore:
        """
        Score a single options contract for tradability.

        Args:
            contract: The options contract to score.
            metrics: Optional pre-computed metrics. If not provided, they will
                     be computed from the contract.

        Returns:
            A TradabilityScore instance representing the trade quality.
        """
        if metrics is None:
            metrics = self._compute_metrics(contract)

        score = self._calculate_score(contract, metrics)
        return score

    def compare_trades(
        self,
        contracts: list[OptionsContract],
    ) -> list[TradabilityScore]:
        """
        Score and rank a list of options contracts.

        Args:
            contracts: List of options contracts to compare.

        Returns:
            A list of TradabilityScore instances, sorted by score descending.
        """
        scores = [self.score_trade(contract) for contract in contracts]
        scores.sort(key=lambda s: s.score, reverse=True)
        return scores

    def _compute_metrics(self, contract: OptionsContract) -> TradabilityMetrics:
        """
        Compute tradability metrics from an options contract.

        Args:
            contract: The options contract.

        Returns:
            Computed TradabilityMetrics.
        """
        bid = contract.bid or 0.0
        ask = contract.ask or 0.0
        mid = (bid + ask) / 2.0 if (bid + ask) > 0 else 0.0

        spread = ask - bid
        spread_pct = (spread / ask * 100.0) if ask > 0 else 0.0

        open_interest = contract.open_interest or 0
        volume = contract.total_volume or 0

        delta = abs(contract.delta) if contract.delta is not None else 0.0
        implied_volatility = contract.implied_volatility or 0.0
        days_to_expiration = contract.days_to_expiration or 0

        return TradabilityMetrics(
            bid=bid,
            ask=ask,
            mid=mid,
            spread=spread,
            spread_pct=spread_pct,
            open_interest=open_interest,
            volume=volume,
            delta=delta,
            implied_volatility=implied_volatility,
            days_to_expiration=days_to_expiration,
        )

    def _calculate_score(
        self,
        contract: OptionsContract,
        metrics: TradabilityMetrics,
    ) -> TradabilityScore:
        """
        Calculate a tradability score from contract and metrics.

        Args:
            contract: The options contract.
            metrics: Pre-computed tradability metrics.

        Returns:
            A TradabilityScore instance.
        """
        score = 0.0
        reasons: list[str] = []

        # Liquidity: reward tight spreads
        if metrics.spread_pct < 5.0:
            score += 30.0
            reasons.append("Tight bid-ask spread (<5%)")
        elif metrics.spread_pct < 10.0:
            score += 15.0
            reasons.append("Moderate bid-ask spread (<10%)")
        else:
            reasons.append("Wide bid-ask spread (>=10%)")

        # Open interest
        if metrics.open_interest >= 1000:
            score += 25.0
            reasons.append("High open interest (>=1000)")
        elif metrics.open_interest >= 100:
            score += 12.0
            reasons.append("Moderate open interest (>=100)")
        else:
            reasons.append("Low open interest (<100)")

        # Volume
        if metrics.volume >= 500:
            score += 20.0
            reasons.append("High volume (>=500)")
        elif metrics.volume >= 50:
            score += 10.0
            reasons.append("Moderate volume (>=50)")
        else:
            reasons.append("Low volume (<50)")

        # Delta: prefer near-the-money (0.3 to 0.7)
        if 0.3 <= metrics.delta <= 0.7:
            score += 15.0
            reasons.append("Favorable delta range (0.3-0.7)")
        elif 0.2 <= metrics.delta < 0.3 or 0.7 < metrics.delta <= 0.8:
            score += 7.0
            reasons.append("Acceptable delta range")
        else:
            reasons.append("Unfavorable delta range")

        # Days to expiration: prefer 20-60 DTE
        if 20 <= metrics.days_to_expiration <= 60:
            score += 10.0
            reasons.append("Optimal DTE (20-60 days)")
        elif 10 <= metrics.days_to_expiration < 20 or 60 < metrics.days_to_expiration <= 90:
            score += 5.0
            reasons.append("Acceptable DTE")
        else:
            reasons.append("Suboptimal DTE")

        # Clamp score to [0, 100]
        score = max(0.0, min(100.0, score))

        return TradabilityScore(
            contract=contract,
            metrics=metrics,
            score=score,
            reasons=reasons,
        )