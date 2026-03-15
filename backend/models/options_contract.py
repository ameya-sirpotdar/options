from pydantic import BaseModel
from typing import Literal, Optional


class OptionsContract(BaseModel):
    symbol: str
    option_type: Optional[Literal['call', 'put', 'CALL', 'PUT']] = None
    description: Optional[str] = None
    exchange_name: Optional[str] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    mark: Optional[float] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    bid_ask_size: Optional[str] = None
    last_size: Optional[int] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    open_price: Optional[float] = None
    close_price: Optional[float] = None
    total_volume: Optional[int] = None
    trade_date: Optional[int] = None
    quote_time_in_long: Optional[int] = None
    net_change: Optional[float] = None
    volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None
    open_interest: Optional[int] = None
    time_value: Optional[float] = None
    theoretical_option_value: Optional[float] = None
    theoretical_volatility: Optional[float] = None
    strike_price: Optional[float] = None
    expiration_date: Optional[int] = None
    days_to_expiration: Optional[int] = None
    expiration_type: Optional[str] = None
    last_trading_day: Optional[int] = None
    multiplier: Optional[float] = None
    settlement_type: Optional[str] = None
    deliverable_note: Optional[str] = None
    percent_change: Optional[float] = None
    mark_change: Optional[float] = None
    mark_percent_change: Optional[float] = None
    intrinsic_value: Optional[float] = None
    extrinsic_value: Optional[float] = None
    option_root: Optional[str] = None
    exercise_type: Optional[str] = None
    high_52_week: Optional[float] = None
    low_52_week: Optional[float] = None
    status: Optional[str] = None
    in_the_money: Optional[bool] = None
    non_standard: Optional[bool] = None
    mini: Optional[bool] = None
    penny_pilot: Optional[bool] = None
    option_deliverables_list: Optional[list] = None
