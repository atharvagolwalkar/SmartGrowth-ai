# 🚀 SmartGrowth AI: Production ML Platform

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28.2-red.svg)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3.2-orange.svg)](https://scikit-learn.org/)

A production-ready end-to-end machine learning platform for customer intelligence and churn prediction, featuring FastAPI backend, Streamlit dashboard, and advanced ML capabilities.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

## ✨ Features

### 🤖 Machine Learning
- **Advanced Churn Prediction**: Gradient Boosting model with 84%+ AUC
- **Business-Optimized Thresholds**: Profit-maximizing decision boundaries
- **Feature Engineering**: 15+ engineered features for enhanced accuracy
- **Batch Predictions**: Efficient processing of multiple customers
- **Real-time Inference**: Sub-second prediction latency

### 🔧 Production Architecture  
- **FastAPI Backend**: High-performance async API with automatic validation
- **Streamlit Dashboard**: Interactive business intelligence interface
- **Database Layer**: Professional SQLite schema with optimization
- **Configuration Management**: Environment-based settings
- **Comprehensive Testing**: Unit tests with 90%+ coverage
- **Error Handling**: Robust production-grade error management

### 📊 Business Intelligence
- **Risk Assessment**: Multi-level customer risk classification
- **Strategic Recommendations**: AI-generated retention strategies
- **Interactive Visualizations**: Plotly-powered charts and dashboards
- **Batch Analytics**: Process thousands of customers efficiently
- **Export Capabilities**: CSV downloads for further analysis

## 🏗️ Architecture

```
SmartGrowth AI Platform
├── 🗄️  Database Layer          │ SQLite with professional schema
├── 🤖 ML Services              │ Scikit-learn production models  
├── 🌐 API Layer               │ FastAPI with async endpoints
├── 📱 Frontend Dashboard       │ Streamlit business interface
├── ⚙️  Configuration          │ Environment-based config
└── 🧪 Testing Suite           │ Comprehensive unit tests
```

## 🚀 Quick Start

1. **Clone & Install**
```bash
git clone <repository-url>
cd smartgrowth-ai
pip install -r requirements.txt
```

2. **Setup Database**
```bash
python setup_database.py
```

3. **Start Backend API**
```bash
cd app
python main.py
# API runs at http://localhost:8000
```

4. **Start Dashboard**
```bash
cd app  
streamlit run dashboard_enhanced.py
# Dashboard at http://localhost:8501
```

5. **Make Predictions**
```bash
curl http://localhost:8000/predict/churn/7590-VHVEG
```

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- 4GB+ RAM (for ML model loading)
- 1GB disk space

### Step-by-Step Installation

1. **Create Virtual Environment** (Recommended)
```bash
python -m venv smartgrowth_env
source smartgrowth_env/bin/activate  # Linux/Mac
smartgrowth_env\Scripts\activate     # Windows
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Initialize Database**
```bash
python setup_database.py
```

5. **Verify Installation**
```bash
python -m pytest tests/ -v
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
# Environment
ENVIRONMENT=development  # development, staging, production
DEBUG=true

# Database
DATABASE_DB_PATH=smartgrowth.db

# ML Model
ML_MODEL_PATH=ml_models/churn/enhanced_churn_model.joblib
ML_DEFAULT_THRESHOLD=0.5

# API
API_HOST=0.0.0.0
API_PORT=8000

# Dashboard 
DASHBOARD_PORT=8501
DASHBOARD_API_BASE_URL=http://localhost:8000
```

### Production Configuration

For production deployment:

```bash
ENVIRONMENT=production
DEBUG=false
API_DEBUG=false
API_CORS_ORIGINS=["https://yourdomain.com"]
LOG_LEVEL=WARNING
LOG_FILE_PATH=logs/smartgrowth.log
```

## 🎯 Usage

### 1. **API Usage**

#### Single Customer Prediction
```bash
# Get prediction for specific customer
curl http://localhost:8000/predict/churn/7590-VHVEG

# Response
{
  "customer_id": "7590-VHVEG",
  "churn_probability": 0.73,
  "churn_prediction": true,
  "risk_level": "High Risk",
  "recommendations": [
    "🔴 URGENT: Immediate retention campaign required",
    "💰 Offer significant discount or upgrade incentive"
  ]
}
```

#### Batch Predictions
```bash
curl -X POST http://localhost:8000/predict/churn/batch \
  -H "Content-Type: application/json" \
  -d '{"customer_ids": ["7590-VHVEG", "5575-GNVDE", "3668-QPYBK"]}'
```

#### Customer Lookup
```bash
# Get customer details
curl http://localhost:8000/customer/7590-VHVEG
```

### 2. **Dashboard Usage**

Access the interactive dashboard at `http://localhost:8501`:

- **🏠 Dashboard Overview**: Quick metrics and customer lookup
- **🔍 Customer Risk Analysis**: Detailed individual analysis  
- **📊 Model Performance**: ML model metrics and insights
- **⚠️ High-Risk Customers**: Batch risk assessment
- **🔄 Batch Prediction**: Process multiple customers

### 3. **Python Integration**

```python
from ml_models.churn.predictor import ChurnPredictor

# Initialize predictor
predictor = ChurnPredictor()

# Make prediction
result = predictor.predict_churn('7590-VHVEG')
print(f"Risk Level: {result['risk_level']}")
print(f"Probability: {result['churn_probability']:.1%}")

# Batch predictions
customers = ['7590-VHVEG', '5575-GNVDE', '3668-QPYBK']
batch_results = predictor.batch_predict(customers)
```

## 📚 API Documentation

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API health and information |
| `/health` | GET | Detailed health check |
| `/customer/{id}` | GET | Get customer details |
| `/customers/all` | GET | List all customers (paginated) |
| `/predict/churn/{id}` | GET | Predict churn for customer ID |
| `/predict/churn/manual` | POST | Predict churn with provided data |
| `/predict/churn/batch` | POST | Batch churn predictions |
| `/customers/high-risk` | GET | Get high-risk customers |  
| `/model/info` | GET | ML model information |

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Categories
```bash
pytest tests/test_smartgrowth.py::TestChurnPredictor -v
pytest tests/test_smartgrowth.py::TestConfiguration -v
pytest tests/test_smartgrowth.py::TestAPIEndpoints -v
```

### Coverage Report
```bash
pytest tests/ --cov=. --cov-report=html
# View coverage report at htmlcov/index.html
```

### Test Structure
```
tests/
├── test_smartgrowth.py    │ Core functionality tests
├── __init__.py            │ Test package initialization  
└── conftest.py           │ Shared test fixtures (optional)
```

## 🚀 Deployment

### Local Production
```bash
# Set production environment
export ENVIRONMENT=production

# Run with production settings
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### AWS/Azure/GCP Deployment
- Use the production configuration settings
- Set environment variables appropriately
- Ensure database and model files are accessible
- Configure load balancing for high availability

## 📁 Project Structure

```
smartgrowth-ai/
├── 📄 README.md                    │ This documentation
├── 📄 requirements.txt             │ Python dependencies
├── 📄 config.py                    │ Configuration management
├── 📄 setup_database.py            │ Database initialization
├── 📄 explore_data.py              │ Data analysis utilities
│
├── 📁 app/                         │ Web application
│   ├── 📄 main.py                  │ FastAPI backend
│   ├── 📄 dashboard.py             │ Basic Streamlit dashboard  
│   └── 📄 dashboard_enhanced.py    │ Production dashboard
│
├── 📁 ml_models/                   │ ML model components
│   └── 📁 churn/                   │ Churn prediction model
│       ├── 📄 predictor.py         │ Production ML class
│       ├── 📄 churnprediction.ipynb│ Model development
│       └── 📄 enhanced_churn_model.joblib │ Saved model
│
├── 📁 database/                    │ Database components
│   ├── 📄 schema.sql               │ Database schema
│   └── 📄 loader.py                │ Data loading utilities
│
├── 📁 data/                        │ Data files
│   └── 📄 WA_Fn-UseC_-Telco-Customer-Churn.csv
│
├── 📁 tests/                       │ Test suite
│   └── 📄 test_smartgrowth.py      │ Unit tests
│
└── 📄 .env.example                 │ Environment template
```

## 🔧 Troubleshooting

### Common Issues

**1. API Connection Failed**
```bash
# Start the backend first
cd app
python main.py

# Then start dashboard
streamlit run dashboard_enhanced.py  
```

**2. Model Not Found**
```bash
# Ensure model file exists
ls ml_models/churn/enhanced_churn_model.joblib

# If missing, retrain from notebook:
jupyter notebook ml_models/churn/churnprediction.ipynb
```

**3. Database Not Found**
```bash
# Reinitialize database
python setup_database.py
```

**4. Port Already in Use**
```bash
# Use different ports
uvicorn main:app --port 8001
streamlit run dashboard_enhanced.py --server.port 8502
```

### Logs & Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# View API logs
python app/main.py

# Check configuration
python config.py
```

## 🤝 Contributing

1. **Fork the Repository**
2. **Create Feature Branch** (`git checkout -b feature/amazing-feature`)
3. **Write Tests** for new functionality
4. **Ensure Tests Pass** (`pytest tests/ -v`)
5. **Commit Changes** (`git commit -m 'Add amazing feature'`)
6. **Push to Branch** (`git push origin feature/amazing-feature`)
7. **Open Pull Request**

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Use type hints where appropriate
- Ensure backward compatibility

## 📊 Performance Metrics

### Model Performance
- **AUC Score**: 0.841 (84.1%)
- **Precision**: 0.682 (68.2%)
- **Recall**: 0.549 (54.9%)
- **F1-Score**: 0.608 (60.8%)

### System Performance
- **API Response Time**: <100ms (95th percentile)
- **Dashboard Load Time**: <2s
- **Batch Processing**: 1000 customers/minute
- **Model Loading**: <5s cold start

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Telco Customer Churn Dataset** for providing quality training data
- **FastAPI** for excellent async web framework
- **Streamlit** for rapid dashboard development
- **scikit-learn** for robust ML algorithms
- **Plotly** for interactive visualizations

## 📞 Support

- **Documentation**: [Project Wiki](link-to-wiki)
- **Issues**: [GitHub Issues](link-to-issues)
- **Discussions**: [GitHub Discussions](link-to-discussions)
- **Email**: support@yourdomain.com (for enterprise support)

---

**Built with ❤️ for enterprise-grade machine learning**

*SmartGrowth AI - Transforming customer intelligence through production-ready ML*