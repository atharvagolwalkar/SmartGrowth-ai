# SmartGrowth AI: Progress Report and File-by-File Guide

Generated on: 2026-03-23

## 1. What Has Been Completed So Far

### Platform foundation
- Database schema is implemented for customer analytics, transactions, feedback, and daily demand forecasting.
- Data loading pipeline is implemented and can seed the database from Telco churn CSV + synthetic daily demand data.
- Core project configuration is centralized in environment-driven settings.

### ML layer
- Production churn predictor is implemented in Python (load model, feature preparation, risk classification, recommendations).
- Saved model artifacts exist for churn inference (`joblib` files).
- Fallback model training path exists if artifact loading fails.

### API layer
- FastAPI backend is implemented with customer lookup, health checks, single prediction, manual prediction, batch prediction, model info, and high-risk customer scan.
- Request/response schemas are added with Pydantic models.

### Dashboard layer
- Basic dashboard and enhanced dashboard are implemented in Streamlit.
- Enhanced dashboard includes overview metrics, single-customer analysis, model performance, high-risk segment view, and batch prediction workflow.

### Operations and QA
- Automated setup script exists for full database initialization.
- Deployment/start helper scripts exist (`deploy.py`, `start.bat`).
- Test runner exists to execute dependency checks + unit tests.
- Test suites exist for churn prediction, API behavior, and forecasting generation/loading.

## 2. What Is Remaining

### High priority
- Standardize one canonical startup path (currently multiple options: `deploy.py`, `start.bat`, manual commands).
- Remove ambiguity caused by duplicate database file location (`smartgrowth.db` vs `app/smartgrowth.db`).
- Add robust production process management (service supervisors, retries, structured logs).
- Pin and validate dependency compatibility against the exact Python runtime used by team members.

### Medium priority
- Add migration/versioning for database schema changes.
- Add model monitoring hooks (prediction latency, drift signals, failure counters).
- Add API authentication/authorization for production environments.
- Expand dashboard error reporting for failed backend requests.

### Nice to have
- Add CI pipeline (lint + tests + smoke run).
- Add containerization and environment-specific deployment templates.
- Add richer business KPIs and cohort trends in dashboard.

## 3. File-by-File Explanation (Current Workspace)

This section documents active user-facing project files (excluding cache folders and `.git` internals).

## Root files

### `.env.example`
Purpose:
- Template for runtime environment variables.

What code/config does:
- Defines defaults for environment mode, database path, model path, API host/port, dashboard URL/port, and logging level.

### `.gitignore`
Purpose:
- Prevents committing generated/local artifacts.

What code/config does:
- Excludes Python build artifacts, virtual envs, local DB files, notebook checkpoints, IDE files, logs, and local env files.

### `config.py`
Purpose:
- Central configuration module for API, dashboard, ML model, logging, and database paths.

What code does:
- Defines `DatabaseConfig`, `MLModelConfig`, `APIConfig`, `DashboardConfig`, `LoggingConfig`, and `SmartGrowthConfig`.
- Loads `.env` values through Pydantic settings.
- Coerces boolean-like environment values safely.
- Provides helper methods to resolve model/database absolute paths.
- Applies environment-specific overrides (development/staging/production).
- Includes `validate_config()` for sanity checks.

### `deploy.py`
Purpose:
- Programmatic deployment/start orchestration script.

What code does:
- Validates system prerequisites and critical files.
- Installs dependencies from `requirements.txt`.
- Initializes database via `setup_database.py`.
- Runs test suite via `run_tests.py`.
- Starts/stops API and dashboard subprocesses.
- Supports modes: `full`, `setup`, `test`, `start`, `stop`.

### `explore_data.py`
Purpose:
- Data profiling utility for business/ML exploration.

What code does:
- Connects to SQLite and reads `dim_customers` and `customer_summary`.
- Prints dataset size, churn distribution, customer segments, spend tiers, tenure stats, demographics, and churn drivers.
- Computes revenue-at-risk from churned customers.

### `README2.md`
Purpose:
- Main project documentation.

What content does:
- Describes architecture, setup, API usage, dashboard usage, testing, deployment notes, and troubleshooting.

### `requirements.txt`
Purpose:
- Python dependency specification.

What config does:
- Pins FastAPI/Uvicorn, scikit-learn stack, SQLAlchemy, Streamlit/Plotly, requests, Pydantic(+settings), pytest tools, and optional DS extras.

### `run.md`
Purpose:
- Quick operator runbook.

What content does:
- Lists setup commands, startup options, endpoint URLs, curl examples, troubleshooting commands.

### `run_tests.py`
Purpose:
- Convenience test orchestrator.

What code does:
- Checks dependency imports.
- Runs config validation, ML import check, pytest suite, and config smoke check.
- Prints summary and next actions.

### `setup_database.py`
Purpose:
- One-step database bootstrap script.

What code does:
- Creates SQLite DB.
- Executes `database/schema.sql`.
- Loads customer churn data and synthetic daily demand data via `database/loader.py`.
- Prints setup summary and key counts.

### `start.bat`
Purpose:
- Windows convenience launcher.

What script does:
- Verifies Python in venv, ensures DB exists, runs prediction smoke test, then starts API and dashboard in separate terminals.

### `test_api.py`
Purpose:
- API smoke test utility.

What code does:
- Checks model load, API root, health endpoint, customer lookup, and prediction endpoint response.

### `test_prediction.py`
Purpose:
- ML smoke test utility.

What code does:
- Runs one real customer prediction using `predict_customer_churn` and prints risk/probability output.

### `smartgrowth.db`
Purpose:
- Main SQLite database artifact.

What data contains:
- Seeded customer, transaction, demand, and feedback tables according to schema.

## App folder

### `app/main.py`
Purpose:
- FastAPI backend service.

What code does:
- Configures CORS and application metadata.
- Opens DB engine from centralized settings.
- Defines API models (`CustomerData`, `ChurnPredictionResponse`, `BatchPredictionRequest`).
- Exposes endpoints:
  - `/`
  - `/health`
  - `/customer/{customer_id}`
  - `/customers/all`
  - `/predict/churn/{customer_id}`
  - `/predict/churn/manual`
  - `/predict/churn/batch`
  - `/model/info`
  - `/customers/high-risk`

### `app/dashboard.py`
Purpose:
- Lightweight Streamlit dashboard.

What code does:
- Accepts customer ID input.
- Calls API for customer + prediction.
- Displays churn probability, risk level, quick customer snapshot, trend chart, top recommendations.

### `app/dashboard_enhanced.py`
Purpose:
- Full-featured Streamlit UI.

What code does:
- Adds page navigation with 5 workflows:
  - Overview
  - Detailed customer analysis
  - Model performance
  - High-risk customer monitoring
  - Batch prediction
- Includes Plotly charts, risk styling, download buttons, and API health checks.

### `app/smartgrowth.db`
Purpose:
- Secondary DB file in app folder (likely accidental/legacy runtime artifact).

What to do:
- Should be treated carefully to avoid confusion; recommend keeping a single canonical DB path.

## Data folder

### `data/WA_Fn-UseC_-Telco-Customer-Churn.csv`
Purpose:
- Source dataset for churn modeling and initial DB seeding.

### `data/Untitled.ipynb`
Purpose:
- Ad-hoc notebook workspace for experimentation.

## Database folder

### `database/schema.sql`
Purpose:
- Declarative SQL schema for analytics platform.

What SQL defines:
- `dim_customers`
- `fact_transactions`
- `fact_daily_demand`
- `customer_feedback`
- Performance indexes
- Analytical views: `customer_summary`, `demand_summary`

### `database/loader.py`
Purpose:
- Data ingestion and transformation module.

What code does:
- Cleans and maps Telco CSV columns to DB schema.
- Converts data types and handles missing `TotalCharges`.
- Loads `dim_customers` safely (`DELETE + append` if table exists).
- Generates and loads synthetic daily demand into `fact_daily_demand`.

## ML models folder

### `ml_models/__init__.py`
Purpose:
- Package metadata for ML modules.

What code does:
- Declares package version/author and module intent.

### `ml_models/churn/__init__.py`
Purpose:
- Public exports for churn package.

What code does:
- Exposes `ChurnPredictor`, `get_predictor`, and `predict_customer_churn`.

### `ml_models/churn/predictor.py`
Purpose:
- Production churn inference engine.

What code does:
- Loads model artifacts from `joblib`.
- Resolves model and DB paths.
- Looks up customer records by ID.
- Standardizes field names and encodes categorical fields.
- Engineers derived features matching training expectations.
- Produces probability, class, risk level, and business recommendations.
- Supports batch predictions and singleton reuse.
- Trains fallback RandomForest model if artifact load fails.

### `ml_models/churn/churnprediction.ipynb`
Purpose:
- Development notebook used for churn model experimentation/training workflow.

### `ml_models/churn/churn_model.joblib`
Purpose:
- Saved churn model artifact (earlier/baseline version).

### `ml_models/churn/enhanced_churn_model.joblib`
Purpose:
- Saved churn model artifact (enhanced/primary production candidate).

### `ml_models/forecasting/__init__.py`
Purpose:
- Public exports for forecasting package.

What code does:
- Exposes config dataclass + synthetic demand generator function.

### `ml_models/forecasting/data_generator.py`
Purpose:
- Synthetic time-series demand generator for forecasting tests and seed data.

What code does:
- Builds daily data with trend/seasonality, promo/holiday effects, marketing spend, discounts, AOV, and revenue.
- Returns DataFrame with forecasting-ready feature columns.

## Tests folder

### `tests/test_smartgrowth.py`
Purpose:
- Unit/integration-style tests for churn predictor, configuration, and API responses.

What code tests:
- Predictor init/load/fallback/predict/batch/risk logic.
- Config defaults/env override/path validation.
- Feature engineering and dtype handling.
- API response shapes using FastAPI `TestClient` + mocked predictor.

### `tests/test_forecasting.py`
Purpose:
- Forecasting module tests.

What code tests:
- Structure and reproducibility of generated daily demand.
- DB load path for `fact_daily_demand` and CSV output generation.

## 4. Current Health Snapshot

- Churn model inference path: implemented.
- FastAPI prediction endpoints: implemented.
- Streamlit dashboards: implemented.
- Database seeding: implemented.
- Automated test scripts: implemented.

Potential risk to track:
- Duplicate DB artifact under `app/` can cause runtime confusion if process working directory differs.

## 5. Suggested Immediate Next Actions

1. Standardize and enforce a single DB path (root `smartgrowth.db`) across all entry points.
2. Decide one startup script as source of truth (`start.bat` or `deploy.py`) and deprecate the other path in docs.
3. Run full tests after any config/path changes: `python run_tests.py`.
4. Add simple CI workflow for install + tests + API smoke test.
