import pandas as pd
from sqlalchemy import create_engine

# Database connection URL
# Replace 'username', 'password', 'localhost', and 'dbname' with your Postgres details
engine = create_engine('postgresql://username:password@localhost:5432/smartgrowth_db')

# Load the CSV
df = pd.read_csv('data/Telco-Customer-Churn.csv')

# Clean columns to match our schema
df_customers = df[['customerID', 'gender', 'SeniorCitizen', 'Partner', 'Dependents', 
                   'tenure', 'Contract', 'MonthlyCharges', 'TotalCharges', 'Churn']]

# Rename columns to match SQL
df_customers.columns = ['customer_id', 'gender', 'senior_citizen', 'partner', 'dependents', 
                        'tenure_months', 'subscription_type', 'monthly_charges', 'total_charges', 'churn_status']

# Push to Postgres
df_customers.to_sql('dim_customers', engine, if_exists='append', index=False)
print("✅ Successfully loaded real customer data into Postgres!")