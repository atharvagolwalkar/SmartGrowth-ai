from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
import sqlite3
import logging
from datetime import datetime
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our production ML model
from ml_models.churn.predictor import ChurnPredictor, get_predictor

from sqlalchemy import create_engine, text
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SmartGrowth AI",
    description="Production ML Platform for Customer Intelligence & Growth Analytics",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Use SQLite database (same as setup_database.py)
db_path = os.path.join(os.path.dirname(__file__), '..', 'smartgrowth.db')
engine = create_engine(f'sqlite:///{db_path}')

# Pydantic models for request/response validation
class CustomerData(BaseModel):
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

# Initialize the ML predictor
try:
    predictor = get_predictor()
    logger.info("✅ ML Predictor initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize ML predictor: {e}")
    predictor = None

@app.get("/")
def home():
    """Health check and API information"""
    return {
        "message": "SmartGrowth AI Backend is Running",
        "version": "1.0.0",
        "ml_model_status": "loaded" if predictor else "failed",
        "endpoints": [
            "/customer/{customer_id}",
            "/predict/churn/{customer_id}",
            "/predict/churn/batch",
            "/customers/all",
            "/model/info",
            "/health"
        ]
    }

@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database_status": "connected" if os.path.exists(db_path) else "disconnected",
        "ml_model_status": "loaded" if predictor and predictor.model else "not loaded",
        "model_info": predictor.get_model_info() if predictor else None
    }

@app.get("/customer/{customer_id}")
def get_customer(customer_id: str):
    """Get customer information by ID"""
    try:
        # Use parameterized query to prevent SQL injection
        query = text("SELECT * FROM dim_customers WHERE customer_id = :customer_id")
        df = pd.read_sql(query, engine, params={'customer_id': customer_id})
        
        if df.empty:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer_data = df.to_dict(orient='records')[0]
        logger.info(f"Retrieved customer: {customer_id}")
        return customer_data
        
    except Exception as e:
        logger.error(f"Error retrieving customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/customers/all")
def get_all_customers(limit: int = 100, offset: int = 0):
    """Get paginated list of all customers"""
    try:
        query = text("SELECT * FROM dim_customers LIMIT :limit OFFSET :offset")
        df = pd.read_sql(query, engine, params={'limit': limit, 'offset': offset})
        
        total_count_query = text("SELECT COUNT(*) as count FROM dim_customers")
        total_count = pd.read_sql(total_count_query, engine).iloc[0]['count']
        
        return {
            "customers": df.to_dict(orient='records'),
            "total_count": int(total_count),
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }
        
    except Exception as e:
        logger.error(f"Error retrieving customers: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/predict/churn/{customer_id}", response_model=ChurnPredictionResponse)
def predict_churn(customer_id: str):
    """Predict churn for a specific customer using real ML model"""
    try:
        if not predictor:
            raise HTTPException(status_code=503, detail="ML model not available")
        
        logger.info(f"Predicting churn for customer: {customer_id}")
        
        # Make prediction using our production ML model
        prediction_result = predictor.predict_churn(customer_id)
        
        logger.info(f"Churn prediction completed for {customer_id}: {prediction_result['risk_level']}")
        return prediction_result
        
    except ValueError as e:
        logger.error(f"Customer {customer_id} not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error predicting churn for {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/predict/churn/manual")
def predict_churn_manual(customer_data: CustomerData):
    """Predict churn for manually provided customer data"""
    try:
        if not predictor:
            raise HTTPException(status_code=503, detail="ML model not available")
        
        logger.info("Predicting churn for manual customer data")
        
        # Convert to dict and make prediction
        customer_dict = customer_data.dict()
        prediction_result = predictor.predict_churn(customer_dict)
        
        logger.info(f"Manual churn prediction completed: {prediction_result['risk_level']}")
        return prediction_result
        
    except Exception as e:
        logger.error(f"Error in manual churn prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/predict/churn/batch")
def predict_churn_batch(request: BatchPredictionRequest):
    """Predict churn for multiple customers"""
    try:
        if not predictor:
            raise HTTPException(status_code=503, detail="ML model not available")
        
        logger.info(f"Batch churn prediction for {len(request.customer_ids)} customers")
        
        # Make batch predictions
        results = predictor.batch_predict(request.customer_ids)
        
        # Summarize results
        successful_predictions = [r for r in results if 'error' not in r]
        failed_predictions = [r for r in results if 'error' in r]
        
        summary = {
            "batch_results": results,
            "summary": {
                "total_requested": len(request.customer_ids),
                "successful_predictions": len(successful_predictions),
                "failed_predictions": len(failed_predictions),
                "success_rate": len(successful_predictions) / len(request.customer_ids) * 100
            }
        }
        
        logger.info(f"Batch prediction completed: {len(successful_predictions)}/{len(request.customer_ids)} successful")
        return summary
        
    except Exception as e:
        logger.error(f"Error in batch churn prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")

@app.get("/model/info")
def get_model_info():
    """Get information about the loaded ML model"""
    try:
        if not predictor:
            raise HTTPException(status_code=503, detail="ML model not available")
        
        model_info = predictor.get_model_info()
        return model_info
        
    except Exception as e:
        logger.error(f"Error retrieving model info: {e}")
        raise HTTPException(status_code=500, detail=f"Model info error: {str(e)}")

@app.get("/customers/high-risk")
def get_high_risk_customers(limit: int = 50):
    """Get customers with high churn risk (demo endpoint)"""
    try:
        if not predictor:
            raise HTTPException(status_code=503, detail="ML model not available")
        
        # Get random sample of customers for demo
        query = text("SELECT * FROM dim_customers ORDER BY RANDOM() LIMIT :limit")
        df = pd.read_sql(query, engine, params={'limit': limit})
        
        high_risk_customers = []
        for _, customer in df.iterrows():
            try:
                prediction = predictor.predict_churn(customer.to_dict())
                if prediction['churn_probability'] >= 0.6:  # High risk threshold
                    high_risk_customers.append({
                        'customer_id': customer['customer_id'],
                        'churn_probability': prediction['churn_probability'],
                        'risk_level': prediction['risk_level'],
                        'monthly_charges': customer['monthly_charges'],
                        'tenure_months': customer['tenure_months']
                    })
            except:
                continue
        
        return {
            "high_risk_customers": high_risk_customers,
            "count": len(high_risk_customers),
            "threshold": 0.6
        }
        
    except Exception as e:
        logger.error(f"Error retrieving high-risk customers: {e}")
        raise HTTPException(status_code=500, detail=f"High-risk customers error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


