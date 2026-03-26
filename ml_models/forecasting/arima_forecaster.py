"""
ARIMA / SARIMA baseline forecaster for SmartGrowth AI.

Uses statsmodels auto_arima (via pmdarima) with weekly seasonality.
Acts as the statistical baseline that Prophet and N-BEATS are compared against.
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


class ARIMAForecaster:
    """
    SARIMA baseline forecaster.

    Fits a Seasonal ARIMA (p,d,q)(P,D,Q,m=7) using pmdarima's auto_arima
    which selects the best order via AIC.  Falls back to a simple ARIMA(1,1,1)
    if pmdarima is unavailable.
    """

    def __init__(self, seasonal: bool = True, m: int = 7):
        self.seasonal = seasonal
        self.m = m          # weekly seasonality
        self.model = None
        self.model_fit = None
        self.train_end_date: Optional[pd.Timestamp] = None
        self.is_fitted: bool = False

    # ── Training ──────────────────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame) -> "ARIMAForecaster":
        """
        Fit SARIMA on the 'y' column of df (must also have 'ds' column).
        """
        series = df.set_index("ds")["y"].asfreq("D").fillna(method="ffill")
        self.train_end_date = series.index[-1]

        try:
            import pmdarima as pm
            logger.info("Fitting auto_arima (this may take 30-90 seconds)...")
            self.model = pm.auto_arima(
                series,
                seasonal=self.seasonal,
                m=self.m,
                stepwise=True,
                suppress_warnings=True,
                error_action="ignore",
                max_p=3, max_q=3, max_P=2, max_Q=2,
                information_criterion="aic",
            )
            self.model_fit = self.model
        except ImportError:
            logger.warning("pmdarima not found — falling back to ARIMA(1,1,1)")
            from statsmodels.tsa.arima.model import ARIMA
            self.model = ARIMA(series, order=(1, 1, 1))
            self.model_fit = self.model.fit()

        self.is_fitted = True
        logger.info("ARIMA fitting complete.")
        return self

    # ── Inference ─────────────────────────────────────────────────────────────

    def predict(self, horizon: int = 30) -> pd.DataFrame:
        """
        Forecast `horizon` days ahead.  Returns DataFrame with:
            ds, yhat, yhat_lower, yhat_upper
        """
        if not self.is_fitted:
            raise RuntimeError("Call .fit() before .predict()")

        future_dates = pd.date_range(
            start=self.train_end_date + pd.Timedelta(days=1),
            periods=horizon,
            freq="D",
        )

        try:
            # pmdarima path
            forecast, conf_int = self.model_fit.predict(
                n_periods=horizon, return_conf_int=True, alpha=0.10
            )
            lower = conf_int[:, 0]
            upper = conf_int[:, 1]
        except (AttributeError, TypeError):
            # statsmodels path
            res = self.model_fit.forecast(steps=horizon)
            forecast = res.values if hasattr(res, "values") else np.array(res)
            std_err = forecast.std() * 1.645  # 90% CI approximation
            lower = forecast - std_err
            upper = forecast + std_err

        return pd.DataFrame({
            "ds":          future_dates,
            "yhat":        np.clip(forecast, 0, None).round(2),
            "yhat_lower":  np.clip(lower, 0, None).round(2),
            "yhat_upper":  upper.round(2),
            "model":       "ARIMA",
        })

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)
        logger.info(f"ARIMA model saved to {path}")

    @classmethod
    def load(cls, path: str) -> "ARIMAForecaster":
        with open(path, "rb") as f:
            obj = pickle.load(f)
        logger.info(f"ARIMA model loaded from {path}")
        return obj

    # ── Evaluation ────────────────────────────────────────────────────────────

    @staticmethod
    def evaluate(actual: np.ndarray, predicted: np.ndarray) -> dict:
        actual = np.array(actual)
        predicted = np.array(predicted)
        mae  = np.mean(np.abs(actual - predicted))
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        mape = np.mean(np.abs((actual - predicted) / (actual + 1e-8))) * 100
        return {"MAE": round(mae, 3), "RMSE": round(rmse, 3), "MAPE": round(mape, 3)}


if __name__ == "__main__":
    from data_generator import generate_daily_demand, ForecastingConfig
    df = generate_daily_demand(ForecastingConfig(periods=365))
    train, test = df.iloc[:335], df.iloc[335:]

    arima = ARIMAForecaster(seasonal=True, m=7)
    arima.fit(train)
    preds = arima.predict(horizon=30)
    print(preds.head(10).to_string())

    metrics = ARIMAForecaster.evaluate(test["y"].values[:30], preds["yhat"].values)
    print(f"\nTest metrics: {metrics}")