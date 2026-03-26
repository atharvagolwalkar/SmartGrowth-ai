from datetime import datetime
import logging
import os
import sys
from typing import Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config
from ml_models.churn.predictor import get_predictor

from app.forecast_routes import router as forecast_router

settings = get_config()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def serialize_row(row: dict) -> dict:
    """Convert numpy types to native Python types for JSON serialization."""
    clean = {}
    for k, v in row.items():
        if hasattr(v, 'item'):          # catches numpy.bool_, numpy.int64, numpy.float64 etc
            clean[k] = v.item()
        elif v != v:                    # NaN check
            clean[k] = None
        else:
            clean[k] = v
    return clean


app = FastAPI(
    title=settings.project_name,
    description="Production ML Platform for Customer Intelligence & Growth Analytics",
    version=settings.version,
)

app.include_router(forecast_router, prefix="/forecast", tags=["Forecasting"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_path = settings.get_database_path()
engine = create_engine(settings.database.database_url)


class CustomerData(BaseModel):
    customer_id: Optional[str] = Field(default=None)
    gender: str
    senior_citizen: int
    partner: int
    dependents: int
    tenure_months: int
    subscription_type: str
    payment_method: str
    monthly_charges: float
    total_charges: float


class ChurnPredictionResponse(BaseModel):
    customer_id: str
    churn_probability: float
    churn_prediction: bool
    risk_level: str
    optimal_threshold: float
    recommendations: List[str]
    model_info: Dict
    prediction_timestamp: str


class BatchPredictionRequest(BaseModel):
    customer_ids: List[str]


try:
    predictor = get_predictor()
    logger.info("ML Predictor initialized successfully")
except Exception as exc:  # pragma: no cover - startup fallback
    logger.error("Failed to initialize ML predictor: %s", exc)
    predictor = None


@app.get("/")
def home():
    """Health check and API information."""
    return {
        "message": "SmartGrowth AI Backend is Running",
        "version": settings.version,
        "ml_model_status": "loaded" if predictor else "failed",
        "endpoints": [
            "/customer/{customer_id}",
            "/predict/churn/{customer_id}",
            "/predict/churn/batch",
            "/customers/all",
            "/model/info",
            "/health",
        ],
    }

@app.on_event("startup")
async def startup_event():
    # ... your existing startup code ...

    # Pre-load forecast pipeline
    try:
        from ml_models.forecasting import get_forecast_pipeline
        get_forecast_pipeline()
        logger.info("Forecast pipeline loaded.")
    except Exception as e:
        logger.warning(f"Forecast pipeline not ready: {e}")


@app.get("/health")
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database_status": "connected" if os.path.exists(db_path) else "disconnected",
        "ml_model_status": "loaded" if predictor and predictor.model else "not loaded",
        "model_info": predictor.get_model_info() if predictor else None,
    }


@app.get("/customer/{customer_id}")
def get_customer(customer_id: str):
    """Get customer information by ID."""
    try:
        query = text("SELECT * FROM dim_customers WHERE customer_id = :customer_id")
        df = pd.read_sql(query, engine, params={"customer_id": customer_id})

        if df.empty:
            raise HTTPException(status_code=404, detail="Customer not found")

        return df.to_dict(orient="records")[0]
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error retrieving customer %s: %s", customer_id, exc)
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")


@app.get("/customers/all")
def get_all_customers(limit: int = 100, offset: int = 0):
    """Get paginated list of all customers."""
    try:
        query = text("SELECT * FROM dim_customers LIMIT :limit OFFSET :offset")
        df = pd.read_sql(query, engine, params={"limit": limit, "offset": offset})

        total_count_query = text("SELECT COUNT(*) as count FROM dim_customers")
        total_count = pd.read_sql(total_count_query, engine).iloc[0]["count"]

        # Fix: replace NaN with None, strip all numpy types to native Python
        df = df.where(pd.notnull(df), None)
        customers = df.astype(object).to_dict(orient="records")

        return {
            "customers": customers,
            "total_count": int(total_count),
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < int(total_count),
        }
    except Exception as exc:
        logger.error("Error retrieving customers: %s", exc)
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")


@app.get("/predict/churn/{customer_id}", response_model=ChurnPredictionResponse)
def predict_churn(customer_id: str):
    """Predict churn for a specific customer using the loaded model."""
    try:
        if not predictor:
            raise HTTPException(status_code=503, detail="ML model not available")

        prediction_result = predictor.predict_churn(customer_id)
        return prediction_result
    except ValueError as exc:
        logger.error("Customer %s not found: %s", customer_id, exc)
        raise HTTPException(status_code=404, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error predicting churn for %s: %s", customer_id, exc)
        raise HTTPException(status_code=500, detail=f"Prediction error: {exc}")


@app.post("/predict/churn/manual", response_model=ChurnPredictionResponse)
def predict_churn_manual(customer_data: CustomerData):
    """Predict churn for manually provided customer data."""
    try:
        if not predictor:
            raise HTTPException(status_code=503, detail="ML model not available")

        prediction_result = predictor.predict_churn(customer_data.model_dump())
        return prediction_result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error in manual churn prediction: %s", exc)
        raise HTTPException(status_code=500, detail=f"Prediction error: {exc}")


@app.post("/predict/churn/batch")
def predict_churn_batch(request: BatchPredictionRequest):
    """Predict churn for multiple customers."""
    try:
        if not predictor:
            raise HTTPException(status_code=503, detail="ML model not available")

        results = predictor.batch_predict(request.customer_ids)
        successful_predictions = [result for result in results if "error" not in result]
        failed_predictions = [result for result in results if "error" in result]

        return {
            "batch_results": results,
            "summary": {
                "total_requested": len(request.customer_ids),
                "successful_predictions": len(successful_predictions),
                "failed_predictions": len(failed_predictions),
                "success_rate": len(successful_predictions) / len(request.customer_ids) * 100,
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error in batch churn prediction: %s", exc)
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {exc}")


@app.get("/model/info")
def get_model_info():
    """Get information about the loaded ML model."""
    try:
        if not predictor:
            raise HTTPException(status_code=503, detail="ML model not available")

        return predictor.get_model_info()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error retrieving model info: %s", exc)
        raise HTTPException(status_code=500, detail=f"Model info error: {exc}")


@app.get("/customers/high-risk")
def get_high_risk_customers(limit: int = 50):
    """Get high-risk customers by scoring a sample of the customer base."""
    try:
        if not predictor:
            raise HTTPException(status_code=503, detail="ML model not available")

        query = text("SELECT * FROM dim_customers ORDER BY RANDOM() LIMIT :limit")
        df = pd.read_sql(query, engine, params={"limit": limit})

        high_risk_customers = []
        for _, customer in df.iterrows():
            try:
                prediction = predictor.predict_churn(customer.to_dict())
            except Exception as exc:
                logger.warning(
                    "Skipping customer %s during high-risk scan: %s",
                    customer.get("customer_id"),
                    exc,
                )
                continue

            if prediction["churn_probability"] >= 0.6:
                high_risk_customers.append(
                    {
                        "customer_id": customer["customer_id"],
                        "churn_probability": prediction["churn_probability"],
                        "risk_level": prediction["risk_level"],
                        "monthly_charges": customer["monthly_charges"],
                        "tenure_months": customer["tenure_months"],
                    }
                )

        return {
            "high_risk_customers": high_risk_customers,
            "count": len(high_risk_customers),
            "threshold": 0.6,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error retrieving high-risk customers: %s", exc)
        raise HTTPException(status_code=500, detail=f"High-risk customers error: {exc}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload,
    )