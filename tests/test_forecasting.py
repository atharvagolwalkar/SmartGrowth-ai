"""Tests for forecasting dataset generation and loading."""

import os
import sys

import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.loader import load_daily_demand_data
from ml_models.forecasting import DailyDemandGeneratorConfig, generate_synthetic_daily_demand


def test_generate_synthetic_daily_demand_structure():
    config = DailyDemandGeneratorConfig(start_date="2024-01-01", end_date="2024-01-31", random_seed=7)
    df = generate_synthetic_daily_demand(config)

    assert len(df) == 31
    assert list(df.columns) == [
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
    assert pd.api.types.is_datetime64_any_dtype(df["demand_date"])
    assert (df["orders"] >= 0).all()
    assert (df["revenue"] >= 0).all()
    assert df["is_promotion"].dtype == bool


def test_generate_synthetic_daily_demand_reproducible():
    config = DailyDemandGeneratorConfig(start_date="2024-01-01", end_date="2024-01-10", random_seed=11)
    df_one = generate_synthetic_daily_demand(config)
    df_two = generate_synthetic_daily_demand(config)

    pd.testing.assert_frame_equal(df_one, df_two)


def test_load_daily_demand_data_into_database():
    db_path = os.path.join(os.getcwd(), "forecast_test.db")
    csv_path = os.path.join(os.getcwd(), "daily_demand_test.csv")
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        if os.path.exists(csv_path):
            os.remove(csv_path)

        engine = create_engine(f"sqlite:///{db_path}")
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE fact_daily_demand (
                        demand_date DATE PRIMARY KEY,
                        orders INTEGER NOT NULL,
                        revenue REAL NOT NULL,
                        avg_order_value REAL NOT NULL,
                        marketing_spend REAL NOT NULL,
                        discount_pct REAL NOT NULL,
                        is_promotion BOOLEAN NOT NULL,
                        is_holiday BOOLEAN NOT NULL,
                        day_of_week INTEGER NOT NULL,
                        week_of_year INTEGER NOT NULL,
                        month INTEGER NOT NULL,
                        is_weekend BOOLEAN NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )

        success, row_count = load_daily_demand_data(engine, csv_output_path=csv_path)

        assert success is True
        assert row_count > 1000
        assert os.path.exists(csv_path)

        with engine.connect() as conn:
            loaded_count = conn.execute(text("SELECT COUNT(*) FROM fact_daily_demand")).scalar_one()
        assert loaded_count == row_count
        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
        if os.path.exists(csv_path):
            os.remove(csv_path)
