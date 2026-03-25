# SmartGrowth AI

SmartGrowth AI is an end-to-end customer intelligence platform designed like a production system used by companies such as Amazon, Netflix, and Uber: data foundation, ML models, API serving, and business dashboard in one workflow.

It helps teams answer practical business questions:
- Which customers are likely to churn?
- Who should be targeted first for retention?
- What action should we take for each risk tier?
- How can we prepare for demand variation over time?

## Project Goal

Build a practical, production-style AI product for growth teams, not just a notebook experiment. The project combines:
- Structured data layer
- Feature engineering and trained ML artifacts
- Real-time inference API
- Interactive decision dashboard
- Automated setup and test flows

## Core Features

## 1) Customer Churn Intelligence
- Production predictor class (`ChurnPredictor`) with model loading, fallback training, and batch inference
- Real-time churn scoring by customer ID
- Manual scoring endpoint for ad-hoc customer profiles
- Risk segmentation (`Low Risk`, `Medium Risk`, `High Risk`)
- Actionable recommendation engine tied to probability bands

## 2) FastAPI Backend
- API service for customer retrieval and churn prediction
- Health/status and model metadata endpoints
- Batch prediction endpoint for multiple customers
- High-risk customer scan endpoint
- Pydantic request/response validation

## 3) Streamlit Business Dashboards
- Lightweight dashboard for quick lookups
- Enhanced dashboard with multi-page workflows:
  - Overview KPIs
  - Detailed customer analysis
  - Model performance view
  - High-risk customer monitoring
  - Batch prediction operations
- Plotly charts for clear business interpretation

## 4) Data Platform Foundation
- SQLite schema with dimensions/facts/views
- Seed loaders for churn data and synthetic daily demand
- Cleaned and typed customer data ingestion pipeline
- Analytical views for segmentation and demand summaries

## 5) Forecasting Data Readiness
- Synthetic daily demand generator with:
  - seasonality
  - promotions
  - holiday effects
  - marketing spend and discount impact
- Forecasting-ready fact table (`fact_daily_demand`)

## 6) Production Readiness Utilities
- Config management with environment-driven settings
- One-command setup/deploy scripts
- API and model smoke-test scripts
- Unit tests for model, config, API behavior, and forecasting data

## Architecture

```text
Data Source (Telco CSV + Synthetic Demand)
        |
        v
Database Setup & Loader (schema + ETL)
        |
        +--> SQLite (customers, transactions, demand, feedback, views)
        |
        v
ML Layer (churn model artifacts + predictor engine)
        |
        v
FastAPI Service (online inference + data endpoints)
        |
        v
Streamlit Dashboard (business decision interface)
```

## Main Tech Stack

- Python
- FastAPI + Uvicorn
- Streamlit + Plotly
- scikit-learn, pandas, numpy, joblib
- SQLAlchemy + SQLite
- pytest
- Pydantic + pydantic-settings

## Current Project Capabilities

Today the project can:
- Initialize database and load customer + demand data
- Serve real churn predictions from trained model artifacts
- Return business recommendations by risk level
- Run batch predictions
- Display results through interactive dashboard pages
- Validate behavior via test suite and smoke checks

## Setup

## 1) Install dependencies
```bash
pip install -r requirements.txt
```

## 2) Initialize database
```bash
python setup_database.py
```

## 3) Start backend
```bash
cd app
python main.py
```

## 4) Start dashboard
```bash
cd app
streamlit run dashboard_enhanced.py
```

## 5) Open services
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501

## Quick API Examples

## Single prediction
```bash
curl http://localhost:8000/predict/churn/7590-VHVEG
```

## Batch prediction
```bash
curl -X POST http://localhost:8000/predict/churn/batch \
  -H "Content-Type: application/json" \
  -d '{"customer_ids": ["7590-VHVEG", "5575-GNVDE", "3668-QPYBK"]}'
```

## Customer lookup
```bash
curl http://localhost:8000/customer/7590-VHVEG
```

## Testing and Validation

Run all tests:
```bash
python run_tests.py
```

Direct smoke tests:
```bash
python test_prediction.py
python test_api.py
```

## Project Structure (High Level)

```text
app/
  main.py                  # FastAPI backend
  dashboard.py             # Lightweight dashboard
  dashboard_enhanced.py    # Full business dashboard

database/
  schema.sql               # DB schema and views
  loader.py                # ETL/data loading utilities

ml_models/
  churn/
    predictor.py           # Production churn inference engine
    enhanced_churn_model.joblib
  forecasting/
    data_generator.py      # Synthetic demand generator

tests/
  test_smartgrowth.py
  test_forecasting.py

config.py                  # Environment/config management
setup_database.py          # Database bootstrap
deploy.py                  # Deployment orchestration script
run_tests.py               # Test orchestrator
```

## Roadmap (Next Steps)

- Add stronger production deployment flow (process supervision, logs, retries)
- Add auth/security for API endpoints
- Add CI pipeline for install + tests + API smoke checks
- Add model monitoring (latency, drift, prediction quality)
- Expand forecasting into a trained forecasting model service

## Vision Summary

SmartGrowth AI is built as a practical blueprint for a modern AI product:
- data-first foundation
- model-driven decisions
- API-first serving
- business-ready interface

The focus is not only prediction accuracy, but operational usability for growth, retention, and strategic planning teams.