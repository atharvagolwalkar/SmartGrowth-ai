"""
Tests for SmartGrowth AI forecasting module.

Run with:
    pytest tests/test_forecasting.py -v
or:
    python -m pytest tests/test_forecasting.py -v --tb=short
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import sys
from pathlib import Path

# Make sure imports resolve from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml_models.forecasting.data_generator import generate_daily_demand, ForecastingConfig
from ml_models.forecasting.arima_forecaster import ARIMAForecaster
from ml_models.forecasting.nbeats_forecaster import NBEATSForecaster, _NBeatsNumpy


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def small_df():
    """200-day dataset — fast for unit tests."""
    return generate_daily_demand(ForecastingConfig(periods=200, seed=0))


@pytest.fixture(scope="module")
def medium_df():
    """400-day dataset — for model fit tests."""
    return generate_daily_demand(ForecastingConfig(periods=400, seed=1))


# ── Data generator tests ──────────────────────────────────────────────────────

class TestDataGenerator:
    def test_shape(self, small_df):
        assert small_df.shape == (200, 11)

    def test_required_columns(self, small_df):
        required = {"ds", "y", "day_of_week", "month", "is_weekend",
                    "is_holiday", "is_promo", "marketing_spend",
                    "discount_pct", "avg_order_value", "revenue"}
        assert required.issubset(set(small_df.columns))

    def test_dates_are_daily(self, small_df):
        diffs = small_df["ds"].diff().dropna()
        assert (diffs == pd.Timedelta("1D")).all()

    def test_demand_positive(self, small_df):
        assert (small_df["y"] > 0).all()

    def test_discount_in_range(self, small_df):
        assert small_df["discount_pct"].between(0, 0.40).all()

    def test_revenue_positive(self, small_df):
        assert (small_df["revenue"] > 0).all()

    def test_reproducibility(self):
        df1 = generate_daily_demand(ForecastingConfig(seed=99))
        df2 = generate_daily_demand(ForecastingConfig(seed=99))
        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seeds_differ(self):
        df1 = generate_daily_demand(ForecastingConfig(seed=1))
        df2 = generate_daily_demand(ForecastingConfig(seed=2))
        assert not df1["y"].equals(df2["y"])

    def test_config_periods(self):
        for n in [100, 365, 730]:
            df = generate_daily_demand(ForecastingConfig(periods=n))
            assert len(df) == n


# ── ARIMA tests ───────────────────────────────────────────────────────────────

class TestARIMAForecaster:
    def test_predict_before_fit_raises(self):
        a = ARIMAForecaster()
        with pytest.raises(RuntimeError):
            a.predict()

    def test_fit_and_predict(self, small_df):
        a = ARIMAForecaster(seasonal=False)   # non-seasonal for speed
        a.fit(small_df.iloc[:170])
        preds = a.predict(horizon=30)
        assert len(preds) == 30
        assert set(preds.columns) >= {"ds", "yhat", "yhat_lower", "yhat_upper"}

    def test_predictions_positive(self, small_df):
        a = ARIMAForecaster(seasonal=False)
        a.fit(small_df.iloc[:170])
        preds = a.predict(horizon=10)
        assert (preds["yhat"] >= 0).all()

    def test_ci_ordering(self, small_df):
        a = ARIMAForecaster(seasonal=False)
        a.fit(small_df.iloc[:170])
        preds = a.predict(horizon=10)
        assert (preds["yhat_upper"] >= preds["yhat"]).all()
        assert (preds["yhat"] >= preds["yhat_lower"]).all()

    def test_evaluate_metrics(self):
        actual    = np.array([100, 110, 120, 130, 140])
        predicted = np.array([105, 108, 125, 128, 145])
        metrics = ARIMAForecaster.evaluate(actual, predicted)
        assert set(metrics.keys()) == {"MAE", "RMSE", "MAPE"}
        assert metrics["MAE"] > 0
        assert metrics["MAPE"] < 10   # reasonable accuracy


# ── N-BEATS numpy fallback tests ──────────────────────────────────────────────

class TestNBeatsNumpy:
    def test_fit_predict(self):
        rng = np.random.default_rng(0)
        series = 500 + np.arange(200) * 0.1 + rng.normal(0, 20, 200)
        nb = _NBeatsNumpy(horizon=10, lookback=50, n_epochs=20)
        nb.fit(series)
        preds = nb.predict()
        assert len(preds) == 10

    def test_output_in_reasonable_range(self):
        rng = np.random.default_rng(1)
        series = np.clip(500 + rng.normal(0, 30, 300), 200, 1000)
        nb = _NBeatsNumpy(horizon=15, lookback=60, n_epochs=30)
        nb.fit(series)
        preds = nb.predict()
        # Predictions should be in the same ballpark (within 3× of series mean)
        assert (preds > 0).all()
        assert preds.mean() < series.mean() * 3


class TestNBEATSForecaster:
    def test_fit_and_predict_numpy(self, small_df):
        nf = NBEATSForecaster(horizon=10, max_steps=30)
        nf.fit(small_df.iloc[:170])
        assert nf.is_fitted
        preds = nf.predict()
        assert len(preds) == 10

    def test_predict_columns(self, small_df):
        nf = NBEATSForecaster(horizon=10, max_steps=20)
        nf.fit(small_df.iloc[:170])
        preds = nf.predict()
        assert set(preds.columns) >= {"ds", "yhat", "yhat_lower", "yhat_upper", "model"}

    def test_ci_ordering(self, small_df):
        nf = NBEATSForecaster(horizon=10, max_steps=20)
        nf.fit(small_df.iloc[:170])
        preds = nf.predict()
        assert (preds["yhat_upper"] >= preds["yhat_lower"]).all()

    def test_evaluate_metrics(self):
        a = np.array([500, 520, 510, 530])
        p = np.array([490, 525, 505, 540])
        m = NBEATSForecaster.evaluate(a, p)
        assert "MAE" in m and "RMSE" in m and "MAPE" in m
        assert m["MAE"] > 0


# ── Pipeline integration test (lightweight) ───────────────────────────────────

class TestForecastPipelineIntegration:
    def test_pipeline_run_skip_heavy(self, medium_df):
        """Run pipeline with ARIMA + numpy N-BEATS skipped for speed."""
        from ml_models.forecasting.pipeline import ForecastPipeline
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = ForecastPipeline(
                artifact_dir=tmpdir,
                skip_arima=True,
                skip_nbeats=True,   # skip heavy models in CI
            )
            results = pipeline.run(df=medium_df)

        assert "Prophet" in results or len(results) > 0

    def test_pipeline_best_model_selection(self):
        from ml_models.forecasting.pipeline import ForecastPipeline
        results = {
            "ARIMA":   {"MAPE": 8.5, "MAE": 50, "RMSE": 60},
            "Prophet": {"MAPE": 6.2, "MAE": 38, "RMSE": 48},
            "N-BEATS": {"MAPE": 5.1, "MAE": 30, "RMSE": 40},
        }
        best = ForecastPipeline._pick_best(results)
        assert best == "N-BEATS"

    def test_pipeline_best_model_fallback_on_error(self):
        from ml_models.forecasting.pipeline import ForecastPipeline
        results = {
            "ARIMA":   {"error": "fit failed"},
            "Prophet": {"MAPE": 6.0, "MAE": 35, "RMSE": 45},
            "N-BEATS": {"error": "fit failed"},
        }
        best = ForecastPipeline._pick_best(results)
        assert best == "Prophet"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])