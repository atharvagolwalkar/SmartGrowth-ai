#!/usr/bin/env python3
"""
SmartGrowth AI Test Runner

Comprehensive testing script that runs all tests and provides detailed reporting.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and capture output"""
    print(f"\n🔍 {description}")
    print("=" * 60)
    
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    
    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ {description} - FAILED")
        if result.stderr:
            print(f"Error: {result.stderr}")
        if result.stdout:
            print(f"Output: {result.stdout}")
    
    return result.returncode == 0

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking Dependencies")
    print("=" * 60)
    
    required_packages = [
        'pytest', 'fastapi', 'streamlit', 'pandas', 
        'scikit-learn', 'plotly', 'sqlalchemy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main test runner"""
    print("🚀 SmartGrowth AI Test Runner")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('requirements.txt'):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install requirements first.")
        sys.exit(1)
    
    # Test steps
    test_steps = [
        ("python config.py", "Configuration Validation"),
        ("python -c \"import ml_models.churn.predictor; print('✅ ML Module Import')\"", "ML Module Import"),
        ("python -m pytest tests/ -v", "Unit Tests"),
        ("python -c \"from config import validate_config; validate_config(); print('✅ Config Validation')\"", "Configuration Tests"),
    ]
    
    # Run all tests
    all_passed = True
    results = {}
    
    for command, description in test_steps:
        success = run_command(command, description)
        results[description] = success
        if not success:
            all_passed = False
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<30} {status}")
    
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Ready for deployment!")
        print("\nNext steps:")
        print("1. Start API: python app/main.py")
        print("2. Start Dashboard: streamlit run app/dashboard_enhanced.py")
        print("3. Open: http://localhost:8000/docs (API)")
        print("4. Open: http://localhost:8501 (Dashboard)")
    else:
        print("\n⚠️  Please fix failing tests before deployment")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())