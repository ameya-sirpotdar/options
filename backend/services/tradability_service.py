from typing import List, Optional
from backend.models.tradability import TradabilityScore, TradabilityWeights
from backend.models.opportunity import TradeOpportunity


class TradabilityService:
    def __init__(self, weights: Optional[TradabilityWeights] = None):
        self.weights = weights or TradabilityWeights()

    def extract_metrics(self, opportunity: TradeOpportunity) -> dict:
        metrics = {}

        metrics["liquidity"] = float(getattr(opportunity, "liquidity_score", 0.0) or 0.0)
        metrics["volatility"] = float(getattr(opportunity, "volatility_score", 0.0) or 0.0)
        metrics["momentum"] = float(getattr(opportunity, "momentum_score", 0.0) or 0.0)
        metrics["spread"] = float(getattr(opportunity, "spread_score", 0.0) or 0.0)
        metrics["volume"] = float(getattr(opportunity, "volume_score", 0.0) or 0.0)

        return metrics

    def compute_score(self, opportunity: TradeOpportunity) -> TradabilityScore:
        metrics = self.extract_metrics(opportunity)

        weighted_sum = (
            metrics["liquidity"] * self.weights.liquidity
            + metrics["volatility"] * self.weights.volatility
            + metrics["momentum"] * self.weights.momentum
            + metrics["spread"] * self.weights.spread
            + metrics["volume"] * self.weights.volume
        )

        total_weight = (
            self.weights.liquidity
            + self.weights.volatility
            + self.weights.momentum
            + self.weights.spread
            + self.weights.volume
        )

        composite_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        composite_score = max(0.0, min(1.0, composite_score))

        return TradabilityScore(
            opportunity_id=opportunity.id,
            symbol=opportunity.symbol,
            composite_score=composite_score,
            liquidity_score=metrics["liquidity"],
            volatility_score=metrics["volatility"],
            momentum_score=metrics["momentum"],
            spread_score=metrics["spread"],
            volume_score=metrics["volume"],
            weights_used=self.weights,
        )

    def rank_candidates(self, opportunities: List[TradeOpportunity]) -> List[TradabilityScore]:
        scores = [self.compute_score(opp) for opp in opportunities]
        scores.sort(key=lambda s: s.composite_score, reverse=True)
        return scores

    def get_best_trade(self, opportunities: List[TradeOpportunity]) -> Optional[TradabilityScore]:
        if not opportunities:
            return None
        ranked = self.rank_candidates(opportunities)
        return ranked[0] if ranked else None