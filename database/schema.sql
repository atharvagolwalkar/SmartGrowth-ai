-- SmartGrowth AI Database Schema
-- SQLite version (for development) - can be easily adapted to PostgreSQL later

-- 1. Customer Dimension Table (Core entity for churn prediction & segmentation)
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    gender VARCHAR(10) NOT NULL,
    senior_citizen BOOLEAN NOT NULL DEFAULT 0,
    partner BOOLEAN NOT NULL DEFAULT 0,
    dependents BOOLEAN NOT NULL DEFAULT 0,
    tenure_months INTEGER NOT NULL,
    subscription_type VARCHAR(20) NOT NULL, -- Month-to-month, One year, Two year
    monthly_charges REAL NOT NULL,
    total_charges REAL NOT NULL,
    churn_status BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Transaction Fact Table (for future demand forecasting)
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id VARCHAR(50) NOT NULL,
    transaction_date DATE NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    product_category VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id)
);

-- 3. Customer Feedback Table (for future NLP insights)  
CREATE TABLE IF NOT EXISTS customer_feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id VARCHAR(50) NOT NULL,
    review_text TEXT NOT NULL,
    sentiment_score REAL CHECK (sentiment_score >= -1 AND sentiment_score <= 1), -- Range: -1 to +1
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_customers_churn ON dim_customers(churn_status);
CREATE INDEX IF NOT EXISTS idx_customers_tenure ON dim_customers(tenure_months);
CREATE INDEX IF NOT EXISTS idx_customers_charges ON dim_customers(monthly_charges);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_customer ON fact_transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_feedback_customer ON customer_feedback(customer_id);

-- Create some useful views for analysis
CREATE VIEW IF NOT EXISTS customer_summary AS
SELECT 
    customer_id,
    gender,
    senior_citizen,
    partner,
    dependents,
    tenure_months,
    subscription_type,
    monthly_charges,
    total_charges,
    churn_status,
    CASE 
        WHEN churn_status = 1 THEN 'Churned'
        WHEN tenure_months >= 36 THEN 'Long-term'
        WHEN monthly_charges > 70 THEN 'High-value'
        WHEN tenure_months < 12 THEN 'New'
        ELSE 'Regular'
    END as customer_segment,
    CASE
        WHEN monthly_charges < 35 THEN 'Low'
        WHEN monthly_charges < 65 THEN 'Medium' 
        ELSE 'High'
    END as spending_tier
FROM dim_customers;