"""
Forecasting API routes for SmartGrowth AI.

Drop these routes into app/main.py by importing and including the router:

    from app.forecast_routes import router as forecast_router
    app.include_router(forecast_router, prefix="/forecast", tags=["Forecasting"])

Endpoints:
    GET  /forecast/predict?horizon=30&model=best
    GET  /forecast/predict/all?horizon=30
    GET  /forecast/metrics
    GET  /forecast/models
    POST /forecast/retrain
"""

from __future__ import annotations

import logging
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Lazy-load the pipeline (avoids import-time model loading) ─────────────────

_pipeline = None

def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        from ml_models.forecasting import get_forecast_pipeline
        _pipeline = get_forecast_pipeline()
    return _pipeline


# ── Response schemas ──────────────────────────────────────────────────────────

class ForecastPoint(BaseModel):
    date:        str
    forecast:    float
    lower_bound: float
    upper_bound: float
    model:       str


class ForecastResponse(BaseModel):
    model_used:       str
    horizon_days:     int
    forecast:         list[ForecastPoint]
    business_summary: dict


class ModelMetricsResponse(BaseModel):
    best_model:   str
    holdout_days: int
    models:       dict


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/predict", response_model=ForecastResponse, summary="Generate demand forecast")
def get_forecast(
    horizon: int = Query(default=30, ge=1, le=365, description="Days to forecast"),
    model:   str = Query(default="best", description="Model: best | ARIMA | Prophet | N-BEATS"),
):
    """
    Generate a demand forecast for the next `horizon` days.

    - **horizon**: 1–365 days
    - **model**: which model to use (`best` = auto-select by MAPE)
    """
    pipeline = _get_pipeline()

    valid_models = {"best", "ARIMA", "Prophet", "N-BEATS"}
    if model not in valid_models:
        raise HTTPException(400, f"Invalid model. Choose from: {valid_models}")

    try:
        df = pipeline.forecast(horizon=horizon, model=model)
    except RuntimeError as e:
        raise HTTPException(503, detail=str(e))

    points = [
        ForecastPoint(
            date=str(row["ds"].date()),
            forecast=float(row["yhat"]),
            lower_bound=float(row["yhat_lower"]),
            upper_bound=float(row["yhat_upper"]),
            model=row["model"],
        )
        for _, row in df.iterrows()
    ]

    # Business summary
    total_units   = df["yhat"].sum()
    avg_daily     = df["yhat"].mean()
    peak_day      = df.loc[df["yhat"].idxmax()]
    trough_day    = df.loc[df["yhat"].idxmin()]

    summary = {
        "total_forecast_units": round(total_units, 0),
        "avg_daily_demand":     round(avg_daily, 1),
        "peak_day":             str(peak_day["ds"].date()),
        "peak_demand":          round(float(peak_day["yhat"]), 1),
        "trough_day":           str(trough_day["ds"].date()),
        "trough_demand":        round(float(trough_day["yhat"]), 1),
        "demand_volatility":    round(float(df["yhat"].std()), 1),
        "model_used":           df["model"].iloc[0],
    }

    return ForecastResponse(
        model_used=df["model"].iloc[0],
        horizon_days=horizon,
        forecast=points,
        business_summary=summary,
    )


@router.get("/predict/all", summary="Forecast from all models (for comparison)")
def get_all_forecasts(
    horizon: int = Query(default=30, ge=1, le=90),
):
    """
    Returns forecasts from all loaded models side by side.
    Useful for the dashboard comparison chart.
    """
    pipeline = _get_pipeline()

    try:
        all_forecasts = pipeline.forecast(horizon=horizon, return_all=True)
    except RuntimeError as e:
        raise HTTPException(503, detail=str(e))

    response = {}
    for model_name, df in all_forecasts.items():
        response[model_name] = [
            {
                "date":        str(row["ds"].date()) if hasattr(row["ds"], 'date') else str(row["ds"]),
                "forecast":    round(float(row["yhat"]), 2),
                "lower_bound": round(float(row["yhat_lower"]), 2),
                "upper_bound": round(float(row["yhat_upper"]), 2),
            }
            for _, row in df.iterrows()
        ]

    return {
        "horizon_days":  horizon,
        "best_model":    pipeline.best_model_name,
        "forecasts":     response,
    }


@router.get("/metrics", response_model=ModelMetricsResponse, summary="Model evaluation metrics")
def get_metrics():
    """
    Returns the holdout evaluation metrics for all trained models.
    Used by the dashboard model comparison table.
    """
    pipeline = _get_pipeline()

    if not pipeline.metrics:
        raise HTTPException(404, detail="No metrics available. Run pipeline.run() first.")

    return ModelMetricsResponse(
        best_model=pipeline.best_model_name,
        holdout_days=30,
        models=pipeline.metrics,
    )


@router.get("/models", summary="List available forecasting models")
def list_models():
    """Returns which models are loaded and ready."""
    pipeline = _get_pipeline()
    return {
        "best_model": pipeline.best_model_name,
        "available": {
            "ARIMA":   pipeline.arima_model is not None and getattr(pipeline.arima_model, "is_fitted", False),
            "Prophet": pipeline.prophet_model is not None and getattr(pipeline.prophet_model, "is_fitted", False),
            "N-BEATS": pipeline.nbeats_model is not None and getattr(pipeline.nbeats_model, "is_fitted", False),
        },
    }


@router.post("/retrain", summary="Retrain all forecasting models (async)")
def retrain(background_tasks: BackgroundTasks):
    """
    Triggers a full pipeline retrain in the background.
    Returns immediately — check /forecast/metrics for results.
    """
    def _retrain_job():
        global _pipeline
        from ml_models.forecasting import ForecastPipeline
        logger.info("Background retrain started...")
        p = ForecastPipeline()
        p.run()
        _pipeline = p
        logger.info("Background retrain complete.")

    background_tasks.add_task(_retrain_job)
    return {"status": "retrain_started", "message": "Check /forecast/metrics in ~2 minutes."}