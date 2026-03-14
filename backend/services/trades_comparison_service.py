backend/services/trades_comparison_service.py
from __future__ import annotations

import logging
from typing import Any

from backend.models.options_contract import OptionsContract
from backend.models.tradability_score import TradabilityScore
from backend.models.tradability_metrics import TradabilityMetrics

logger = logging.getLogger(__name__)


class TradesComparisonService:
    """
    Consolidates tradability scoring and CCP calculation logic.

    Formerly split across:
      - tradability_service.py
      - ccp_calculator.py
    """

    # ---------------------------------------------------------------------------
    # CCP (Cost / Credit / Premium) helpers
    # ---------------------------------------------------------------------------

    @staticmethod
    def calculate_ccp(contract: OptionsContract) -> float:
        """
        Calculate the Cost/Credit/Premium score for a single options contract.

        The CCP is a normalised measure in [0, 1] that rewards contracts with:
          - a high bid/ask mid-point relative to the strike price
          - a tight bid/ask spread (low slippage)

        Returns 0.0 when the contract data are insufficient to compute a score.
        """
        try:
            bid: float = float(contract.bid or 0)
            ask: float = float(contract.ask or 0)
            strike: float = float(contract.strike_price or 0)

            if strike <= 0:
                return 0.0

            mid = (bid + ask) / 2.0
            spread = ask - bid

            if mid <= 0:
                return 0.0

            # Spread penalty: fraction of mid consumed by the spread
            spread_penalty = spread / mid if mid > 0 else 1.0
            spread_penalty = min(spread_penalty, 1.0)

            # Premium-to-strike ratio (capped at 1)
            premium_ratio = min(mid / strike, 1.0)

            ccp = premium_ratio * (1.0 - spread_penalty)
            return round(max(ccp, 0.0), 6)

        except (TypeError, ValueError, ZeroDivisionError) as exc:
            logger.debug("CCP calculation failed for contract %s: %s", contract, exc)
            return 0.0

    # ---------------------------------------------------------------------------
    # Tradability metrics
    # ---------------------------------------------------------------------------

    @staticmethod
    def compute_metrics(contract: OptionsContract) -> TradabilityMetrics:
        """
        Derive a full set of tradability metrics from a single contract.
        """
        bid: float = float(contract.bid or 0)
        ask: float = float(contract.ask or 0)
        volume: int = int(contract.volume or 0)
        open_interest: int = int(contract.open_interest or 0)
        implied_volatility: float = float(contract.implied_volatility or 0)
        delta: float = float(contract.delta or 0)

        mid = (bid + ask) / 2.0
        spread = ask - bid
        spread_pct = (spread / mid * 100.0) if mid > 0 else 0.0

        return TradabilityMetrics(
            bid=bid,
            ask=ask,
            mid=round(mid, 4),
            spread=round(spread, 4),
            spread_pct=round(spread_pct, 4),
            volume=volume,
            open_interest=open_interest,
            implied_volatility=round(implied_volatility, 6),
            delta=round(delta, 6),
        )

    # ---------------------------------------------------------------------------
    # Tradability scoring
    # ---------------------------------------------------------------------------

    def score_contract(self, contract: OptionsContract) -> TradabilityScore:
        """
        Produce a :class:`TradabilityScore` for *contract*.

        The composite score is a weighted sum of sub-scores:

        +-----------------------+--------+
        | Component             | Weight |
        +=======================+========+
        | CCP                   |  0.35  |
        | Liquidity (vol + OI)  |  0.30  |
        | Spread tightness      |  0.20  |
        | IV attractiveness     |  0.15  |
        +-----------------------+--------+
        """
        metrics = self.compute_metrics(contract)
        ccp = self.calculate_ccp(contract)

        liquidity_score = self._liquidity_score(metrics.volume, metrics.open_interest)
        spread_score = self._spread_score(metrics.spread_pct)
        iv_score = self._iv_score(metrics.implied_volatility)

        composite = (
            0.35 * ccp
            + 0.30 * liquidity_score
            + 0.20 * spread_score
            + 0.15 * iv_score
        )

        return TradabilityScore(
            symbol=contract.symbol,
            description=contract.description,
            contract_type=contract.contract_type,
            strike_price=contract.strike_price,
            expiration_date=contract.expiration_date,
            bid=metrics.bid,
            ask=metrics.ask,
            mid=metrics.mid,
            spread=metrics.spread,
            spread_pct=metrics.spread_pct,
            volume=metrics.volume,
            open_interest=metrics.open_interest,
            implied_volatility=metrics.implied_volatility,
            delta=metrics.delta,
            ccp=round(ccp, 6),
            liquidity_score=round(liquidity_score, 6),
            spread_score=round(spread_score, 6),
            iv_score=round(iv_score, 6),
            composite_score=round(composite, 6),
        )

    # ---------------------------------------------------------------------------
    # Batch comparison
    # ---------------------------------------------------------------------------

    def rank_contracts(
        self, contracts: list[OptionsContract]
    ) -> list[TradabilityScore]:
        """
        Score and rank a list of contracts by composite score (descending).
        """
        scores: list[TradabilityScore] = []
        for contract in contracts:
            try:
                scores.append(self.score_contract(contract))
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "Skipping contract %s during ranking: %s", contract, exc
                )

        scores.sort(key=lambda s: s.composite_score, reverse=True)
        return scores

    def best_trade(
        self, contracts: list[OptionsContract]
    ) -> TradabilityScore | None:
        """
        Return the highest-scoring contract, or *None* if the list is empty.
        """
        ranked = self.rank_contracts(contracts)
        return ranked[0] if ranked else None

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    @staticmethod
    def _liquidity_score(volume: int, open_interest: int) -> float:
        """
        Normalised liquidity score in [0, 1].

        Uses a soft-cap via a logistic-like function so that very high values
        do not dominate while still rewarding liquid contracts.
        """
        if volume <= 0 and open_interest <= 0:
            return 0.0

        # Combine with equal weight; thresholds chosen empirically
        vol_score = min(volume / 500.0, 1.0)
        oi_score = min(open_interest / 1000.0, 1.0)
        return round((vol_score + oi_score) / 2.0, 6)

    @staticmethod
    def _spread_score(spread_pct: float) -> float:
        """
        Convert a spread percentage into a [0, 1] score where 0 % → 1.0
        and spreads ≥ 20 % → 0.0.
        """
        if spread_pct <= 0:
            return 1.0
        if spread_pct >= 20.0:
            return 0.0
        return round(1.0 - spread_pct / 20.0, 6)

    @staticmethod
    def _iv_score(implied_volatility: float) -> float:
        """
        Score implied volatility.

        Moderate IV (20 %–60 %) is considered attractive for premium selling.
        Very low or very high IV is penalised.
        """
        iv_pct = implied_volatility * 100.0  # assume stored as decimal

        if iv_pct <= 0:
            return 0.0
        if iv_pct < 20.0:
            # Ramp up from 0 to 1 between 0 % and 20 %
            return round(iv_pct / 20.0, 6)
        if iv_pct <= 60.0:
            # Sweet spot
            return 1.0
        if iv_pct <= 100.0:
            # Ramp down from 1 to 0 between 60 % and 100 %
            return round(1.0 - (iv_pct - 60.0) / 40.0, 6)
        return 0.0