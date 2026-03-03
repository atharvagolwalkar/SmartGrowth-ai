"""
Data Explorer for SmartGrowth AI

Simple script to explore and analyze the loaded customer data.
Helps you understand your dataset before building ML models.
"""

import sqlite3
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def explore_data():
    """Explore the customer dataset"""
    
    try:
        # Connect to database
        conn = sqlite3.connect('smartgrowth.db')
        
        print("🔍 SmartGrowth AI Data Explorer")
        print("="*50)
        
        # 1. Basic dataset info
        df = pd.read_sql("SELECT * FROM dim_customers", conn)
        print(f"\n📊 Dataset Overview:")
        print(f"  - Total customers: {len(df):,}")
        print(f"  - Features: {len(df.columns)}")
        print(f"  - Memory usage: {df.memory_usage().sum() / 1024:.1f} KB")
        
        # 2. Target variable analysis
        churn_rate = df['churn_status'].mean()
        print(f"\n🎯 Target Variable (Churn):")
        print(f"  - Churn rate: {churn_rate:.1%}")
        print(f"  - Churned customers: {df['churn_status'].sum():,}")
        print(f"  - Retained customers: {(~df['churn_status']).sum():,}")
        
        # 3. Customer segments
        print(f"\n👥 Customer Segments:")
        segments = pd.read_sql("SELECT customer_segment, COUNT(*) as count FROM customer_summary GROUP BY customer_segment ORDER BY count DESC", conn)
        for _, row in segments.iterrows():
            print(f"  - {row['customer_segment']}: {row['count']:,}")
        
        # 4. Spending analysis
        print(f"\n💰 Spending Analysis:")
        spending = pd.read_sql("SELECT spending_tier, COUNT(*) as count, AVG(monthly_charges) as avg_monthly FROM customer_summary GROUP BY spending_tier ORDER BY avg_monthly", conn)
        for _, row in spending.iterrows():
            print(f"  - {row['spending_tier']} spenders: {row['count']:,} customers (avg: ${row['avg_monthly']:.2f}/month)")
        
        # 5. Tenure analysis
        print(f"\n⏰ Customer Tenure:")
        print(f"  - Average tenure: {df['tenure_months'].mean():.1f} months")
        print(f"  - Median tenure: {df['tenure_months'].median():.1f} months")
        print(f"  - New customers (< 12 months): {(df['tenure_months'] < 12).sum():,}")
        print(f"  - Long-term customers (> 36 months): {(df['tenure_months'] > 36).sum():,}")
        
        # 6. Contract type analysis
        print(f"\n📋 Contract Types:")
        contracts = df['subscription_type'].value_counts()
        for contract_type, count in contracts.items():
            pct = count / len(df) * 100
            print(f"  - {contract_type}: {count:,} ({pct:.1f}%)")
        
        # 7. Demographics
        print(f"\n👤 Demographics:")
        print(f"  - Female customers: {(df['gender'] == 'Female').sum():,} ({(df['gender'] == 'Female').mean():.1%})")
        print(f"  - Male customers: {(df['gender'] == 'Male').sum():,} ({(df['gender'] == 'Male').mean():.1%})")
        print(f"  - Senior citizens: {df['senior_citizen'].sum():,} ({df['senior_citizen'].mean():.1%})")
        print(f"  - Customers with partners: {df['partner'].sum():,} ({df['partner'].mean():.1%})")
        print(f"  - Customers with dependents: {df['dependents'].sum():,} ({df['dependents'].mean():.1%})")
        
        # 8. Key insights for ML
        print(f"\n🤖 Key Insights for ML Models:")
        
        # Churn by contract type
        churn_by_contract = df.groupby('subscription_type')['churn_status'].mean().sort_values(ascending=False)
        print(f"  - Highest churn rate: {churn_by_contract.index[0]} ({churn_by_contract.iloc[0]:.1%})")
        print(f"  - Lowest churn rate: {churn_by_contract.index[-1]} ({churn_by_contract.iloc[-1]:.1%})")
        
        # Churn by tenure
        short_tenure_churn = df[df['tenure_months'] < 12]['churn_status'].mean()
        long_tenure_churn = df[df['tenure_months'] > 36]['churn_status'].mean()
        print(f"  - New customer churn rate: {short_tenure_churn:.1%}")
        print(f"  - Long-term customer churn rate: {long_tenure_churn:.1%}")
        
        # Revenue impact - Fixed boolean indexing
        churned_customers = df[df['churn_status'] == True]  # Explicit boolean comparison
        churned_revenue = churned_customers['monthly_charges'].sum()
        total_revenue = df['monthly_charges'].sum()
        print(f"  - Revenue at risk from churn: ${churned_revenue:,.0f}/month ({churned_revenue/total_revenue:.1%})")
        
        conn.close()
        
        print(f"\n✅ Data exploration complete!")
        print(f"💡 Your data is ready for machine learning!")
        
    except Exception as e:
        logger.error(f"❌ Error exploring data: {e}")

if __name__ == "__main__":
    explore_data()