"""
Database Loader Module for SmartGrowth AI

This module contains functions to load and clean data.
It's imported by setup_database.py - don't run this directly.
"""

import pandas as pd
from sqlalchemy import inspect, text
import os
import logging
from ml_models.forecasting import generate_synthetic_daily_demand

logger = logging.getLogger(__name__)

def clean_customer_data(df):
    """Clean and transform the customer data"""
    logger.info("Cleaning and transforming data...")
    
    # Select relevant columns
    df_customers = df[['customerID', 'gender', 'SeniorCitizen', 'Partner', 'Dependents', 
                       'tenure', 'Contract', 'MonthlyCharges', 'TotalCharges', 'Churn']].copy()
    
    # Rename columns to match SQL schema
    df_customers.columns = ['customer_id', 'gender', 'senior_citizen', 'partner', 'dependents', 
                            'tenure_months', 'subscription_type', 'monthly_charges', 'total_charges', 'churn_status']
    
    # Convert data types
    df_customers['senior_citizen'] = df_customers['senior_citizen'].astype(bool)
    df_customers['partner'] = df_customers['partner'].map({'Yes': True, 'No': False})
    df_customers['dependents'] = df_customers['dependents'].map({'Yes': True, 'No': False})  
    df_customers['churn_status'] = df_customers['churn_status'].map({'Yes': True, 'No': False})
    
    # Handle TotalCharges column (some entries are spaces, need to convert to numeric)
    df_customers['total_charges'] = pd.to_numeric(df_customers['total_charges'], errors='coerce')
    
    # Fill missing total_charges with calculated value
    missing_total = df_customers['total_charges'].isna().sum()
    if missing_total > 0:
        logger.info(f"Found {missing_total} missing total_charges values - filling with calculated values")
        df_customers['total_charges'] = df_customers['total_charges'].fillna(
            df_customers['monthly_charges'] * df_customers['tenure_months']
        )
    
    return df_customers

def load_customer_data(engine):
    """Load customer churn data from CSV into database"""
    try:
        # Check if file exists
        csv_path = 'data/WA_Fn-UseC_-Telco-Customer-Churn.csv'
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return False
            
        # Load the CSV
        logger.info(f"Loading data from {csv_path}")
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from CSV")
        
        # Display basic info about the dataset
        logger.info("Dataset columns: " + str(list(df.columns)))
        logger.info(f"Dataset shape: {df.shape}")
        
        # Clean the data
        df_customers = clean_customer_data(df)
        
        # Display data quality info
        logger.info("Data quality check:")
        logger.info(f"  - Missing values: {df_customers.isnull().sum().sum()}")
        logger.info(f"  - Duplicate customer_ids: {df_customers['customer_id'].duplicated().sum()}")
        logger.info(f"  - Churn rate: {df_customers['churn_status'].mean():.2%}")
        
        # Preserve the schema created from schema.sql instead of replacing it.
        logger.info("Loading data into database...")
        inspector = inspect(engine)
        table_exists = inspector.has_table('dim_customers')

        if table_exists:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM dim_customers"))
            df_customers.to_sql('dim_customers', engine, if_exists='append', index=False)
        else:
            df_customers.to_sql('dim_customers', engine, if_exists='fail', index=False)
        
        # Verify the load using text() wrapper
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dim_customers")).fetchone()
            loaded_count = result[0]
            
        logger.info(f"✅ Successfully loaded {loaded_count} customer records into database!")
        
        # Show sample data
        logger.info("\nSample of loaded data:")
        print(df_customers.head())
        
        return True, loaded_count
        
    except Exception as e:
        logger.error(f"❌ Error loading customer data: {e}")
        return False, 0


def load_daily_demand_data(engine, csv_output_path: str = "data/daily_demand.csv"):
    """Generate and load synthetic daily demand data for forecasting."""
    try:
        logger.info("Generating synthetic daily demand dataset...")
        demand_df = generate_synthetic_daily_demand()

        output_dir = os.path.dirname(csv_output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        demand_df.to_csv(csv_output_path, index=False)

        logger.info(f"Synthetic demand data generated with {len(demand_df)} rows")
        logger.info("Loading synthetic demand data into database...")

        inspector = inspect(engine)
        table_exists = inspector.has_table("fact_daily_demand")

        if table_exists:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM fact_daily_demand"))
            demand_df.to_sql("fact_daily_demand", engine, if_exists="append", index=False)
        else:
            demand_df.to_sql("fact_daily_demand", engine, if_exists="fail", index=False)

        with engine.connect() as conn:
            loaded_count = conn.execute(text("SELECT COUNT(*) FROM fact_daily_demand")).scalar_one()
            date_range = conn.execute(
                text("SELECT MIN(demand_date), MAX(demand_date) FROM fact_daily_demand")
            ).fetchone()

        logger.info(f"Successfully loaded {loaded_count} daily demand records into database")
        logger.info(f"Demand date range: {date_range[0]} to {date_range[1]}")

        return True, int(loaded_count)
    except Exception as e:
        logger.error(f"Error loading daily demand data: {e}")
        return False, 0
