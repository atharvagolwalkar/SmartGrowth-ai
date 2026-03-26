FROM python:3.11-slim

WORKDIR /app

# System deps for Prophet + statsmodels
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-train models if artifacts don't exist
RUN python -c "from ml_models.forecasting.data_generator import generate_daily_demand; print('ML imports OK')" || true

EXPOSE 8000 8501

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]