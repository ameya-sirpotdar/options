from datetime import date
from typing import Optional


def compute_days_to_expiration(expiration_date: date, today: Optional[date] = None) -> int:
    """
    Compute the number of calendar days between today and expiration_date.

    Parameters
    ----------
    expiration_date : date
        The option's expiration date.
    today : date, optional
        The date from which to measure. Defaults to today (date.today()).

    Returns
    -------
    int
        Number of days until expiration. Negative if expiration_date is in the past.
    """
    if today is None:
        today = date.today()

    delta = (expiration_date - today).days
    return delta


def compute_annualized_roi(
    premium: float,
    strike: float,
    days_to_expiration: int,
) -> Optional[float]:
    """
    Compute the annualized return on investment for a Cash Covered Put (CCP).

    The formula is:
        annualized_roi = (premium / strike) * (365 / days_to_expiration)

    Parameters
    ----------
    premium : float
        The option premium received (per share, not per contract).
    strike : float
        The strike price of the put option.
    days_to_expiration : int
        Number of calendar days until the option expires.

    Returns
    -------
    float
        Annualized ROI as a decimal (e.g. 0.15 means 15%).

    Raises
    ------
    ValueError
        If strike is zero/negative or days_to_expiration is zero/negative.
    """
    if days_to_expiration <= 0:
        raise ValueError("days_to_expiration must be a positive integer.")

    if strike <= 0:
        raise ValueError("strike must be a positive number.")

    roi = (premium / strike) * (365.0 / days_to_expiration)
    return roi


def enrich_put_options_with_roi(
    put_options: list[dict],
    today: Optional[date] = None,
) -> list[dict]:
    """
    Enrich a list of put option records with annualized_roi and days_to_expiration.

    Each record is expected to be a dict containing at least:
        - "expiration_date": a date object (or ISO-format string "YYYY-MM-DD")
        - "strike": numeric strike price
        - "bid": numeric bid price used as the conservative premium estimate
        - "option_type": string, only records with "put" (case-insensitive) are enriched

    Non-put records are copied unchanged into the returned list.
    The function returns a new list of new dicts (originals are not mutated).

    Parameters
    ----------
    put_options : list[dict]
        List of option data dictionaries.
    today : date, optional
        Reference date for DTE calculation. Defaults to date.today().

    Returns
    -------
    list[dict]
        A new list of dicts; put records are enriched with
        "days_to_expiration" and "annualized_roi".
    """
    if today is None:
        today = date.today()

    enriched = []

    for option in put_options:
        record = dict(option)

        if str(record.get("option_type", "")).lower() != "put":
            enriched.append(record)
            continue

        expiration_raw = record.get("expiration_date")

        if expiration_raw is None:
            record["days_to_expiration"] = 0
            record["annualized_roi"] = None
            enriched.append(record)
            continue

        if isinstance(expiration_raw, str):
            try:
                expiration_date = date.fromisoformat(expiration_raw)
            except ValueError:
                record["days_to_expiration"] = 0
                record["annualized_roi"] = None
                enriched.append(record)
                continue
        elif isinstance(expiration_raw, date):
            expiration_date = expiration_raw
        else:
            record["days_to_expiration"] = 0
            record["annualized_roi"] = None
            enriched.append(record)
            continue

        dte = compute_days_to_expiration(expiration_date, today)
        record["days_to_expiration"] = dte

        strike = record.get("strike")
        premium = record.get("bid")

        if strike is None or premium is None:
            record["annualized_roi"] = None
            enriched.append(record)
            continue

        try:
            strike = float(strike)
            premium = float(premium)
        except (TypeError, ValueError):
            record["annualized_roi"] = None
            enriched.append(record)
            continue

        try:
            record["annualized_roi"] = compute_annualized_roi(premium, strike, dte)
        except ValueError:
            record["annualized_roi"] = None

        enriched.append(record)

    return enriched