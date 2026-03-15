"""
Trades comparison and scoring service.

Consolidates tradability scoring (formerly tradability_service.py) with
trade comparison logic into a single unified service.
"""
import math
from datetime import date
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Weights and constants (from tradability_service.py)
# ---------------------------------------------------------------------------

WEIGHT_DELTA = 0.30
WEIGHT_THETA = 0.25
WEIGHT_IV = 0.25
WEIGHT_PREMIUM = 0.20

IV_IDEAL_LOW = 0.20
IV_IDEAL_HIGH = 0.50


# ---------------------------------------------------------------------------
# Module-level scoring functions (from tradability_service.py)
# ---------------------------------------------------------------------------

def extract_metrics(row: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract tradability-relevant metrics from an options row (strict version).

    Raises ValueError/TypeError if any required field is missing or non-numeric.
    """
    metrics: Dict[str, float] = {}

    for field in ("delta", "theta", "iv", "premium"):
        raw = row[field]  # raises KeyError if missing
        if raw is None:
            raise TypeError(f"Field '{field}' must not be None")
        metrics[field] = float(raw)  # raises TypeError/ValueError if non-numeric

    return metrics


def _score_delta(delta: Optional[float]) -> float:
    """Higher absolute delta → higher score. Linear [0, 1]."""
    if delta is None or not math.isfinite(delta):
        return 0.0
    return min(1.0, abs(delta))


def _score_theta(theta: Optional[float]) -> float:
    """Less negative theta (closer to 0) → higher score."""
    if theta is None or not math.isfinite(theta):
        return 0.0
    # theta >= 0 is unusual but still score it
    return max(0.0, min(1.0, 1.0 - abs(theta) / 0.10))


def _score_iv(iv: Optional[float]) -> float:
    if iv is None or not math.isfinite(iv) or iv < 0.0:
        return 0.0
    if IV_IDEAL_LOW <= iv <= IV_IDEAL_HIGH:
        return 1.0
    if iv < IV_IDEAL_LOW:
        return iv / IV_IDEAL_LOW
    if iv >= 1.0:
        return 0.0
    return (1.0 - iv) / (1.0 - IV_IDEAL_HIGH)


def _score_premium(premium: Optional[float]) -> float:
    if premium is None or not math.isfinite(premium) or premium < 0.0:
        return 0.0
    # Saturates at premium ~= 10.0
    score = math.log1p(premium) / math.log1p(10.0)
    return min(1.0, max(0.0, score))


def compute_score(metrics: Dict[str, Optional[float]]) -> float:
    """Compute a weighted tradability score in [0.0, 1.0] from extracted metrics."""
    score = (
        WEIGHT_DELTA * _score_delta(metrics["delta"])
        + WEIGHT_THETA * _score_theta(metrics["theta"])
        + WEIGHT_IV * _score_iv(metrics["iv"])
        + WEIGHT_PREMIUM * _score_premium(metrics["premium"])
    )
    return round(score, 6)


def rank_candidates(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank a list of options rows by their tradability score (descending).

    Each output element is the original row dict augmented with:
        - ``metrics``: dict returned by :func:`extract_metrics`
        - ``score``: float returned by :func:`compute_score`
    """
    scored: List[Dict[str, Any]] = []

    for row in rows:
        metrics = extract_metrics(row)  # may raise
        score = compute_score(metrics)
        enriched = dict(row)
        enriched["metrics"] = metrics
        enriched["score"] = score
        scored.append(enriched)

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored


def best_candidate(rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return the single best trade candidate from a list of options rows."""
    ranked = rank_candidates(rows)
    return ranked[0] if ranked else None


# ---------------------------------------------------------------------------
# TradesComparisonService class
# ---------------------------------------------------------------------------

class TradesComparisonService:
    """
    Service for comparing and scoring options trades.
    Operates on raw contract dicts from the Schwab API.
    """

    # ------------------------------------------------------------------
    # Dict-based scoring (used by rank_contracts / score_contract)
    # ------------------------------------------------------------------

    def _compute_contract_metrics(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        """Compute raw metrics from a contract dict."""
        bid = contract.get("bid") or 0.0
        ask = contract.get("ask") or 0.0
        volume = contract.get("totalVolume") or contract.get("volume") or 0
        open_interest = contract.get("openInterest") or 0
        delta = contract.get("delta")
        spread = (ask - bid) if ask and bid else 0.0
        spread_pct = (spread / ask * 100.0) if ask and ask > 0 else 0.0
        return {
            "bid": bid,
            "ask": ask,
            "volume": volume,
            "open_interest": open_interest,
            "delta": delta,
            "spread": spread,
            "spread_pct": spread_pct,
            "days_to_expiration": contract.get("daysToExpiration") or 0,
            "implied_volatility": contract.get("volatility") or 0.0,
        }

    def _compute_contract_score(self, metrics: Dict[str, Any]) -> float:
        """Compute a 0-100 composite score from contract metrics."""
        score = 0.0

        # Spread score
        spread_pct = metrics.get("spread_pct", 0)
        if spread_pct < 5.0:
            score += 30.0
        elif spread_pct < 10.0:
            score += 15.0

        # Open interest
        oi = metrics.get("open_interest", 0)
        if oi >= 1000:
            score += 25.0
        elif oi >= 100:
            score += 12.0

        # Volume
        vol = metrics.get("volume", 0)
        if vol >= 500:
            score += 20.0
        elif vol >= 50:
            score += 10.0

        # Delta
        delta = metrics.get("delta")
        abs_delta = abs(delta) if delta is not None else 0.0
        if 0.3 <= abs_delta <= 0.7:
            score += 15.0
        elif 0.2 <= abs_delta < 0.3 or 0.7 < abs_delta <= 0.8:
            score += 7.0

        # DTE
        dte = metrics.get("days_to_expiration", 0)
        if 20 <= dte <= 60:
            score += 10.0
        elif 10 <= dte < 20 or 60 < dte <= 90:
            score += 5.0

        return max(0.0, min(100.0, score))

    def score_contract(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        """Score a single options contract dict. Returns dict with 'score' and 'metrics'."""
        metrics = self._compute_contract_metrics(contract)
        score = self._compute_contract_score(metrics)
        result = dict(contract)
        result["score"] = score
        result["metrics"] = metrics
        return result

    def _flatten_chain(self, chain: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten callExpDateMap and putExpDateMap into a flat list of contracts."""
        contracts = []
        for map_key in ("callExpDateMap", "putExpDateMap"):
            exp_map = chain.get(map_key) or {}
            for _exp_key, strikes in exp_map.items():
                if not isinstance(strikes, dict):
                    continue
                for _strike_key, contract_list in strikes.items():
                    if not isinstance(contract_list, list):
                        continue
                    for contract in contract_list:
                        if isinstance(contract, dict):
                            contracts.append(contract)
        return contracts

    def rank_contracts(self, chain: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Score and rank all contracts from an options chain dict (descending by score)."""
        contracts = self._flatten_chain(chain)
        scored = [self.score_contract(c) for c in contracts]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def get_top_trades(self, chain: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Return the top N scored contracts from an options chain dict."""
        ranked = self.rank_contracts(chain)
        return ranked[:limit]

    def calculate_ccp(self, contract: Dict[str, Any]) -> float:
        """Calculate cash-covered put probability score [0, 1] using delta."""
        delta = contract.get("delta")
        if delta is None:
            return 0.0
        return max(0.0, min(1.0, abs(delta)))

    def calculate_liquidity_score(self, contract: Dict[str, Any]) -> float:
        """Calculate a liquidity score [0, inf) from volume, open interest, and spread."""
        volume = contract.get("totalVolume") or contract.get("volume") or 0
        open_interest = contract.get("openInterest") or 0
        bid = contract.get("bid") or 0.0
        ask = contract.get("ask") or 0.0

        if volume == 0 and open_interest == 0:
            return 0.0

        # Normalize volume (0-1) and OI (0-1) with saturation at 10000
        vol_score = min(1.0, volume / 10000.0)
        oi_score = min(1.0, open_interest / 100000.0)

        # Spread score (tighter = better)
        if ask > 0:
            spread_pct = (ask - bid) / ask
            spread_score = max(0.0, 1.0 - spread_pct * 10)
        else:
            spread_score = 0.0

        return (vol_score + oi_score + spread_score) / 3.0

    def compare_contracts(
        self, contract_a: Dict[str, Any], contract_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare two contracts and return a dict with 'winner' and 'scores'."""
        score_a = self._compute_contract_score(self._compute_contract_metrics(contract_a))
        score_b = self._compute_contract_score(self._compute_contract_metrics(contract_b))

        if score_a > score_b:
            winner = "a"
        elif score_b > score_a:
            winner = "b"
        else:
            winner = "tie"

        return {
            "winner": winner,
            "scores": {"a": score_a, "b": score_b},
        }

    def compute_tradability_score(self, trades: List[Dict[str, Any]]) -> Optional[float]:
        """Return the highest tradability score from a list of trade dicts, or None."""
        if not trades:
            return None
        best: Optional[float] = None
        for trade in trades:
            try:
                metrics = extract_metrics(trade)
                score = compute_score(metrics)
                if best is None or score > best:
                    best = score
            except Exception:  # noqa: BLE001
                continue
        return best

    def rank_candidates(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank raw options rows by tradability score (delegates to module function)."""
        return rank_candidates(rows)

    def score_trades(self, options_data: Any) -> Any:
        """Score and rank options data (alias for rank_candidates)."""
        if isinstance(options_data, list):
            return rank_candidates(options_data)
        return options_data

    @staticmethod
    def enrich_put_options_with_roi(
        put_options: list,
        today: Optional[date] = None,
    ) -> list:
        """Enrich put options with annualized_roi and days_to_expiration."""
        from backend.services.schwab_service import enrich_put_options_with_roi as _enrich
        return _enrich(put_options, today=today)
