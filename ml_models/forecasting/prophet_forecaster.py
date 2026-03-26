"""
Facebook Prophet forecaster for SmartGrowth AI.

Prophet handles:
  - Trend with automatic changepoint detection
  - Weekly + yearly seasonality
  - Custom holiday effects (Indian e-commerce calendar)
  - External regressors: marketing_spend, discount_pct, is_promo
  - Uncertainty intervals (Monte Carlo sampling)

This is the "business-friendly" middle layer between ARIMA and N-BEATS.
It's interpretable, robust to missing data, and easy to explain to stakeholders.
"""

from __future__ import annotations

import json
import logging
import pickle
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


# Indian e-commerce holiday calendar for Prophet
def _get_holidays() -> pd.DataFrame:
    rows = []
    for year in range(2021, 2028):
        events = [
            ("New Year",           f"{year}-01-01", 1),
            ("Republic Day Sale",  f"{year}-01-26", 2),
            ("Valentine's Day",    f"{year}-02-14", 1),
            ("Holi",               f"{year}-03-25", 1),
            ("Independence Day",   f"{year}-08-15", 2),
            ("Gandhi Jayanti Sale",f"{year}-10-02", 1),
            ("Dussehra",           f"{year}-10-12", 2),
            ("Diwali",             f"{year}-11-12", 3),
            ("Black Friday",       f"{year}-11-29", 2),
            ("Cyber Monday",       f"{year}-12-02", 1),
            ("Christmas",          f"{year}-12-25", 1),
            ("New Year Eve",       f"{year}-12-31", 1),
        ]
        for name, ds, lower_window in events:
            rows.append({"holiday": name, "ds": pd.Timestamp(ds),
                         "lower_window": -lower_window, "upper_window": 1})
    return pd.DataFrame(rows)


class ProphetForecaster:
    """
    Prophet-based forecaster with regressors and custom holidays.

    Usage:
        pf = ProphetForecaster()
        pf.fit(train_df)                        # df must have ds, y + regressor cols
        forecast = pf.predict(horizon=30, future_regressors=reg_df)
    """

    def __init__(
        self,
        changepoint_prior_scale: float = 0.05,
        seasonality_prior_scale: float = 10.0,
        holidays_prior_scale: float = 10.0,
        interval_width: float = 0.90,
        regressors: list[str] | None = None,
    ):
        self.changepoint_prior_scale = changepoint_prior_scale
        self.seasonality_prior_scale = seasonality_prior_scale
        self.holidays_prior_scale = holidays_prior_scale
        self.interval_width = interval_width
        self.regressors = regressors or ["marketing_spend", "discount_pct", "is_promo"]
        self.model = None
        self.is_fitted: bool = False
        self.train_df: Optional[pd.DataFrame] = None

    # ── Training ──────────────────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame) -> "ProphetForecaster":
        """
        Fit Prophet.  df must contain columns: ds, y, and any regressors.
        """
        try:
            from prophet import Prophet
        except ImportError:
            raise ImportError(
                "prophet not installed. Run: pip install prophet"
            )

        self.train_df = df.copy()

        self.model = Prophet(
            changepoint_prior_scale=self.changepoint_prior_scale,
            seasonality_prior_scale=self.seasonality_prior_scale,
            holidays_prior_scale=self.holidays_prior_scale,
            interval_width=self.interval_width,
            holidays=_get_holidays(),
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
        )

        # Add extra monthly seasonality to capture Q4 ramp-up
        self.model.add_seasonality(
            name="monthly", period=30.5, fourier_order=5
        )

        # Add external regressors
        available_cols = set(df.columns)
        for reg in self.regressors:
            if reg in available_cols:
                self.model.add_regressor(reg, standardize=True)
            else:
                logger.warning(f"Regressor '{reg}' not found in df — skipping.")

        # Prophet expects boolean regressors as float
        fit_df = df[["ds", "y"] + [r for r in self.regressors if r in available_cols]].copy()
        for col in ["is_promo", "is_holiday", "is_weekend"]:
            if col in fit_df.columns:
                fit_df[col] = fit_df[col].astype(float)

        self.model.fit(fit_df)
        self.is_fitted = True
        logger.info("Prophet fitting complete.")
        return self

    # ── Inference ─────────────────────────────────────────────────────────────

    def predict(
        self,
        horizon: int = 30,
        future_regressors: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Forecast `horizon` days.

        If regressors are used, pass `future_regressors` as a DataFrame with
        columns [ds, marketing_spend, discount_pct, is_promo, ...].
        If None, we auto-generate naive forward-fill values from training tail.
        """
        if not self.is_fitted:
            raise RuntimeError("Call .fit() before .predict()")

        future = self.model.make_future_dataframe(periods=horizon, freq="D")

        # Populate regressors on future dates
        active_regs = [r for r in self.regressors if r in (self.train_df.columns if self.train_df is not None else [])]
        if active_regs:
            if future_regressors is not None:
                # Merge provided regressors
                future = future.merge(
                    future_regressors[["ds"] + active_regs], on="ds", how="left"
                )
            else:
                # Naive: carry forward mean of last 30 days
                tail = self.train_df.tail(30)
                for reg in active_regs:
                    if reg in ["is_promo", "is_holiday", "is_weekend"]:
                        future[reg] = 0.0
                    else:
                        future[reg] = tail[reg].mean()

            for col in ["is_promo", "is_holiday", "is_weekend"]:
                if col in future.columns:
                    future[col] = future[col].fillna(0.0).astype(float)
            for reg in active_regs:
                if reg not in ["is_promo", "is_holiday", "is_weekend"]:
                    future[reg] = future[reg].fillna(future[reg].mean())

        raw = self.model.predict(future)

        # Return only forecast horizon (tail)
        forecast = raw.tail(horizon)[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        forecast["yhat"]       = np.clip(forecast["yhat"],       0, None).round(2)
        forecast["yhat_lower"] = np.clip(forecast["yhat_lower"], 0, None).round(2)
        forecast["yhat_upper"] = forecast["yhat_upper"].round(2)
        forecast["model"]      = "Prophet"
        forecast = forecast.reset_index(drop=True)
        return forecast

    def get_components(self) -> Optional[pd.DataFrame]:
        """
        Returns the full in-sample component breakdown (trend, weekly,
        yearly, holiday, regressors).  Useful for dashboard visualisation.
        """
        if not self.is_fitted or self.train_df is None:
            return None
        future = self.model.make_future_dataframe(periods=0, freq="D")
        active_regs = [r for r in self.regressors if r in self.train_df.columns]
        if active_regs:
            future = future.merge(
                self.train_df[["ds"] + active_regs], on="ds", how="left"
            )
            for col in ["is_promo", "is_holiday", "is_weekend"]:
                if col in future.columns:
                    future[col] = future[col].fillna(0.0).astype(float)
        return self.model.predict(future)

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)
        logger.info(f"Prophet model saved → {path}")

    @classmethod
    def load(cls, path: str) -> "ProphetForecaster":
        with open(path, "rb") as f:
            obj = pickle.load(f)
        logger.info(f"Prophet model loaded ← {path}")
        return obj

    # ── Evaluation ────────────────────────────────────────────────────────────

    @staticmethod
    def evaluate(actual: np.ndarray, predicted: np.ndarray) -> dict:
        actual    = np.array(actual)
        predicted = np.array(predicted)
        mae  = np.mean(np.abs(actual - predicted))
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        mape = np.mean(np.abs((actual - predicted) / (actual + 1e-8))) * 100
        return {"MAE": round(mae, 3), "RMSE": round(rmse, 3), "MAPE": round(mape, 3)}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from data_generator import generate_daily_demand, ForecastingConfig

    df = generate_daily_demand(ForecastingConfig(periods=400))
    train, test = df.iloc[:370], df.iloc[370:]

    pf = ProphetForecaster()
    pf.fit(train)
    forecast = pf.predict(horizon=30)
    print(forecast.to_string())

    metrics = ProphetForecaster.evaluate(test["y"].values[:30], forecast["yhat"].values)
    print(f"\nTest metrics: {metrics}")