from typing import Optional
from backend.models.tradability import TradabilityWeights, TradabilityScore
from backend.config import Settings


class TradabilityService:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.weights = TradabilityWeights(
            liquidity=self.settings.weight_liquidity,
            volatility=self.settings.weight_volatility,
            momentum=self.settings.weight_momentum,
            spread=self.settings.weight_spread,
            volume=self.settings.weight_volume,
        )

    def extract_metrics(self, candidate: dict) -> dict:
        """
        Extract and normalize tradability metrics from a raw candidate dict.
        Returns a dict with keys: liquidity, volatility, momentum, spread, volume.
        All values are expected to be floats in [0, 1] after normalization.
        """
        metrics = {}

        metrics["liquidity"] = float(candidate.get("liquidity", 0.0))
        metrics["volatility"] = float(candidate.get("volatility", 0.0))
        metrics["momentum"] = float(candidate.get("momentum", 0.0))
        metrics["spread"] = float(candidate.get("spread", 0.0))
        metrics["volume"] = float(candidate.get("volume", 0.0))

        return metrics

    def compute_score(self, candidate: dict, weights: Optional[TradabilityWeights] = None) -> TradabilityScore:
        """
        Compute the tradability score for a single candidate.
        Uses provided weights or falls back to instance-level weights.
        """
        w = weights or self.weights
        metrics = self.extract_metrics(candidate)

        symbol = candidate.get("symbol", "UNKNOWN")

        # Spread is a cost/friction metric: lower spread is better, so we invert it
        spread_score = 1.0 - metrics["spread"]

        raw_score = (
            w.liquidity * metrics["liquidity"]
            + w.volatility * metrics["volatility"]
            + w.momentum * metrics["momentum"]
            + w.spread * spread_score
            + w.volume * metrics["volume"]
        )

        # Clamp to [0, 1]
        score = max(0.0, min(1.0, raw_score))

        return TradabilityScore(
            symbol=symbol,
            score=score,
            liquidity=metrics["liquidity"],
            volatility=metrics["volatility"],
            momentum=metrics["momentum"],
            spread=metrics["spread"],
            volume=metrics["volume"],
        )

    def rank_candidates(
        self,
        candidates: list[dict],
        weights: Optional[TradabilityWeights] = None,
    ) -> list[TradabilityScore]:
        """
        Score and rank a list of candidates by tradability score descending.
        """
        if not candidates:
            return []

        scored = [self.compute_score(c, weights=weights) for c in candidates]
        ranked = sorted(scored, key=lambda s: s.score, reverse=True)
        return ranked

    def get_best_trade(
        self,
        candidates: list[dict],
        weights: Optional[TradabilityWeights] = None,
    ) -> Optional[TradabilityScore]:
        """
        Return the single best tradable candidate, or None if the list is empty.
        """
        ranked = self.rank_candidates(candidates, weights=weights)
        if not ranked:
            return None
        return ranked[0]