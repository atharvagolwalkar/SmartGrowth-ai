# 🚀 SmartGrowth AI - Quick Start Guide

## 📋 Prerequisites
- Python 3.8+
- 4GB+ RAM
- 1GB disk space

## 🚀 Quick Deployment
```bash
# One-command deployment
python deploy.py full
```

## 📖 Step-by-Step Setup

### 1. **Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Database Setup** 
```bash
python setup_database.py
```

### 3. **Run Tests** (Optional)
```bash
python run_tests.py
```

### 4. **Start Services**

**Option A: Production Deployment**
```bash
python deploy.py start
```

**Option B: Manual Startup**
```bash
# Terminal 1 (Backend API)
cd app
python main.py

# Terminal 2 (Enhanced Dashboard) 
cd app
streamlit run dashboard_enhanced.py
```

### 5. **Access Services**
- 🌐 **API Backend**: http://localhost:8000
- 📖 **API Documentation**: http://localhost:8000/docs
- 📱 **Dashboard**: http://localhost:8501

## 🔧 Development Commands

### Data Analysis
```bash
python explore_data.py              # Data exploration
sqlite3 smartgrowth.db             # Direct database access
```

### Testing
```bash
python run_tests.py                # Run all tests
pytest tests/ -v                   # Detailed test output
pytest tests/ --cov=.              # Coverage analysis
```

### Configuration
```bash
python config.py                   # Validate configuration
cp .env.example .env               # Setup environment
```

## 📊 API Usage Examples

### Single Prediction
```bash
curl http://localhost:8000/predict/churn/7590-VHVEG
```

### Batch Predictions
```bash
curl -X POST http://localhost:8000/predict/churn/batch \
  -H "Content-Type: application/json" \
  -d '{"customer_ids": ["7590-VHVEG", "5575-GNVDE"]}'
```

### Customer Lookup
```bash
curl http://localhost:8000/customer/7590-VHVEG
```

## 🛑 Stop Services
```bash
python deploy.py stop              # Stop all services
# Or Ctrl+C in terminal
```

## ⚠️  Troubleshooting

### Port Already in Use
```bash
# Use different ports
uvicorn main:app --port 8001
streamlit run dashboard_enhanced.py --server.port 8502
```

### Model Not Found
```bash
# Check model file exists
ls ml_models/churn/enhanced_churn_model.joblib
```

### Dependencies Issues
```bash
pip install -r requirements.txt --upgrade
```

---

**✨ Production-Ready ML Platform**  
*SmartGrowth AI - Customer Intelligence & Churn Prediction*