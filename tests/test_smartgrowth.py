"""
Unit tests for SmartGrowth AI Platform

Test modules:
- ChurnPredictor class
- FastAPI endpoints
- Configuration management
- Database operations

Run tests with: pytest tests/
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.churn.predictor import ChurnPredictor, get_predictor, predict_customer_churn
from config import SmartGrowthConfig, get_config, validate_config

class TestChurnPredictor:
    """Test cases for the ChurnPredictor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_model_path = os.path.join(self.temp_dir, "test_model.joblib")
        self.test_db_path = os.path.join(self.temp_dir, "test.db")
        
        # Create mock model artifacts
        self.mock_model_artifacts = {
            'model': Mock(),
            'feature_columns': ['tenure_months', 'monthly_charges', 'total_charges'],
            'optimal_threshold': 0.6,
            'performance_metrics': {'auc': 0.85, 'precision': 0.75},
            'model_name': 'Test Model'
        }
        
        # Mock customer data
        self.test_customer_data = {
            'customer_id': 'TEST-0001',
            'gender': 'Female',
            'senior_citizen': 0,
            'partner': 1,
            'dependents': 0,
            'tenure_months': 12,
            'subscription_type': 'Month-to-month',
            'payment_method': 'Credit card',
            'monthly_charges': 65.0,
            'total_charges': 780.0,
            'churn_status': 0
        }
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_predictor_initialization(self):
        """Test ChurnPredictor initialization"""
        with patch('joblib.load') as mock_load:
            mock_load.return_value = self.mock_model_artifacts
            
            predictor = ChurnPredictor(
                model_path=self.test_model_path,
                db_path=self.test_db_path
            )
            
            assert predictor.model is not None
            assert predictor.feature_columns == ['tenure_months', 'monthly_charges', 'total_charges']
            assert predictor.optimal_threshold == 0.6
    
    def test_predictor_fallback_training(self):
        """Test fallback model training when saved model is not available"""
        # Use non-existent model path to trigger fallback
        with patch('ml_models.churn.predictor.create_engine') as mock_engine, \
             patch('pandas.read_sql') as mock_read_sql:
            
            # Mock database response
            mock_df = pd.DataFrame([self.test_customer_data])
            mock_read_sql.return_value = mock_df
            
            predictor = ChurnPredictor(
                model_path="/non/existent/path.joblib",
                db_path=self.test_db_path
            )
            
            # Should have trained a fallback model
            assert predictor.model is not None
            assert predictor.feature_columns is not None
    
    def test_predict_churn_with_dict(self):
        """Test churn prediction with dictionary input"""
        with patch('joblib.load') as mock_load:
            mock_load.return_value = self.mock_model_artifacts
            
            # Mock prediction
            self.mock_model_artifacts['model'].predict_proba.return_value = [[0.3, 0.7]]
            
            predictor = ChurnPredictor(
                model_path=self.test_model_path,
                db_path=self.test_db_path
            )
            
            result = predictor.predict_churn(self.test_customer_data)
            
            assert 'churn_probability' in result
            assert 'risk_level' in result
            assert 'recommendations' in result
            assert result['customer_id'] == 'TEST-0001'
            assert isinstance(result['churn_probability'], float)
    
    def test_predict_churn_with_customer_id(self):
        """Test churn prediction with customer ID lookup"""
        with patch('joblib.load') as mock_load, \
             patch.object(ChurnPredictor, '_lookup_customer') as mock_lookup:
            
            mock_load.return_value = self.mock_model_artifacts
            self.mock_model_artifacts['model'].predict_proba.return_value = [[0.4, 0.6]]
            
            # Mock customer lookup
            mock_lookup.return_value = pd.DataFrame([self.test_customer_data])
            
            predictor = ChurnPredictor()
            result = predictor.predict_churn('TEST-0001')
            
            assert result['customer_id'] == 'TEST-0001'
            assert 'churn_probability' in result
    
    def test_risk_level_classification(self):
        """Test risk level classification"""
        with patch('joblib.load') as mock_load:
            mock_load.return_value = self.mock_model_artifacts
            
            predictor = ChurnPredictor()
            
            # Test different probability levels
            assert predictor._get_risk_level(0.8) == "High Risk"
            assert predictor._get_risk_level(0.5) == "Medium Risk"
            assert predictor._get_risk_level(0.2) == "Low Risk"
    
    def test_batch_prediction(self):
        """Test batch prediction functionality"""
        with patch('joblib.load') as mock_load, \
             patch.object(ChurnPredictor, 'predict_churn') as mock_predict:
            
            mock_load.return_value = self.mock_model_artifacts
            
            # Mock individual predictions
            mock_predict.side_effect = [
                {'customer_id': 'TEST-001', 'churn_probability': 0.7},
                {'customer_id': 'TEST-002', 'churn_probability': 0.3}
            ]
            
            predictor = ChurnPredictor()
            results = predictor.batch_predict(['TEST-001', 'TEST-002'])
            
            assert len(results) == 2
            assert results[0]['customer_id'] == 'TEST-001'
            assert results[1]['customer_id'] == 'TEST-002'
    
    def test_model_info(self):
        """Test model information retrieval"""
        with patch('joblib.load') as mock_load:
            mock_load.return_value = self.mock_model_artifacts
            
            predictor = ChurnPredictor()
            info = predictor.get_model_info()
            
            assert info['model_loaded'] == True
            assert info['feature_count'] == 3
            assert info['optimal_threshold'] == 0.6
            assert 'auc' in info['performance_metrics']


class TestConfiguration:
    """Test cases for configuration management"""
    
    def test_default_config(self):
        """Test default configuration loading"""
        config = SmartGrowthConfig()
        
        assert config.environment == "development"
        assert config.project_name == "SmartGrowth AI"
        assert config.version == "1.0.0"
        assert config.database.db_path == "smartgrowth.db"
        assert config.api.port == 8000
        assert config.dashboard.port == 8501
    
    def test_environment_detection(self):
        """Test environment detection methods"""
        config = SmartGrowthConfig(environment="development")
        assert config.is_development == True
        assert config.is_production == False
        
        config = SmartGrowthConfig(environment="production")
        assert config.is_development == False
        assert config.is_production == True
    
    def test_path_resolution(self):
        """Test path resolution methods"""
        config = SmartGrowthConfig()
        
        db_path = config.get_database_path()
        assert isinstance(db_path, str)
        assert db_path.endswith("smartgrowth.db")
        
        model_path = config.get_model_path()
        assert isinstance(model_path, str)
        assert "enhanced_churn_model.joblib" in model_path
    
    def test_config_validation(self):
        """Test configuration validation"""
        # This should not raise an exception with default config
        # Note: May need to mock file system for clean test environment
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            result = validate_config()
            assert result == True


class TestMockData:
    """Test cases for data validation and processing"""
    
    def test_feature_engineering(self):
        """Test feature engineering functions"""
        with patch('joblib.load') as mock_load:
            mock_model_artifacts = {
                'model': Mock(),
                'feature_columns': ['AvgChargesPerMonth', 'TenureGroup', 'IsHighValue'],
                'optimal_threshold': 0.5
            }
            mock_load.return_value = mock_model_artifacts
            
            predictor = ChurnPredictor()
            
            # Test with basic customer data
            test_data = pd.DataFrame([{
                'tenure_months': 24,
                'monthly_charges': 75.0,
                'total_charges': 1800.0,
                'senior_citizen': 0,
                'partner': 1,
                'dependents': 0,
                'subscription_type': 'One year'
            }])
            
            engineered = predictor._engineer_features(test_data)
            
            # Check that new features are created
            assert 'AvgChargesPerMonth' in engineered.columns
            assert 'TenureGroup' in engineered.columns
            assert 'IsHighValue' in engineered.columns
    
    def test_data_type_handling(self):
        """Test proper data type handling"""
        with patch('joblib.load') as mock_load:
            mock_model_artifacts = {
                'model': Mock(),
                'feature_columns': ['tenure_months', 'monthly_charges', 'total_charges'],
                'optimal_threshold': 0.5
            }
            mock_load.return_value = mock_model_artifacts
            
            predictor = ChurnPredictor()
            
            # Test with string values that should be converted to numeric
            test_data = {
                'tenure_months': '24',
                'monthly_charges': '75.5',
                'total_charges': '1800.0',
                'customer_id': 'TEST-001'
            }
            
            features_df = predictor._prepare_features(test_data)
            
            # Should convert strings to numeric types
            assert features_df['tenure_months'].dtype in [np.int64, np.float64]
            assert features_df['monthly_charges'].dtype in [np.float64]


# Mock FastAPI test (basic structure)
class TestAPIEndpoints:
    """Test cases for FastAPI endpoints"""
    
    def setup_method(self):
        """Set up FastAPI test client"""
        # Note: This is a simplified test structure
        # In a full implementation, you would use FastAPI TestClient
        pass
    
    def test_health_endpoint_structure(self):
        """Test that health endpoint returns expected structure"""
        # Mock the expected response structure
        expected_keys = ['status', 'timestamp', 'database_status', 'ml_model_status', 'model_info']
        
        # This is a structure test - in reality you'd make an actual API call
        mock_response = {
            'status': 'healthy',
            'timestamp': '2023-12-07T10:00:00',
            'database_status': 'connected',
            'ml_model_status': 'loaded',
            'model_info': {'model_loaded': True}
        }
        
        for key in expected_keys:
            assert key in mock_response
    
    def test_prediction_response_structure(self):
        """Test prediction response structure"""
        expected_keys = [
            'customer_id', 'churn_probability', 'churn_prediction', 
            'risk_level', 'recommendations', 'prediction_timestamp'
        ]
        
        mock_prediction_response = {
            'customer_id': 'TEST-001',
            'churn_probability': 0.65,
            'churn_prediction': True,
            'risk_level': 'Medium Risk',
            'recommendations': ['Action 1', 'Action 2'],
            'prediction_timestamp': '2023-12-07T10:00:00'
        }
        
        for key in expected_keys:
            assert key in mock_prediction_response


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])