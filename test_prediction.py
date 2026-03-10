#!/usr/bin/env python3
"""
Quick test script to verify ML model predictions work correctly.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ml_models.churn.predictor import predict_customer_churn
    
    print("🔍 Testing ML Model Predictions")
    print("=" * 50)
    
    # Test with a real customer ID
    customer_id = "7590-VHVEG"
    print(f"Testing prediction for customer: {customer_id}")
    
    result = predict_customer_churn(customer_id)
    
    if 'error' not in result:
        print("✅ Prediction successful!")
        print(f"  Customer ID: {result.get('customer_id', 'N/A')}")
        print(f"  Risk Level: {result.get('risk_level', 'N/A')}")
        print(f"  Probability: {result.get('churn_probability', 0):.2%}")
        print(f"  Recommendations: {len(result.get('recommendations', []))} items")
    else:
        print(f"❌ Prediction failed: {result.get('error', 'Unknown error')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()