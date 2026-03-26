"""
Synthetic demand data generator for SmartGrowth AI forecasting module.
Generates realistic daily demand with trend, seasonality, promotions,
holidays, marketing spend, and noise — ready for ARIMA / Prophet / N-BEATS.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ForecastingConfig:
    """Central config for data generation and model training."""
    start_date: str = "2022-01-01"
    periods: int = 730          # 2 years of daily data
    base_demand: float = 500.0
    trend_per_day: float = 0.12
    noise_std: float = 30.0
    seed: int = 42

    # Seasonality amplitudes
    weekly_amplitude: float = 60.0
    yearly_amplitude: float = 120.0

    # Promotion / holiday params
    promo_lift_pct: float = 0.25
    holiday_lift_pct: float = 0.40

    # Model output paths (relative to repo root)
    model_dir: str = "ml_models/forecasting/artifacts"

    # Forecast horizon (days)
    forecast_horizon: int = 30


# Indian / global holidays that affect e-commerce demand
_HOLIDAYS = {
    "New Year":      ("01-01",),
    "Valentine's":   ("02-14",),
    "Holi":          ("03-25",),   # approximate fixed date for synthetic data
    "Independence":  ("08-15",),
    "Dussehra":      ("10-12",),
    "Diwali":        ("11-12",),   # approximate
    "Christmas":     ("12-25",),
    "New Year Eve":  ("12-31",),
}

# Month-day strings that get a promotional lift
_PROMO_DAYS = {
    "Big Sale Jan":  ("01-26",),   # Republic Day sale
    "Summer Sale":   ("05-15",),
    "Independence Sale": ("08-15",),
    "Festive Sale":  ("10-02",),
    "Black Friday":  ("11-29",),
    "Cyber Monday":  ("12-02",),
}


def _is_holiday(date: pd.Timestamp) -> bool:
    md = date.strftime("%m-%d")
    return any(md in days for days in _HOLIDAYS.values())


def _is_promo(date: pd.Timestamp) -> bool:
    md = date.strftime("%m-%d")
    return any(md in days for days in _PROMO_DAYS.values())


def generate_daily_demand(config: Optional[ForecastingConfig] = None) -> pd.DataFrame:
    """
    Generate a realistic synthetic daily demand DataFrame.

    Returns columns:
        ds          - date (datetime64)
        y           - demand units (float)
        day_of_week - 0=Mon … 6=Sun
        month       - 1-12
        is_weekend  - bool
        is_holiday  - bool
        is_promo    - bool
        marketing_spend - float (correlated with demand)
        discount_pct    - float 0-0.4
        avg_order_value - float
        revenue         - float (y * avg_order_value * (1 - discount_pct))
    """
    if config is None:
        config = ForecastingConfig()

    rng = np.random.default_rng(config.seed)
    dates = pd.date_range(start=config.start_date, periods=config.periods, freq="D")
    t = np.arange(config.periods)

    # ── Base components ──────────────────────────────────────────────────────
    trend = config.base_demand + config.trend_per_day * t

    # Weekly seasonality: higher on Fri/Sat/Sun
    day_of_week = dates.dayofweek.values   # 0=Mon
    weekly = config.weekly_amplitude * np.sin(2 * np.pi * day_of_week / 7 - np.pi / 2)

    # Yearly seasonality: Q4 peak (Oct-Dec)
    yearly = config.yearly_amplitude * np.sin(2 * np.pi * t / 365 - np.pi)

    noise = rng.normal(0, config.noise_std, config.periods)

    demand = trend + weekly + yearly + noise

    # ── Event lifts ──────────────────────────────────────────────────────────
    is_holiday = np.array([_is_holiday(d) for d in dates])
    is_promo = np.array([_is_promo(d) for d in dates])

    demand = np.where(is_holiday, demand * (1 + config.holiday_lift_pct), demand)
    demand = np.where(is_promo,   demand * (1 + config.promo_lift_pct),   demand)

    # Carry-over effect: 50% lift on day after a promo/holiday
    carry = np.roll(is_holiday | is_promo, 1).astype(float) * 0.5
    carry[0] = 0
    demand = demand * (1 + carry * 0.15)

    demand = np.clip(demand, 50, None)  # floor at 50 units

    # ── Derived columns ──────────────────────────────────────────────────────
    is_weekend = (day_of_week >= 5).astype(bool)
    month = dates.month.values

    # Marketing spend: baseline + random bursts
    marketing_spend = 2000 + rng.normal(0, 300, config.periods)
    marketing_spend += is_promo * 5000
    marketing_spend += is_holiday * 3000
    marketing_spend = np.clip(marketing_spend, 500, None)

    # Discount: higher on promo days
    discount_pct = np.clip(
        rng.uniform(0.02, 0.15, config.periods)
        + is_promo * 0.20
        + is_holiday * 0.10,
        0, 0.40
    )

    avg_order_value = 850 + rng.normal(0, 80, config.periods) + is_weekend * 50

    revenue = demand * avg_order_value * (1 - discount_pct)

    df = pd.DataFrame({
        "ds":               dates,
        "y":                demand.round(2),
        "day_of_week":      day_of_week,
        "month":            month,
        "is_weekend":       is_weekend,
        "is_holiday":       is_holiday,
        "is_promo":         is_promo,
        "marketing_spend":  marketing_spend.round(2),
        "discount_pct":     discount_pct.round(4),
        "avg_order_value":  avg_order_value.round(2),
        "revenue":          revenue.round(2),
    })

    return df


if __name__ == "__main__":
    df = generate_daily_demand()
    print(df.head(10).to_string())
    print(f"\nShape: {df.shape}")
    print(f"Date range: {df['ds'].min().date()} → {df['ds'].max().date()}")
    print(f"Demand stats:\n{df['y'].describe().round(1)}")