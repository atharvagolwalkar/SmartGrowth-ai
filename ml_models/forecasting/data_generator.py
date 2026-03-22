"""Synthetic demand data generation for the forecasting module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class DailyDemandGeneratorConfig:
    """Controls the synthetic time-series demand shape."""

    start_date: str = "2022-01-01"
    end_date: str = "2024-12-31"
    base_orders: int = 240
    weekly_amplitude: float = 45.0
    yearly_amplitude: float = 30.0
    trend_per_day: float = 0.08
    marketing_spend_base: float = 1800.0
    marketing_spend_noise: float = 220.0
    avg_order_value_base: float = 82.0
    random_seed: int = 42


def _holiday_calendar(year: int) -> set[pd.Timestamp]:
    """Return a compact set of high-impact retail dates."""
    return {
        pd.Timestamp(year=year, month=1, day=1),
        pd.Timestamp(year=year, month=2, day=14),
        pd.Timestamp(year=year, month=8, day=15),
        pd.Timestamp(year=year, month=10, day=24),
        pd.Timestamp(year=year, month=11, day=1),
        pd.Timestamp(year=year, month=11, day=27),
        pd.Timestamp(year=year, month=12, day=25),
        pd.Timestamp(year=year, month=12, day=31),
    }


def generate_synthetic_daily_demand(
    config: Optional[DailyDemandGeneratorConfig] = None,
) -> pd.DataFrame:
    """Generate a realistic daily demand dataset with business drivers."""

    config = config or DailyDemandGeneratorConfig()
    rng = np.random.default_rng(config.random_seed)
    dates = pd.date_range(config.start_date, config.end_date, freq="D")
    df = pd.DataFrame({"demand_date": dates})

    day_index = np.arange(len(df))
    day_of_week = df["demand_date"].dt.dayofweek
    month = df["demand_date"].dt.month
    week_of_year = df["demand_date"].dt.isocalendar().week.astype(int)
    is_weekend = day_of_week >= 5

    holiday_dates = {
        holiday
        for year in df["demand_date"].dt.year.unique()
        for holiday in _holiday_calendar(int(year))
    }
    is_holiday = df["demand_date"].isin(holiday_dates)

    promo_cycle = (day_index % 28) < 5
    q4_boost = month.isin([10, 11, 12]) & ((day_index % 21) < 6)
    is_promotion = promo_cycle | q4_boost

    marketing_spend = (
        config.marketing_spend_base
        + np.where(is_promotion, 950.0, 0.0)
        + np.where(is_holiday, 450.0, 0.0)
        + rng.normal(0, config.marketing_spend_noise, len(df))
    ).clip(min=400.0)

    discount_pct = (
        np.where(is_promotion, rng.uniform(0.08, 0.22, len(df)), rng.uniform(0.0, 0.05, len(df)))
        + np.where(is_holiday, 0.03, 0.0)
    ).clip(0, 0.30)

    avg_order_value = (
        config.avg_order_value_base
        + month.map({
            1: -4.0,
            2: -3.0,
            3: -1.5,
            4: 0.0,
            5: 1.5,
            6: 2.5,
            7: 2.0,
            8: 2.5,
            9: 4.0,
            10: 6.0,
            11: 8.5,
            12: 10.0,
        }).astype(float)
        + np.where(is_promotion, -6.0, 0.0)
        + rng.normal(0, 2.5, len(df))
    ).clip(lower=45.0)

    weekly_pattern = config.weekly_amplitude * np.sin(2 * np.pi * day_of_week / 7)
    yearly_pattern = config.yearly_amplitude * np.cos(2 * np.pi * df["demand_date"].dt.dayofyear / 365.25)
    holiday_lift = np.where(is_holiday, 110.0, 0.0)
    promotion_lift = np.where(is_promotion, 75.0, 0.0)
    weekend_lift = np.where(is_weekend, 28.0, 0.0)
    marketing_lift = (marketing_spend - config.marketing_spend_base) / 42.0
    discount_lift = discount_pct * 260.0
    noise = rng.normal(0, 18.0, len(df))

    orders = (
        config.base_orders
        + (config.trend_per_day * day_index)
        + weekly_pattern
        + yearly_pattern
        + holiday_lift
        + promotion_lift
        + weekend_lift
        + marketing_lift
        + discount_lift
        + noise
    )
    orders = np.round(np.clip(orders, a_min=35, a_max=None)).astype(int)
    revenue = np.round(orders * avg_order_value, 2)

    df["orders"] = orders
    df["revenue"] = revenue
    df["avg_order_value"] = np.round(avg_order_value, 2)
    df["marketing_spend"] = np.round(marketing_spend, 2)
    df["discount_pct"] = np.round(discount_pct, 4)
    df["is_promotion"] = is_promotion.astype(bool)
    df["is_holiday"] = is_holiday.astype(bool)
    df["day_of_week"] = day_of_week.astype(int)
    df["week_of_year"] = week_of_year.astype(int)
    df["month"] = month.astype(int)
    df["is_weekend"] = is_weekend.astype(bool)

    return df[
        [
            "demand_date",
            "orders",
            "revenue",
            "avg_order_value",
            "marketing_spend",
            "discount_pct",
            "is_promotion",
            "is_holiday",
            "day_of_week",
            "week_of_year",
            "month",
            "is_weekend",
        ]
    ]
