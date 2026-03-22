"""
Unit tests for SmartGrowth AI Platform.

Run tests with: python -m pytest tests/
"""

import os
import sys
import tempfile
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SmartGrowthConfig, validate_config
from ml_models.churn.predictor import ChurnPredictor


class TestChurnPredictor:
    """Test cases for the ChurnPredictor class."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_model_path = os.path.join(self.temp_dir, "test_model.joblib")
        self.test_db_path = os.path.join(self.temp_dir, "test.db")
        self.mock_model_artifacts = {
            "model": Mock(),
            "feature_columns": ["tenure_months", "monthly_charges", "total_charges"],
            "optimal_threshold": 0.6,
            "performance_metrics": {"auc": 0.85, "precision": 0.75},
            "model_name": "Test Model",
        }
        self.test_customer_data = {
            "customer_id": "TEST-0001",
            "gender": "Female",
            "senior_citizen": 0,
            "partner": 1,
            "dependents": 0,
            "tenure_months": 12,
            "subscription_type": "Month-to-month",
            "payment_method": "Credit card",
            "monthly_charges": 65.0,
            "total_charges": 780.0,
            "churn_status": 0,
        }

    def teardown_method(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_predictor_initialization(self):
        with patch("joblib.load") as mock_load, patch("os.path.exists") as mock_exists:
            mock_load.return_value = self.mock_model_artifacts
            mock_exists.side_effect = lambda path: path == self.test_model_path

            predictor = ChurnPredictor(
                model_path=self.test_model_path,
                db_path=self.test_db_path,
            )

            assert predictor.model is not None
            assert predictor.feature_columns == ["tenure_months", "monthly_charges", "total_charges"]
            assert predictor.optimal_threshold == 0.6

    def test_predictor_fallback_training(self):
        with patch("ml_models.churn.predictor.create_engine"), patch("pandas.read_sql") as mock_read_sql:
            mock_read_sql.return_value = pd.DataFrame([self.test_customer_data])

            predictor = ChurnPredictor(
                model_path="/non/existent/path.joblib",
                db_path=self.test_db_path,
            )

            assert predictor.model is not None
            assert predictor.feature_columns is not None

    def test_predict_churn_with_dict(self):
        with patch("joblib.load") as mock_load, patch("os.path.exists") as mock_exists:
            mock_load.return_value = self.mock_model_artifacts
            self.mock_model_artifacts["model"].predict_proba.return_value = np.array([[0.3, 0.7]])
            mock_exists.side_effect = lambda path: path == self.test_model_path

            predictor = ChurnPredictor(
                model_path=self.test_model_path,
                db_path=self.test_db_path,
            )

            result = predictor.predict_churn(self.test_customer_data)

            assert "churn_probability" in result
            assert "risk_level" in result
            assert "recommendations" in result
            assert result["customer_id"] == "TEST-0001"
            assert isinstance(result["churn_probability"], float)

    def test_predict_churn_with_customer_id(self):
        with patch("joblib.load") as mock_load, patch.object(ChurnPredictor, "_lookup_customer") as mock_lookup:
            mock_load.return_value = self.mock_model_artifacts
            self.mock_model_artifacts["model"].predict_proba.return_value = np.array([[0.4, 0.6]])
            mock_lookup.return_value = pd.DataFrame([self.test_customer_data])

            predictor = ChurnPredictor()
            result = predictor.predict_churn("TEST-0001")

            assert result["customer_id"] == "TEST-0001"
            assert "churn_probability" in result

    def test_risk_level_classification(self):
        with patch("joblib.load") as mock_load:
            mock_load.return_value = self.mock_model_artifacts
            predictor = ChurnPredictor()

            assert predictor._get_risk_level(0.8) == "High Risk"
            assert predictor._get_risk_level(0.5) == "Medium Risk"
            assert predictor._get_risk_level(0.2) == "Low Risk"

    def test_batch_prediction(self):
        with patch("joblib.load") as mock_load, patch.object(ChurnPredictor, "predict_churn") as mock_predict:
            mock_load.return_value = self.mock_model_artifacts
            mock_predict.side_effect = [
                {"customer_id": "TEST-001", "churn_probability": 0.7},
                {"customer_id": "TEST-002", "churn_probability": 0.3},
            ]

            predictor = ChurnPredictor()
            results = predictor.batch_predict(["TEST-001", "TEST-002"])

            assert len(results) == 2
            assert results[0]["customer_id"] == "TEST-001"
            assert results[1]["customer_id"] == "TEST-002"

    def test_model_info(self):
        with patch("joblib.load") as mock_load:
            mock_load.return_value = self.mock_model_artifacts

            predictor = ChurnPredictor()
            info = predictor.get_model_info()

            assert info["model_loaded"] is True
            assert info["feature_count"] == 3
            assert info["optimal_threshold"] == 0.6
            assert "auc" in info["performance_metrics"]


class TestConfiguration:
    """Test cases for configuration management."""

    def test_default_config(self):
        config = SmartGrowthConfig()

        assert config.environment == "development"
        assert config.project_name == "SmartGrowth AI"
        assert config.version == "1.0.0"
        assert config.database.db_path == "smartgrowth.db"
        assert config.api.port == 8000
        assert config.dashboard.port == 8501

    def test_environment_detection(self):
        development = SmartGrowthConfig(environment="development")
        assert development.is_development is True
        assert development.is_production is False

        production = SmartGrowthConfig(environment="production")
        assert production.is_development is False
        assert production.is_production is True

    def test_database_env_prefix(self, monkeypatch):
        monkeypatch.setenv("DATABASE_DB_PATH", "custom.db")
        config = SmartGrowthConfig()
        assert config.database.db_path == "custom.db"

    def test_path_resolution(self):
        config = SmartGrowthConfig()

        db_path = config.get_database_path()
        assert isinstance(db_path, str)
        assert db_path.endswith("smartgrowth.db")

        model_path = config.get_model_path()
        assert isinstance(model_path, str)
        assert "enhanced_churn_model.joblib" in model_path

    def test_config_validation(self):
        with patch("os.path.exists", return_value=True):
            result = validate_config()
            assert result is True


class TestMockData:
    """Test cases for data validation and processing."""

    def test_feature_engineering(self):
        with patch("joblib.load") as mock_load:
            mock_load.return_value = {
                "model": Mock(),
                "feature_columns": ["AvgChargesPerMonth", "TenureGroup", "IsHighValue"],
                "optimal_threshold": 0.5,
            }

            predictor = ChurnPredictor()
            test_data = pd.DataFrame(
                [
                    {
                        "tenure_months": 24,
                        "monthly_charges": 75.0,
                        "total_charges": 1800.0,
                        "senior_citizen": 0,
                        "partner": 1,
                        "dependents": 0,
                        "subscription_type": "One year",
                    }
                ]
            )

            standardized = predictor._standardize_and_encode_data(test_data)
            engineered = predictor._engineer_features(standardized)

            assert "AvgChargesPerMonth" in engineered.columns
            assert "TenureGroup" in engineered.columns
            assert "IsHighValue" in engineered.columns

    def test_data_type_handling(self):
        with patch("joblib.load") as mock_load:
            mock_load.return_value = {
                "model": Mock(),
                "feature_columns": ["tenure", "MonthlyCharges", "TotalCharges"],
                "optimal_threshold": 0.5,
            }

            predictor = ChurnPredictor()
            test_data = {
                "tenure_months": "24",
                "monthly_charges": "75.5",
                "total_charges": "1800.0",
                "customer_id": "TEST-001",
            }

            features_df = predictor._prepare_features(test_data)
            assert features_df["tenure"].dtype in [np.int64, np.float64]
            assert features_df["MonthlyCharges"].dtype in [np.float64]


class TestAPIEndpoints:
    """Test cases for FastAPI endpoints."""

    def setup_method(self):
        self.mock_predictor = Mock()
        self.mock_predictor.model = Mock()
        self.mock_predictor.get_model_info.return_value = {
            "model_loaded": True,
            "model_type": "GradientBoostingClassifier",
            "feature_count": 5,
            "optimal_threshold": 0.55,
            "performance_metrics": {"auc": 0.84},
            "features": ["tenure", "MonthlyCharges"],
        }

        import app.main as main_module

        self.original_predictor = main_module.predictor
        main_module.predictor = self.mock_predictor
        self.client = TestClient(main_module.app)

    def teardown_method(self):
        import app.main as main_module

        main_module.predictor = self.original_predictor

    def test_health_endpoint_structure(self):
        response = self.client.get("/health")

        assert response.status_code == 200
        payload = response.json()
        for key in ["status", "timestamp", "database_status", "ml_model_status", "model_info"]:
            assert key in payload

    def test_prediction_response_structure(self):
        self.mock_predictor.predict_churn.return_value = {
            "customer_id": "TEST-001",
            "churn_probability": 0.65,
            "churn_prediction": True,
            "risk_level": "Medium Risk",
            "optimal_threshold": 0.55,
            "recommendations": ["Action 1", "Action 2"],
            "model_info": {"model_name": "Mock Model", "auc_score": 0.84, "features_used": 5},
            "prediction_timestamp": "2023-12-07T10:00:00",
        }

        response = self.client.get("/predict/churn/TEST-001")

        assert response.status_code == 200
        payload = response.json()
        for key in [
            "customer_id",
            "churn_probability",
            "churn_prediction",
            "risk_level",
            "recommendations",
            "prediction_timestamp",
        ]:
            assert key in payload


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
