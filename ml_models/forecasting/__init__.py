"""
SmartGrowth AI — Forecasting Module
=====================================

Three-layer forecasting pipeline:
  Layer 1 — ARIMA/SARIMA      (statistical baseline)
  Layer 2 — Facebook Prophet  (business-friendly, handles seasonality + holidays)
  Layer 3 — N-BEATS           (DL architecture, best accuracy)

Public API:
    from ml_models.forecasting import ForecastPipeline, get_forecast_pipeline

    # Train + evaluate + save all models
    pipeline = ForecastPipeline()
    pipeline.run()

    # Get forecast from best model
    df = pipeline.forecast(horizon=30)

    # FastAPI singleton
    pipeline = get_forecast_pipeline()
"""

from .data_generator import generate_daily_demand, ForecastingConfig
from .arima_forecaster import ARIMAForecaster
from .prophet_forecaster import ProphetForecaster
from .nbeats_forecaster import NBEATSForecaster
from .pipeline import ForecastPipeline, get_forecast_pipeline

__all__ = [
    "generate_daily_demand",
    "ForecastingConfig",
    "ARIMAForecaster",
    "ProphetForecaster",
    "NBEATSForecaster",
    "ForecastPipeline",
    "get_forecast_pipeline",
]

__version__ = "1.0.0"
__author__  = "SmartGrowth AI"