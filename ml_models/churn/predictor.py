"""
Production-ready Churn Prediction System

This module provides a clean, production-ready interface for churn prediction
that can be integrated with FastAPI and other production systems.
"""

import pandas as pd
import numpy as np
import joblib
import os
import logging
from typing import Dict, List, Optional, Union
from sqlalchemy import create_engine, text
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class ChurnPredictor:
    """Production-ready churn prediction system"""
    
    def __init__(self, model_path: Optional[str] = None, db_path: Optional[str] = None):
        """
        Initialize the churn predictor
        
        Args:
            model_path: Path to the saved model file
            db_path: Path to the database for customer data lookup
        """
        self.model_path = model_path or self._get_default_model_path()
        self.db_path = db_path or self._get_default_db_path()
        self.model_artifacts = None
        self.model = None
        self.feature_columns = None
        self.optimal_threshold = 0.5  # Default threshold
        self.performance_metrics = {}
        
        # Load model on initialization
        self._load_model()
    
    def _get_default_db_path(self) -> str:
        """Get default database path, resolving relative to project root"""
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        return os.path.join(project_root, 'smartgrowth.db')
    
    def _get_default_model_path(self) -> str:
        """Get default model path"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, 'enhanced_churn_model.joblib')
    
    def _load_model(self) -> None:
        """Load the trained model and its artifacts"""
        try:
            if os.path.exists(self.model_path):
                logger.info(f"Loading model from {self.model_path}")
                self.model_artifacts = joblib.load(self.model_path)
                
                self.model = self.model_artifacts['model']
                self.feature_columns = self.model_artifacts['feature_columns']
                self.optimal_threshold = self.model_artifacts.get('optimal_threshold', 0.5)
                self.performance_metrics = self.model_artifacts.get('performance_metrics', {})
                
                logger.info("✅ Model loaded successfully")
                logger.info(f"  - Model type: {self.model.__class__.__name__}")
                logger.info(f"  - Features: {len(self.feature_columns)}")
                logger.info(f"  - Optimal threshold: {self.optimal_threshold:.3f}")
                
                if 'auc' in self.performance_metrics:
                    logger.info(f"  - Model AUC: {self.performance_metrics['auc']:.3f}")
                    
            else:
                logger.warning(f"Model file not found: {self.model_path}")
                logger.warning("Using fallback model training...")
                self._train_fallback_model()
                
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            logger.info("Attempting to train fallback model...")
            self._train_fallback_model()
    
    def _train_fallback_model(self) -> None:
        """Train a simple fallback model if saved model is not available"""
        try:
            logger.info("Training fallback model...")
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.preprocessing import LabelEncoder
            
            # Load data from database
            engine = create_engine(f'sqlite:///{self.db_path}')
            df = pd.read_sql("SELECT * FROM dim_customers", engine)
            
            if len(df) == 0:
                raise ValueError("No customer data found in database")
            
            # Simple feature preparation
            features = ['gender', 'senior_citizen', 'partner', 'dependents', 
                       'tenure_months', 'monthly_charges', 'total_charges']
            
            # Encode categorical variables if needed
            le_gender = LabelEncoder()
            if df['gender'].dtype == 'object':
                df['gender_encoded'] = le_gender.fit_transform(df['gender'])
                features[0] = 'gender_encoded'
            
            X = df[features]
            y = df['churn_status']
            
            # Train simple model
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X, y)
            self.feature_columns = features
            self.optimal_threshold = 0.5
            
            logger.info("✅ Fallback model trained successfully")
            
        except Exception as e:
            logger.error(f"Failed to train fallback model: {e}")
            raise
    
    def predict_churn(self, customer_data: Union[Dict, pd.DataFrame, str]) -> Dict:
        """
        Predict churn probability for a customer
        
        Args:
            customer_data: Customer data as dict, DataFrame, or customer_id string
            
        Returns:
            Dict with prediction results and recommendations
        """
        try:
            if self.model is None:
                raise ValueError("Model not loaded")
            
            # Handle different input types
            if isinstance(customer_data, str):
                # Treat as customer_id and lookup from database
                customer_df = self._lookup_customer(customer_data)
                if customer_df is None:
                    raise ValueError(f"Customer {customer_data} not found")
                customer_data = customer_df.iloc[0].to_dict()
            elif isinstance(customer_data, pd.DataFrame):
                customer_data = customer_data.iloc[0].to_dict()
            
            # Prepare features
            features_df = self._prepare_features(customer_data)
            
            # Make prediction
            churn_probability = self.model.predict_proba(features_df)[0, 1]
            
            # Apply optimal threshold
            churn_prediction = churn_probability >= self.optimal_threshold
            
            # Determine risk level
            risk_level = self._get_risk_level(churn_probability)
            
            # Generate recommendations
            recommendations = self._get_recommendations(churn_probability)
            
            # Prepare result
            result = {
                'customer_id': customer_data.get('customer_id', 'unknown'),
                'churn_probability': float(churn_probability),
                'churn_prediction': bool(churn_prediction),
                'risk_level': risk_level,
                'optimal_threshold': float(self.optimal_threshold),
                'recommendations': recommendations,
                'model_info': {
                    'model_name': self.model_artifacts.get('model_name', 'Fallback Model') if self.model_artifacts else 'Fallback Model',
                    'auc_score': self.performance_metrics.get('auc', 'N/A'),
                    'features_used': len(self.feature_columns)
                },
                'prediction_timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in churn prediction: {e}")
            raise
    
    def _lookup_customer(self, customer_id: str) -> Optional[pd.DataFrame]:
        """Lookup customer data from database"""
        try:
            engine = create_engine(f'sqlite:///{self.db_path}')
            with engine.connect() as conn:
                query = text("SELECT * FROM dim_customers WHERE customer_id = :customer_id")
                result = conn.execute(query, {'customer_id': customer_id})
                rows = result.fetchall()
                
                if rows:
                    columns = result.keys()
                    return pd.DataFrame(rows, columns=columns)
                return None
        except Exception as e:
            logger.error(f"Error looking up customer {customer_id}: {e}")
            return None
    
    def _prepare_features(self, customer_data: Dict) -> pd.DataFrame:
        """Prepare features for prediction"""
        try:
            # Create DataFrame from customer data
            df = pd.DataFrame([customer_data])
            
            # First, standardize column names and encode categorical variables
            df = self._standardize_and_encode_data(df)
            
            # Handle different feature sets (enhanced vs basic)
            if 'Contract_Tenure_Interaction' in self.feature_columns:
                # Enhanced feature set - need to engineer features
                df = self._engineer_features(df)
            
            # Select only the features the model was trained on
            available_features = [col for col in self.feature_columns if col in df.columns]
            
            if len(available_features) != len(self.feature_columns):
                logger.warning(f"Missing features: {set(self.feature_columns) - set(available_features)}")
                # Fill missing features with reasonable defaults
                for missing_feature in set(self.feature_columns) - set(available_features):
                    df[missing_feature] = 0
            
            return df[self.feature_columns]
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            raise
    
    def _standardize_and_encode_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names and encode categorical variables"""
        df = df.copy()
        
        # Standardize column names (database -> model format)
        column_mapping = {
            'tenure_months': 'tenure',
            'monthly_charges': 'MonthlyCharges', 
            'total_charges': 'TotalCharges',
            'senior_citizen': 'SeniorCitizen',
            'partner': 'Partner',
            'dependents': 'Dependents',
            'subscription_type': 'Contract',
            'payment_method': 'PaymentMethod'
        }
        
        # Apply column name mapping
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df[new_name] = df[old_name]
        
        # Encode categorical variables to numeric
        # Gender encoding
        if 'gender' in df.columns:
            df['gender'] = df['gender'].map({'Female': 0, 'Male': 1}).fillna(0)
        
        # Boolean fields (ensure they are 0/1)
        boolean_fields = ['SeniorCitizen', 'Partner', 'Dependents']
        for field in boolean_fields:
            if field in df.columns:
                df[field] = df[field].astype(int)
        
        # Contract type encoding
        if 'Contract' in df.columns:
            contract_map = {
                'Month-to-month': 0, 
                'One year': 1, 
                'Two year': 2
            }
            df['Contract'] = df['Contract'].map(contract_map).fillna(0)
        
        # Payment method encoding (simplified)
        if 'PaymentMethod' in df.columns:
            # Encode as: Electronic check=0, Others=1
            df['PaymentMethod'] = (df['PaymentMethod'] != 'Electronic check').astype(int)
        
        # Ensure numeric types for charges
        numeric_fields = ['tenure', 'MonthlyCharges', 'TotalCharges']
        for field in numeric_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0)
        
        return df
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer advanced features (same as training)"""
        df = df.copy()
        
        # Ensure numeric types (using standardized column names)
        numeric_columns = ['tenure', 'MonthlyCharges', 'TotalCharges']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Feature engineering (must match training)
        if 'tenure' in df.columns and 'TotalCharges' in df.columns:
            df['AvgChargesPerMonth'] = df['TotalCharges'] / (df['tenure'] + 1)
        
        if 'tenure' in df.columns:
            # TenureGroup
            df['TenureGroup'] = df['tenure'].apply(
                lambda x: 0 if x <= 12 else (1 if x <= 36 else 2)
            )
            
            # TenureGroup_Detailed
            df['TenureGroup_Detailed'] = pd.cut(
                df['tenure'], bins=[0, 6, 12, 24, 36, 100], labels=[0, 1, 2, 3, 4]
            ).astype(int)
        
        if 'MonthlyCharges' in df.columns:
            # IsHighValue (using median from training - approximately 65)
            df['IsHighValue'] = (df['MonthlyCharges'] > 65).astype(int)
            
            # Revenue_Per_Month_Category
            df['Revenue_Per_Month_Category'] = pd.cut(
                df['MonthlyCharges'], bins=3, labels=[0, 1, 2]
            ).astype(int)
        
        if all(col in df.columns for col in ['SeniorCitizen', 'Partner', 'Dependents']):
            df['SeniorWithFamily'] = (
                df['SeniorCitizen'] & (df['Partner'] | df['Dependents'])
            ).astype(int)
        
        # Interaction features
        if 'Contract' in df.columns and 'tenure' in df.columns:
            df['Contract_Tenure_Interaction'] = df['Contract'] * df['tenure']
        
        if 'MonthlyCharges' in df.columns and 'tenure' in df.columns:
            df['Charges_Tenure_Ratio'] = df['MonthlyCharges'] / (df['tenure'] + 1)
        
        if 'tenure' in df.columns and 'MonthlyCharges' in df.columns:
            df['CustomerValue_Proxy'] = (df['tenure'] * df['MonthlyCharges']) / 100
        
        return df
    
    def _get_risk_level(self, probability: float) -> str:
        """Determine risk level based on probability"""
        if probability >= 0.7:
            return "High Risk"
        elif probability >= 0.4:
            return "Medium Risk"
        else:
            return "Low Risk"
    
    def _get_recommendations(self, probability: float) -> List[str]:
        """Generate business recommendations based on churn probability"""
        if probability >= 0.8:
            return [
                "🔴 URGENT: Immediate retention campaign required",
                "💰 Offer significant discount or upgrade incentive",
                "📞 Personal outreach from customer success team",
                "🎁 Provide exclusive benefits or early access features"
            ]
        elif probability >= 0.6:
            return [
                "⚠️  HIGH RISK: Proactive retention needed", 
                "📧 Send targeted email campaign with value proposition",
                "💬 Schedule customer satisfaction survey",
                "🛠️  Provide additional support or training resources"
            ]
        elif probability >= 0.4:
            return [
                "📊 MEDIUM RISK: Monitor closely",
                "📝 Send product usage tips and best practices",
                "🤝 Invite to user community or webinars", 
                "📈 Share success stories and ROI metrics"
            ]
        else:
            return [
                "✅ LOW RISK: Focus on expansion opportunities",
                "🚀 Introduce premium features or add-ons",
                "🎯 Request referrals or case study participation",
                "📢 Consider as brand advocate for testimonials"
            ]
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        return {
            'model_loaded': self.model is not None,
            'model_type': self.model.__class__.__name__ if self.model else None,
            'feature_count': len(self.feature_columns) if self.feature_columns else 0,
            'optimal_threshold': float(self.optimal_threshold),
            'performance_metrics': self.performance_metrics,
            'model_path': self.model_path,
            'features': self.feature_columns
        }
    
    def batch_predict(self, customer_list: List[Union[str, Dict]]) -> List[Dict]:
        """Predict churn for multiple customers"""
        results = []
        for customer in customer_list:
            try:
                result = self.predict_churn(customer)
                results.append(result)
            except Exception as e:
                logger.error(f"Error predicting for customer {customer}: {e}")
                results.append({
                    'customer_id': customer if isinstance(customer, str) else customer.get('customer_id', 'unknown'),
                    'error': str(e),
                    'prediction_timestamp': datetime.now().isoformat()
                })
        return results


# Global predictor instance (singleton pattern)
_predictor_instance = None

def get_predictor() -> ChurnPredictor:
    """Get the global predictor instance (singleton)"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = ChurnPredictor()
    return _predictor_instance

def predict_customer_churn(customer_data: Union[Dict, str]) -> Dict:
    """Convenience function for quick churn prediction"""
    predictor = get_predictor()
    return predictor.predict_churn(customer_data)
