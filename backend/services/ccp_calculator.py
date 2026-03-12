from datetime import date
from typing import Optional


def compute_days_to_expiration(expiration_date: date, reference_date: Optional[date] = None) -> int:
    """
    Compute the number of calendar days between reference_date and expiration_date.

    Parameters
    ----------
    expiration_date : date
        The option's expiration date.
    reference_date : date, optional
        The date from which to measure. Defaults to today (date.today()).

    Returns
    -------
    int
        Number of days until expiration. Returns 0 if expiration_date is in the past.
    """
    if reference_date is None:
        reference_date = date.today()

    delta = (expiration_date - reference_date).days
    return max(delta, 0)


def compute_annualized_roi(
    premium: float,
    strike_price: float,
    days_to_expiration: int,
) -> Optional[float]:
    """
    Compute the annualized return on investment for a Cash Covered Put (CCP).

    The formula is:
        annualized_roi = (premium / strike_price) * (365 / days_to_expiration)

    Parameters
    ----------
    premium : float
        The option premium received (per share, not per contract).
    strike_price : float
        The strike price of the put option.
    days_to_expiration : int
        Number of calendar days until the option expires.

    Returns
    -------
    float or None
        Annualized ROI as a decimal (e.g. 0.15 means 15%). Returns None if
        strike_price is zero or days_to_expiration is zero, to avoid
        division-by-zero errors.
    """
    if strike_price == 0 or days_to_expiration == 0:
        return None

    if premium < 0 or strike_price < 0:
        return None

    roi = (premium / strike_price) * (365.0 / days_to_expiration)
    return roi


def enrich_put_options_with_roi(
    put_options: list[dict],
    reference_date: Optional[date] = None,
) -> list[dict]:
    """
    Enrich a list of put option records with annualized_roi and days_to_expiration.

    Each record is expected to be a dict containing at least:
        - "expiration_date": a date object (or ISO-format string "YYYY-MM-DD")
        - "strike": numeric strike price
        - "bid": numeric bid price used as the conservative premium estimate

    The function adds two keys to each record (mutating the dicts in-place and
    also returning the list for convenience):
        - "days_to_expiration": int
        - "annualized_roi": float or None

    Parameters
    ----------
    put_options : list[dict]
        List of put option data dictionaries.
    reference_date : date, optional
        Reference date for DTE calculation. Defaults to date.today().

    Returns
    -------
    list[dict]
        The same list with each dict enriched in-place.
    """
    if reference_date is None:
        reference_date = date.today()

    for option in put_options:
        expiration_raw = option.get("expiration_date")

        if expiration_raw is None:
            option["days_to_expiration"] = 0
            option["annualized_roi"] = None
            continue

        if isinstance(expiration_raw, str):
            try:
                expiration_date = date.fromisoformat(expiration_raw)
            except ValueError:
                option["days_to_expiration"] = 0
                option["annualized_roi"] = None
                continue
        elif isinstance(expiration_raw, date):
            expiration_date = expiration_raw
        else:
            option["days_to_expiration"] = 0
            option["annualized_roi"] = None
            continue

        dte = compute_days_to_expiration(expiration_date, reference_date)
        option["days_to_expiration"] = dte

        strike = option.get("strike")
        premium = option.get("bid")

        if strike is None or premium is None:
            option["annualized_roi"] = None
            continue

        try:
            strike = float(strike)
            premium = float(premium)
        except (TypeError, ValueError):
            option["annualized_roi"] = None
            continue

        option["annualized_roi"] = compute_annualized_roi(premium, strike, dte)

    return put_options