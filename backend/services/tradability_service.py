from typing import List, Optional
from backend.models.tradability import TradabilityWeights, TradabilityScore
from backend.models.opportunity import Opportunity


class TradabilityService:
    def __init__(self, weights: Optional[TradabilityWeights] = None):
        self.weights = weights or TradabilityWeights()

    def extract_metrics(self, opportunity: Opportunity) -> dict:
        return {
            "liquidity": getattr(opportunity, "liquidity", 0.0),
            "volatility": getattr(opportunity, "volatility", 0.0),
            "spread": getattr(opportunity, "spread", 0.0),
            "momentum": getattr(opportunity, "momentum", 0.0),
            "volume": getattr(opportunity, "volume", 0.0),
        }

    def compute_score(self, opportunity: Opportunity) -> TradabilityScore:
        metrics = self.extract_metrics(opportunity)

        liquidity_score = min(max(metrics["liquidity"], 0.0), 1.0)
        volatility_score = min(max(1.0 - metrics["volatility"], 0.0), 1.0)
        spread_score = min(max(1.0 - metrics["spread"], 0.0), 1.0)
        momentum_score = min(max(metrics["momentum"], 0.0), 1.0)
        volume_score = min(max(metrics["volume"], 0.0), 1.0)

        w = self.weights
        composite = (
            w.liquidity * liquidity_score
            + w.volatility * volatility_score
            + w.spread * spread_score
            + w.momentum * momentum_score
            + w.volume * volume_score
        )

        composite = min(max(composite, 0.0), 1.0)

        return TradabilityScore(
            opportunity_id=str(opportunity.id),
            liquidity_score=liquidity_score,
            volatility_score=volatility_score,
            spread_score=spread_score,
            momentum_score=momentum_score,
            volume_score=volume_score,
            composite_score=composite,
        )

    def rank_candidates(self, opportunities: List[Opportunity]) -> List[TradabilityScore]:
        scores = [self.compute_score(opp) for opp in opportunities]
        return sorted(scores, key=lambda s: s.composite_score, reverse=True)

    def get_best_trade(self, opportunities: List[Opportunity]) -> Optional[TradabilityScore]:
        if not opportunities:
            return None
        ranked = self.rank_candidates(opportunities)
        return ranked[0] if ranked else None