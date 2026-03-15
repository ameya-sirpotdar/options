backend/services/trades_comparison_service.py

from typing import Optional
from backend.models.options_contract import OptionsContract
from backend.models.tradability_score import TradabilityScore
from backend.models.tradability_metrics import TradabilityMetrics


class TradesComparisonService:
    """
    Consolidated service combining tradability scoring (formerly TradabilityService)
    and CCP (Closest Comparable Price) calculation logic.
    All existing logic preserved exactly — copy-paste consolidation only.
    """

    # ---------------------------------------------------------------------------
    # Tradability scoring (formerly TradabilityService)
    # ---------------------------------------------------------------------------

    def score_contract(self, contract: OptionsContract) -> TradabilityScore:
        """
        Compute a tradability score for a single options contract.
        Returns a TradabilityScore with a numeric score and descriptive metrics.
        """
        metrics = self._compute_metrics(contract)
        score = self._aggregate_score(metrics)
        return TradabilityScore(score=score, metrics=metrics)

    def _compute_metrics(self, contract: OptionsContract) -> TradabilityMetrics:
        bid = contract.bid if contract.bid is not None else 0.0
        ask = contract.ask if contract.ask is not None else 0.0
        volume = contract.volume if contract.volume is not None else 0
        open_interest = contract.open_interest if contract.open_interest is not None else 0

        spread = ask - bid
        mid = (bid + ask) / 2.0 if (bid + ask) > 0 else 0.0
        spread_pct = (spread / mid) if mid > 0 else 1.0

        return TradabilityMetrics(
            bid=bid,
            ask=ask,
            spread=spread,
            spread_pct=spread_pct,
            volume=volume,
            open_interest=open_interest,
        )

    def _aggregate_score(self, metrics: TradabilityMetrics) -> float:
        """
        Aggregate individual metric scores into a single tradability score [0, 1].
        Higher is more tradable.
        """
        spread_score = self._score_spread_pct(metrics.spread_pct)
        volume_score = self._score_volume(metrics.volume)
        oi_score = self._score_open_interest(metrics.open_interest)

        # Weighted average: spread is most important
        score = 0.5 * spread_score + 0.3 * volume_score + 0.2 * oi_score
        return round(min(max(score, 0.0), 1.0), 4)

    @staticmethod
    def _score_spread_pct(spread_pct: float) -> float:
        """Score based on bid-ask spread percentage. Lower spread → higher score."""
        if spread_pct <= 0.02:
            return 1.0
        elif spread_pct <= 0.05:
            return 0.8
        elif spread_pct <= 0.10:
            return 0.6
        elif spread_pct <= 0.20:
            return 0.4
        elif spread_pct <= 0.50:
            return 0.2
        else:
            return 0.0

    @staticmethod
    def _score_volume(volume: int) -> float:
        """Score based on daily volume. Higher volume → higher score."""
        if volume >= 1000:
            return 1.0
        elif volume >= 500:
            return 0.8
        elif volume >= 100:
            return 0.6
        elif volume >= 10:
            return 0.4
        elif volume >= 1:
            return 0.2
        else:
            return 0.0

    @staticmethod
    def _score_open_interest(open_interest: int) -> float:
        """Score based on open interest. Higher OI → higher score."""
        if open_interest >= 10000:
            return 1.0
        elif open_interest >= 1000:
            return 0.8
        elif open_interest >= 100:
            return 0.6
        elif open_interest >= 10:
            return 0.4
        elif open_interest >= 1:
            return 0.2
        else:
            return 0.0

    # ---------------------------------------------------------------------------
    # CCP — Closest Comparable Price (formerly CCPCalculator / ccp_service)
    # ---------------------------------------------------------------------------

    def calculate_ccp(
        self,
        target_contract: OptionsContract,
        comparable_contracts: list[OptionsContract],
    ) -> Optional[float]:
        """
        Calculate the Closest Comparable Price for a target contract given a list
        of comparable contracts.

        The CCP is the mid-price of the comparable contract whose strike price is
        closest to the target contract's strike price (same expiration and type
        are assumed to have been pre-filtered by the caller).

        Returns the CCP as a float, or None if no comparable contracts are provided.
        """
        if not comparable_contracts:
            return None

        target_strike = target_contract.strike_price
        if target_strike is None:
            return None

        closest = min(
            comparable_contracts,
            key=lambda c: abs((c.strike_price or 0.0) - target_strike),
        )

        return self._mid_price(closest)

    @staticmethod
    def _mid_price(contract: OptionsContract) -> Optional[float]:
        """Return the mid-price of a contract, or None if bid/ask are unavailable."""
        bid = contract.bid
        ask = contract.ask
        if bid is None or ask is None:
            return None
        return round((bid + ask) / 2.0, 4)

    def compare_trades(
        self,
        target_contract: OptionsContract,
        comparable_contracts: list[OptionsContract],
    ) -> dict:
        """
        Full comparison: returns tradability score and CCP for the target contract.

        Returns a dict with keys:
            - 'tradability_score': TradabilityScore
            - 'ccp': float | None
        """
        tradability = self.score_contract(target_contract)
        ccp = self.calculate_ccp(target_contract, comparable_contracts)

        return {
            "tradability_score": tradability,
            "ccp": ccp,
        }