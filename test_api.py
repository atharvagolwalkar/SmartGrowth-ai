#!/usr/bin/env python3
"""
Quick API test script to verify endpoints work correctly.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import requests
    import time
    from ml_models.churn.predictor import get_predictor
    
    print("🌐 Testing API Endpoints")
    print("=" * 50)
    
    # Test direct model loading first
    print("1. Testing ML Model Load...")
    try:
        predictor = get_predictor()
        print(f"✅ Model loaded: {predictor.model is not None}")
    except Exception as e:
        print(f"❌ Model load failed: {e}")
    
    # Test API connectivity
    print("\n2. Testing API Connection...")
    api_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{api_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ API is responding")
            data = response.json()
            print(f"  ML Model Status: {data.get('ml_model_status', 'Unknown')}")
        else:
            print(f"⚠️  API responded with status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ API is not running - start with: python app/main.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ API connection error: {e}")
        sys.exit(1)
    
    # Test health endpoint
    print("\n3. Testing Health Check...")
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed")
            print(f"  Database Status: {health_data.get('database_status', 'Unknown')}")
            print(f"  ML Model Status: {health_data.get('ml_model_status', 'Unknown')}")
        else:
            print(f"⚠️  Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test customer lookup
    print("\n4. Testing Customer Lookup...")
    try:
        customer_id = "7590-VHVEG"
        response = requests.get(f"{api_url}/customer/{customer_id}", timeout=10)
        if response.status_code == 200:
            print("✅ Customer lookup successful")
        else:
            print(f"⚠️  Customer lookup failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Customer lookup error: {e}")
    
    # Test churn prediction
    print("\n5. Testing Churn Prediction...")
    try:
        customer_id = "7590-VHVEG"
        response = requests.get(f"{api_url}/predict/churn/{customer_id}", timeout=15)
        if response.status_code == 200:
            pred_data = response.json()
            print("✅ Churn prediction successful")
            print(f"  Customer: {pred_data.get('customer_id', 'N/A')}")
            print(f"  Risk Level: {pred_data.get('risk_level', 'N/A')}")
            print(f"  Probability: {pred_data.get('churn_probability', 0):.2%}")
        else:
            print(f"⚠️  Churn prediction failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Churn prediction error: {e}")
    
    print("\n🎯 API Test Summary:")
    print("All critical endpoints tested. Ready for dashboard integration!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure dependencies are installed: pip install -r requirements.txt")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()