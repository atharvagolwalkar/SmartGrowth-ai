-- 1. Create the Customer Table (for Churn & Segmentation)
CREATE TABLE dim_customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    gender VARCHAR(10),
    senior_citizen BOOLEAN,
    partner BOOLEAN,
    dependents BOOLEAN,
    tenure_months INT,
    subscription_type VARCHAR(20), -- Monthly, Annual
    monthly_charges DECIMAL(10, 2),
    total_charges DECIMAL(10, 2),
    churn_status BOOLEAN DEFAULT FALSE
);

-- 2. Create the Transactions Table (for Demand Forecasting)
CREATE TABLE fact_transactions (
    transaction_id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES dim_customers(customer_id),
    transaction_date DATE,
    amount DECIMAL(10, 2),
    product_category VARCHAR(50)
);

-- 3. Create the Feedback Table (for NLP Insights)
CREATE TABLE customer_feedback (
    feedback_id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES dim_customers(customer_id),
    review_text TEXT,
    sentiment_score FLOAT, -- We will fill this with our ML model later
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);