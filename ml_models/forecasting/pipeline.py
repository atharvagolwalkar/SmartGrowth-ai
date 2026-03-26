"""
ForecastPipeline — SmartGrowth AI

Unified entry point that:
  1. Loads / generates demand data
  2. Trains ARIMA (baseline), Prophet (business), N-BEATS (DL)
  3. Evaluates all three on a hold-out window
  4. Picks best model by MAPE
  5. Saves all artifacts to ml_models/forecasting/artifacts/
  6. Exposes a single .forecast(horizon) method for the FastAPI layer

This is the file that gets imported by app/main.py.

Model comparison table (example output):
    Model    │  MAE    │  RMSE   │  MAPE
    ─────────┼─────────┼─────────┼───────
    ARIMA    │  42.3   │  55.1   │  7.8%
    Prophet  │  31.7   │  41.2   │  5.9%
    N-BEATS  │  28.4   │  38.6   │  5.3%  ← best
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .data_generator import generate_daily_demand, ForecastingConfig
from .arima_forecaster import ARIMAForecaster
from .prophet_forecaster import ProphetForecaster
from .nbeats_forecaster import NBEATSForecaster

logger = logging.getLogger(__name__)

_ARTIFACT_DIR = Path(__file__).parent / "artifacts"
_METRICS_FILE = _ARTIFACT_DIR / "evaluation_metrics.json"
_HOLDOUT_DAYS = 30


class ForecastPipeline:
    """
    Orchestrates the full forecasting lifecycle.

    Quick start:
        pipeline = ForecastPipeline()
        pipeline.run()                          # train + evaluate + save
        result = pipeline.forecast(horizon=30)  # get predictions from best model
    """

    def __init__(
        self,
        config: Optional[ForecastingConfig] = None,
        artifact_dir: Optional[str] = None,
        skip_arima: bool = False,       # set True to speed up dev iterations
        skip_nbeats: bool = True,
    ):
        self.config = config or ForecastingConfig()
        self.artifact_dir = Path(artifact_dir) if artifact_dir else _ARTIFACT_DIR
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

        self.skip_arima  = skip_arima
        self.skip_nbeats = skip_nbeats

        # Loaded after run() or load()
        self.arima_model:   Optional[ARIMAForecaster]   = None
        self.prophet_model: Optional[ProphetForecaster] = None
        self.nbeats_model:  Optional[NBEATSForecaster]  = None
        self.best_model_name: str = "Prophet"   # sensible default
        self.metrics: dict = {}
        self.df: Optional[pd.DataFrame] = None

    # ── Full pipeline run ─────────────────────────────────────────────────────

    def run(self, df: Optional[pd.DataFrame] = None) -> dict:
        """
        Train all models, evaluate on hold-out, save artifacts.
        Returns evaluation metrics dict.
        """
        logger.info("=" * 60)
        logger.info("SmartGrowth AI — Forecasting Pipeline")
        logger.info("=" * 60)

        # 1. Data
        if df is None:
            logger.info("Generating synthetic demand data...")
            df = generate_daily_demand(self.config)
        self.df = df

        train = df.iloc[:-_HOLDOUT_DAYS]
        test  = df.iloc[-_HOLDOUT_DAYS:]
        actual = test["y"].values

        logger.info(f"Training on {len(train)} days, evaluating on {_HOLDOUT_DAYS} days holdout")

        results = {}

        # 2. ARIMA baseline
        if not self.skip_arima:
            logger.info("\n[1/3] Fitting ARIMA baseline...")
            t0 = time.time()
            try:
                self.arima_model = ARIMAForecaster(seasonal=True, m=7)
                self.arima_model.fit(train)
                arima_preds = self.arima_model.predict(horizon=_HOLDOUT_DAYS)
                arima_metrics = ARIMAForecaster.evaluate(actual, arima_preds["yhat"].values)
                arima_metrics["fit_time_s"] = round(time.time() - t0, 1)
                results["ARIMA"] = arima_metrics
                self.arima_model.save(str(self.artifact_dir / "arima_model.pkl"))
                logger.info(f"  ARIMA metrics: {arima_metrics}")
            except Exception as e:
                logger.warning(f"  ARIMA failed: {e}")
                results["ARIMA"] = {"error": str(e)}
        else:
            logger.info("[1/3] ARIMA skipped.")

        # 3. Prophet
        logger.info("\n[2/3] Fitting Prophet...")
        t0 = time.time()
        try:
            self.prophet_model = ProphetForecaster(
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10.0,
                interval_width=0.90,
            )
            self.prophet_model.fit(train)
            prophet_preds = self.prophet_model.predict(horizon=_HOLDOUT_DAYS)
            prophet_metrics = ProphetForecaster.evaluate(actual, prophet_preds["yhat"].values)
            prophet_metrics["fit_time_s"] = round(time.time() - t0, 1)
            results["Prophet"] = prophet_metrics
            self.prophet_model.save(str(self.artifact_dir / "prophet_model.pkl"))
            logger.info(f"  Prophet metrics: {prophet_metrics}")
        except Exception as e:
            logger.warning(f"  Prophet failed: {e}")
            results["Prophet"] = {"error": str(e)}

        # 4. N-BEATS
        if not self.skip_nbeats:
            logger.info("\n[3/3] Fitting N-BEATS...")
            t0 = time.time()
            try:
                self.nbeats_model = NBEATSForecaster(
                    horizon=_HOLDOUT_DAYS,
                    interpretable=True,
                    max_steps=self.config.__dict__.get("nbeats_steps", 500),
                )
                self.nbeats_model.fit(train)
                nbeats_preds = self.nbeats_model.predict()
                nbeats_metrics = NBEATSForecaster.evaluate(actual, nbeats_preds["yhat"].values)
                nbeats_metrics["fit_time_s"] = round(time.time() - t0, 1)
                results["N-BEATS"] = nbeats_metrics
                self.nbeats_model.save(str(self.artifact_dir / "nbeats_model.pkl"))
                logger.info(f"  N-BEATS metrics: {nbeats_metrics}")
            except Exception as e:
                logger.warning(f"  N-BEATS failed: {e}")
                results["N-BEATS"] = {"error": str(e)}
        else:
            logger.info("[3/3] N-BEATS skipped.")

        # 5. Pick best model by MAPE
        self.metrics = results
        self.best_model_name = self._pick_best(results)

        logger.info(f"\n{'=' * 40}")
        logger.info(f"Best model: {self.best_model_name}")
        self._print_leaderboard(results)

        # 6. Save metrics
        with open(_METRICS_FILE, "w") as f:
            json.dump({
                "results": results,
                "best_model": self.best_model_name,
                "holdout_days": _HOLDOUT_DAYS,
                "train_size": len(train),
            }, f, indent=2)

        return results

    # ── Inference (used by FastAPI) ────────────────────────────────────────────

    def forecast(
        self,
        horizon: int = 30,
        model: str = "best",
        return_all: bool = False,
    ) -> pd.DataFrame | dict:
        """
        Generate a forecast.

        Args:
            horizon:    Days to forecast.
            model:      "best" | "ARIMA" | "Prophet" | "N-BEATS"
            return_all: If True, return dict with forecasts from all loaded models.

        Returns:
            DataFrame with columns: ds, yhat, yhat_lower, yhat_upper, model
        """
        target = self.best_model_name if model == "best" else model

        if return_all:
            out = {}
            if self.arima_model and self.arima_model.is_fitted:
                out["ARIMA"] = self.arima_model.predict(horizon)
            if self.prophet_model and self.prophet_model.is_fitted:
                out["Prophet"] = self.prophet_model.predict(horizon)
            if self.nbeats_model and self.nbeats_model.is_fitted:
                out["N-BEATS"] = self.nbeats_model.predict()
            return out

        model_obj = self._get_model(target)
        if model_obj is None:
            raise RuntimeError(
                f"Model '{target}' is not loaded. Call .run() or .load() first."
            )
        return self._call_predict(model_obj, target, horizon)

    def _get_model(self, name: str):
        mapping = {
            "ARIMA":   self.arima_model,
            "Prophet": self.prophet_model,
            "N-BEATS": self.nbeats_model,
        }
        return mapping.get(name)

    def _call_predict(self, model_obj, name: str, horizon: int) -> pd.DataFrame:
        if name == "N-BEATS":
            return model_obj.predict()
        return model_obj.predict(horizon=horizon)

    # ── Load saved artifacts ───────────────────────────────────────────────────

    def load(self) -> "ForecastPipeline":
        """Load all saved model artifacts from disk."""
        arima_path   = self.artifact_dir / "arima_model.pkl"
        prophet_path = self.artifact_dir / "prophet_model.pkl"
        nbeats_path  = self.artifact_dir / "nbeats_model.pkl"

        if arima_path.exists():
            try:
                self.arima_model = ARIMAForecaster.load(str(arima_path))
            except Exception as e:
                logger.warning(f"Could not load ARIMA: {e}")

        if prophet_path.exists():
            try:
                self.prophet_model = ProphetForecaster.load(str(prophet_path))
            except Exception as e:
                logger.warning(f"Could not load Prophet: {e}")

        if nbeats_path.exists():
            try:
                self.nbeats_model = NBEATSForecaster.load(str(nbeats_path))
            except Exception as e:
                logger.warning(f"Could not load N-BEATS: {e}")

        if _METRICS_FILE.exists():
            with open(_METRICS_FILE) as f:
                saved = json.load(f)
            self.metrics = saved.get("results", {})
            self.best_model_name = saved.get("best_model", "Prophet")

        logger.info(f"Pipeline loaded. Best model: {self.best_model_name}")
        return self

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _pick_best(results: dict) -> str:
        best_name  = "Prophet"
        best_mape  = float("inf")
        priority   = ["N-BEATS", "Prophet", "ARIMA"]   # prefer DL if tie

        for name in priority:
            r = results.get(name, {})
            if "error" not in r and r.get("MAPE", float("inf")) < best_mape:
                best_mape = r["MAPE"]
                best_name = name

        return best_name

    @staticmethod
    def _print_leaderboard(results: dict) -> None:
        print(f"\n{'Model':<12} {'MAE':>8} {'RMSE':>8} {'MAPE':>8} {'Time':>8}")
        print("-" * 48)
        for name, m in results.items():
            if "error" in m:
                print(f"{name:<12} {'ERROR':>8}")
            else:
                print(
                    f"{name:<12}"
                    f" {m.get('MAE', 0):>8.2f}"
                    f" {m.get('RMSE', 0):>8.2f}"
                    f" {m.get('MAPE', 0):>7.2f}%"
                    f" {m.get('fit_time_s', 0):>6.1f}s"
                )


# ── Convenience singleton ─────────────────────────────────────────────────────

_pipeline_instance: Optional[ForecastPipeline] = None


def get_forecast_pipeline() -> ForecastPipeline:
    """
    Returns the singleton ForecastPipeline, loading from disk if available.
    Intended for use in FastAPI startup.
    """
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ForecastPipeline()
        artifact_dir = _ARTIFACT_DIR
        if (artifact_dir / "prophet_model.pkl").exists():
            _pipeline_instance.load()
        else:
            logger.warning(
                "No saved forecast artifacts found. "
                "Run: python -m ml_models.forecasting.pipeline"
            )
    return _pipeline_instance


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

    parser = argparse.ArgumentParser(description="SmartGrowth AI Forecast Pipeline")
    parser.add_argument("--skip-arima",  action="store_true", help="Skip ARIMA training")
    parser.add_argument("--skip-nbeats", action="store_true", help="Skip N-BEATS training")
    parser.add_argument("--horizon",     type=int, default=30, help="Forecast horizon (days)")
    parser.add_argument("--periods",     type=int, default=730, help="Training data days")
    args = parser.parse_args()

    config = ForecastingConfig(periods=args.periods)
    pipeline = ForecastPipeline(
        config=config,
        skip_arima=args.skip_arima,
        skip_nbeats=args.skip_nbeats,
    )
    results = pipeline.run()

    print(f"\nGenerating {args.horizon}-day forecast from best model ({pipeline.best_model_name})...")
    forecast = pipeline.forecast(horizon=args.horizon)
    print(forecast.to_string())