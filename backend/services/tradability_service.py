from typing import List, Optional
from backend.models.tradability import TradabilityWeights, ScoredTrade
from backend.config import settings


def extract_metrics(trade: dict) -> dict:
    """
    Extract relevant tradability metrics from a raw trade dictionary.

    Expected trade fields (all optional, default to neutral values if missing):
      - spread_pct: float, bid-ask spread as a percentage (lower is better)
      - volume_24h: float, 24-hour trading volume in USD (higher is better)
      - slippage_pct: float, estimated slippage as a percentage (lower is better)
      - volatility_pct: float, recent price volatility as a percentage (lower is better)
      - liquidity_score: float, 0–100 composite liquidity score (higher is better)

    Returns a dict with keys matching the above, with defaults applied.
    """
    return {
        "spread_pct": float(trade.get("spread_pct", 1.0)),
        "volume_24h": float(trade.get("volume_24h", 0.0)),
        "slippage_pct": float(trade.get("slippage_pct", 1.0)),
        "volatility_pct": float(trade.get("volatility_pct", 50.0)),
        "liquidity_score": float(trade.get("liquidity_score", 0.0)),
    }


def _normalize_spread(spread_pct: float) -> float:
    """
    Normalize spread percentage to a 0–1 score where lower spread → higher score.

    Uses an inverse linear mapping clamped to [0, 1]:
      score = 1 - clamp(spread_pct / MAX_SPREAD, 0, 1)

    MAX_SPREAD is defined as 5.0% (a spread of 5% or more scores 0).
    """
    MAX_SPREAD = 5.0
    clamped = max(0.0, min(spread_pct, MAX_SPREAD))
    return 1.0 - (clamped / MAX_SPREAD)


def _normalize_volume(volume_24h: float) -> float:
    """
    Normalize 24h volume to a 0–1 score where higher volume → higher score.

    Uses a logarithmic mapping:
      score = clamp(log10(volume_24h + 1) / LOG_MAX, 0, 1)

    LOG_MAX corresponds to log10(1_000_000_001) ≈ 9, meaning volumes at or
    above $1B score 1.0.
    """
    import math

    LOG_MAX = math.log10(1_000_000_001)
    raw = math.log10(volume_24h + 1)
    return max(0.0, min(raw / LOG_MAX, 1.0))


def _normalize_slippage(slippage_pct: float) -> float:
    """
    Normalize slippage percentage to a 0–1 score where lower slippage → higher score.

    Uses an inverse linear mapping clamped to [0, 1]:
      score = 1 - clamp(slippage_pct / MAX_SLIPPAGE, 0, 1)

    MAX_SLIPPAGE is defined as 3.0%.
    """
    MAX_SLIPPAGE = 3.0
    clamped = max(0.0, min(slippage_pct, MAX_SLIPPAGE))
    return 1.0 - (clamped / MAX_SLIPPAGE)


def _normalize_volatility(volatility_pct: float) -> float:
    """
    Normalize volatility percentage to a 0–1 score where lower volatility → higher score.

    Uses an inverse linear mapping clamped to [0, 1]:
      score = 1 - clamp(volatility_pct / MAX_VOLATILITY, 0, 1)

    MAX_VOLATILITY is defined as 100.0%.
    """
    MAX_VOLATILITY = 100.0
    clamped = max(0.0, min(volatility_pct, MAX_VOLATILITY))
    return 1.0 - (clamped / MAX_VOLATILITY)


def _normalize_liquidity(liquidity_score: float) -> float:
    """
    Normalize a 0–100 liquidity score to a 0–1 value.

    score = clamp(liquidity_score / 100.0, 0, 1)
    """
    return max(0.0, min(liquidity_score / 100.0, 1.0))


def compute_score(metrics: dict, weights: TradabilityWeights) -> float:
    """
    Compute a composite tradability score in [0, 1] from extracted metrics and weights.

    Each metric is normalized to [0, 1] and then combined as a weighted sum,
    divided by the total weight to produce a final score in [0, 1].

    Formula:
      score = (
          w_spread   * norm_spread   +
          w_volume   * norm_volume   +
          w_slippage * norm_slippage +
          w_volatility * norm_volatility +
          w_liquidity * norm_liquidity
      ) / (w_spread + w_volume + w_slippage + w_volatility + w_liquidity)

    If total weight is zero, returns 0.0.
    """
    norm_spread = _normalize_spread(metrics["spread_pct"])
    norm_volume = _normalize_volume(metrics["volume_24h"])
    norm_slippage = _normalize_slippage(metrics["slippage_pct"])
    norm_volatility = _normalize_volatility(metrics["volatility_pct"])
    norm_liquidity = _normalize_liquidity(metrics["liquidity_score"])

    total_weight = (
        weights.spread_weight
        + weights.volume_weight
        + weights.slippage_weight
        + weights.volatility_weight
        + weights.liquidity_weight
    )

    if total_weight == 0.0:
        return 0.0

    weighted_sum = (
        weights.spread_weight * norm_spread
        + weights.volume_weight * norm_volume
        + weights.slippage_weight * norm_slippage
        + weights.volatility_weight * norm_volatility
        + weights.liquidity_weight * norm_liquidity
    )

    return weighted_sum / total_weight


def score_trade(trade: dict, weights: TradabilityWeights) -> ScoredTrade:
    """
    Score a single trade dictionary and return a ScoredTrade instance.

    The trade dict must contain an 'id' field (str). All metric fields are optional.
    """
    metrics = extract_metrics(trade)
    score = compute_score(metrics, weights)
    return ScoredTrade(
        id=str(trade.get("id", "")),
        score=round(score, 6),
        spread_pct=metrics["spread_pct"],
        volume_24h=metrics["volume_24h"],
        slippage_pct=metrics["slippage_pct"],
        volatility_pct=metrics["volatility_pct"],
        liquidity_score=metrics["liquidity_score"],
    )


def rank_trades(
    trades: List[dict],
    weights: Optional[TradabilityWeights] = None,
    top_n: Optional[int] = None,
) -> List[ScoredTrade]:
    """
    Score and rank a list of raw trade dictionaries by tradability score (descending).

    Parameters
    ----------
    trades:
        List of raw trade dicts, each expected to have an 'id' field and optional
        metric fields (spread_pct, volume_24h, slippage_pct, volatility_pct,
        liquidity_score).
    weights:
        TradabilityWeights instance controlling the relative importance of each
        metric. If None, defaults are loaded from application settings.
    top_n:
        If provided, return only the top N trades by score. If None or greater
        than the number of trades, all trades are returned.

    Returns
    -------
    List[ScoredTrade] sorted by score descending, optionally truncated to top_n.
    """
    if weights is None:
        weights = TradabilityWeights(
            spread_weight=settings.TRADABILITY_WEIGHT_SPREAD,
            volume_weight=settings.TRADABILITY_WEIGHT_VOLUME,
            slippage_weight=settings.TRADABILITY_WEIGHT_SLIPPAGE,
            volatility_weight=settings.TRADABILITY_WEIGHT_VOLATILITY,
            liquidity_weight=settings.TRADABILITY_WEIGHT_LIQUIDITY,
        )

    scored = [score_trade(trade, weights) for trade in trades]
    scored.sort(key=lambda t: t.score, reverse=True)

    if top_n is not None and top_n > 0:
        scored = scored[:top_n]

    return scored