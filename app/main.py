from fastapi import FastAPI
import random
from sqlalchemy import create_engine
import pandas as pd

app = FastAPI(title="SmartGrowth AI Engine")

engine = create_engine('postgresql://username:password@localhost:5432/smartgrowth_db')

@app.get("/customer/{customer_id}")
def get_customer(customer_id: str):
    query = f"SELECT * FROM dim_customers WHERE customer_id = '{customer_id}'"
    df = pd.read_sql(query, engine)
    
    if df.empty:
        return {"error": "Customer not found"}
    
    return df.to_dict(orient='records')[0]

@app.get("/")
def home():
    return {"message": "SmartGrowth AI Backend is Running"}

@app.get("/predict/churn/{customer_id}")
def predict_churn(customer_id: str):
    # This is a placeholder. In Phase 2, we will load a real model here.
    risk_score = random.uniform(0, 1)
    return {
        "customer_id": customer_id,
        "churn_risk": round(risk_score, 2),
        "status": "High Risk" if risk_score > 0.7 else "Low Risk"
    }


