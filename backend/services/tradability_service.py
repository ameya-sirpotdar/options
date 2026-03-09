from typing import Any, Optional
import math


WEIGHT_DELTA = 0.30
WEIGHT_THETA = 0.25
WEIGHT_IV = 0.25
WEIGHT_PREMIUM = 0.20

IV_IDEAL_LOW = 0.20
IV_IDEAL_HIGH = 0.50


def extract_metrics(row: dict[str, Any]) -> dict[str, Optional[float]]:
    """
    Extract tradability-relevant metrics from an Azure Table Storage options row.

    Parameters
    ----------
    row:
        A dictionary representing a single row from Azure Table Storage.
        Expected keys (all optional / may be missing or None):
            - delta   : float, option delta (-1.0 to 1.0)
            - theta   : float, option theta (typically negative, daily decay)
            - iv      : float, implied volatility as a decimal (e.g. 0.30 = 30 %)
            - premium : float, option premium in dollars

    Returns
    -------
    dict with keys ``delta``, ``theta``, ``iv``, ``premium``.
    Missing or non-numeric values are returned as ``None``.
    """
    metrics: dict[str, Optional[float]] = {}

    for field in ("delta", "theta", "iv", "premium"):
        raw = row.get(field)
        if raw is None:
            metrics[field] = None
        else:
            try:
                metrics[field] = float(raw)
            except (TypeError, ValueError):
                metrics[field] = None

    return metrics


def _score_delta(delta: Optional[float]) -> float:
    """
    Score the delta component.

    Ideal delta for a short-premium strategy is around ±0.30.
    We reward values close to 0.30 (absolute) and penalise extremes.
    Score is in [0.0, 1.0].
    """
    if delta is None or not math.isfinite(delta):
        return 0.0

    abs_delta = abs(delta)
    # Clamp to [0, 1]
    abs_delta = max(0.0, min(1.0, abs_delta))

    # Peak score at 0.30; linear fall-off to 0 at 0.0 and 1.0
    if abs_delta <= 0.30:
        return abs_delta / 0.30
    else:
        return (1.0 - abs_delta) / 0.70


def _score_theta(theta: Optional[float]) -> float:
    """
    Score the theta component.

    Theta is typically negative (time decay works for the option seller).
    A more-negative theta means faster premium decay – desirable for sellers.
    We normalise against a reference of -0.10 (10 cents/day) as a "good" value.
    Score is in [0.0, 1.0].
    """
    if theta is None or not math.isfinite(theta):
        return 0.0

    # Positive theta is unusual / undesirable – score 0
    if theta >= 0.0:
        return 0.0

    # Reference: -0.10 per day → score 1.0; saturates beyond that
    reference = -0.10
    ratio = theta / reference  # both negative → positive ratio
    return min(1.0, max(0.0, ratio))


def _score_iv(iv: Optional[float]) -> float:
    """
    Score the implied-volatility component.

    IV in the ideal band [20 %, 50 %] scores 1.0.
    Outside that band the score falls off linearly.
    Score is in [0.0, 1.0].
    """
    if iv is None or not math.isfinite(iv) or iv < 0.0:
        return 0.0

    if IV_IDEAL_LOW <= iv <= IV_IDEAL_HIGH:
        return 1.0

    if iv < IV_IDEAL_LOW:
        # Linear from 0 at iv=0 to 1 at iv=IV_IDEAL_LOW
        return iv / IV_IDEAL_LOW

    # iv > IV_IDEAL_HIGH: linear from 1 at IV_IDEAL_HIGH to 0 at iv=1.0
    if iv >= 1.0:
        return 0.0
    return (1.0 - iv) / (1.0 - IV_IDEAL_HIGH)


def _score_premium(premium: Optional[float]) -> float:
    """
    Score the premium component.

    Higher premium is generally better (more credit received).
    We use a logarithmic scale normalised so that $1.00 premium → score 1.0.
    Premiums above $1.00 are capped at 1.0.
    Score is in [0.0, 1.0].
    """
    if premium is None or not math.isfinite(premium) or premium <= 0.0:
        return 0.0

    # log scale: log(1 + premium) / log(2)  → score 1.0 at premium = 1.0
    score = math.log1p(premium) / math.log1p(1.0)
    return min(1.0, max(0.0, score))


def compute_score(metrics: dict[str, Optional[float]]) -> float:
    """
    Compute a weighted tradability score in [0.0, 1.0] from extracted metrics.

    Parameters
    ----------
    metrics:
        Dictionary as returned by :func:`extract_metrics`.

    Returns
    -------
    float
        Weighted composite score.  Higher is better.
    """
    score = (
        WEIGHT_DELTA   * _score_delta(metrics.get("delta"))
        + WEIGHT_THETA * _score_theta(metrics.get("theta"))
        + WEIGHT_IV    * _score_iv(metrics.get("iv"))
        + WEIGHT_PREMIUM * _score_premium(metrics.get("premium"))
    )
    return round(score, 6)


def rank_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Rank a list of options rows by their tradability score (descending).

    Each output element is the original row dict augmented with two keys:
        - ``metrics``          : dict returned by :func:`extract_metrics`
        - ``tradability_score``: float returned by :func:`compute_score`

    Parameters
    ----------
    rows:
        List of raw option row dicts (e.g. from Azure Table Storage).

    Returns
    -------
    list
        Rows sorted by ``tradability_score`` descending (best first).
    """
    scored: list[dict[str, Any]] = []

    for row in rows:
        metrics = extract_metrics(row)
        score = compute_score(metrics)
        enriched = dict(row)
        enriched["metrics"] = metrics
        enriched["tradability_score"] = score
        scored.append(enriched)

    scored.sort(key=lambda r: r["tradability_score"], reverse=True)
    return scored


def best_candidate(rows: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """
    Return the single best trade candidate from a list of options rows.

    Parameters
    ----------
    rows:
        List of raw option row dicts.

    Returns
    -------
    The highest-scoring row (augmented with ``metrics`` and
    ``tradability_score``), or ``None`` if *rows* is empty.
    """
    ranked = rank_candidates(rows)
    return ranked[0] if ranked else None