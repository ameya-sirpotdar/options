from datetime import date, timedelta

import pytest

from backend.services.schwab_service import filter_contracts, _is_weekly_expiry


def _make_chain(expiry: str, strike: str, delta: float) -> dict:
    return {
        "putExpDateMap": {
            f"{expiry}:5": {
                strike: [{"delta": delta, "symbol": f"NVDA_{expiry}_{strike}P"}]
            }
        }
    }


def weekly_expiry() -> str:
    return (date.today() + timedelta(days=4)).isoformat()


def distant_expiry() -> str:
    return (date.today() + timedelta(days=30)).isoformat()


def test_filter_keeps_weekly_near_delta():
    chain = _make_chain(weekly_expiry(), "820", -0.30)
    result = filter_contracts(chain)
    assert len(result) == 1


def test_filter_drops_distant_expiry():
    chain = _make_chain(distant_expiry(), "820", -0.30)
    result = filter_contracts(chain)
    assert len(result) == 0


def test_filter_drops_far_delta():
    chain = _make_chain(weekly_expiry(), "820", -0.10)
    result = filter_contracts(chain)
    assert len(result) == 0


def test_filter_keeps_delta_at_boundary():
    chain = _make_chain(weekly_expiry(), "820", -0.25)
    result = filter_contracts(chain)
    assert len(result) == 1


def test_filter_drops_delta_just_outside_boundary():
    chain = _make_chain(weekly_expiry(), "820", -0.24)
    result = filter_contracts(chain)
    assert len(result) == 0


def test_filter_attaches_expiry_and_strike():
    exp = weekly_expiry()
    chain = _make_chain(exp, "820", -0.30)
    result = filter_contracts(chain)
    assert result[0]["expiry"] == exp
    assert result[0]["strike"] == 820.0


def test_filter_empty_chain():
    result = filter_contracts({"putExpDateMap": {}})
    assert result == []


def test_is_weekly_expiry_today():
    assert _is_weekly_expiry(date.today().isoformat()) is True


def test_is_weekly_expiry_past():
    assert _is_weekly_expiry((date.today() - timedelta(days=1)).isoformat()) is False


def test_is_weekly_expiry_beyond_window():
    assert _is_weekly_expiry((date.today() + timedelta(days=9)).isoformat()) is False
