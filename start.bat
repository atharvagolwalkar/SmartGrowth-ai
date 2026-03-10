@echo off
echo ====================================================
echo            🚀 SmartGrowth AI Launcher  
echo ====================================================

echo 🔧 Setting up virtual environment...
c:/Users/athar/smartgrowth-ai/venv/Scripts/python.exe -c "print('✅ Python environment ready')"

echo.
echo 🗄️  Checking database...
if exist smartgrowth.db (
    echo ✅ Database found
) else (
    echo 📦 Setting up database...
    c:/Users/athar/smartgrowth-ai/venv/Scripts/python.exe setup_database.py
)

echo.
echo 🧪 Running quick test...
c:/Users/athar/smartgrowth-ai/venv/Scripts/python.exe test_prediction.py

echo.
echo ====================================================
echo            🌐 Starting Services...
echo ====================================================
echo.
echo 📱 Opening services in new terminal windows...
echo.
echo 1. API Backend (Port 8000)
start "SmartGrowth API" cmd /k "cd app && c:/Users/athar/smartgrowth-ai/venv/Scripts/python.exe main.py"

echo.
echo 2. Dashboard (Port 8501)  
start "SmartGrowth Dashboard" cmd /k "cd app && c:/Users/athar/smartgrowth-ai/venv/Scripts/streamlit run dashboard_enhanced.py"

echo.
echo ====================================================
echo            ✅ SmartGrowth AI is Starting!
echo ====================================================
echo.
echo 📍 Access your services at:
echo   • API Backend:     http://localhost:8000
echo   • API Docs:        http://localhost:8000/docs
echo   • Dashboard:       http://localhost:8501
echo.
echo ⏳ Services are starting in separate windows...
echo    Give them 10-15 seconds to fully load.
echo.
echo 🧪 Test prediction:  
echo    curl http://localhost:8000/predict/churn/7590-VHVEG
echo.
pause