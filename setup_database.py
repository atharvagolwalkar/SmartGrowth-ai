"""
Database Setup Script for SmartGrowth AI.

Creates schema and loads seed data for churn and forecasting modules.
"""

import logging
import os
import sqlite3

from sqlalchemy import create_engine

from database.loader import load_customer_data, load_daily_demand_data


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def setup_database():
    """Create database schema and load initial data."""
    logger.info("Starting SmartGrowth AI Database Setup...")

    try:
        db_path = "smartgrowth.db"
        logger.info("Creating database at: %s", os.path.abspath(db_path))

        engine = create_engine(f"sqlite:///{db_path}")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        logger.info("Creating database schema...")
        with open("database/schema.sql", "r", encoding="utf-8") as schema_file:
            schema_sql = schema_file.read()

        cursor.executescript(schema_sql)
        conn.commit()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        logger.info("Created tables: %s", [table[0] for table in tables])
        conn.close()

        logger.info("Loading customer data...")
        customer_success, customer_count = load_customer_data(engine)

        logger.info("Loading synthetic daily demand data...")
        demand_success, demand_count = load_daily_demand_data(engine)

        if not (customer_success and demand_success):
            logger.error("Failed to load database seed data")
            return False

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dim_customers WHERE churn_status = 1")
        churn_count = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(orders), AVG(revenue) FROM fact_daily_demand")
        avg_orders, avg_revenue = cursor.fetchone()
        conn.close()

        logger.info("Database Summary:")
        logger.info("  - Total customers: %s", customer_count)
        logger.info("  - Churned customers: %s", churn_count)
        logger.info("  - Churn rate: %.1f%%", (churn_count / customer_count) * 100)
        logger.info("  - Daily demand rows: %s", demand_count)
        logger.info("  - Average daily orders: %.1f", avg_orders)
        logger.info("  - Average daily revenue: $%0.2f", avg_revenue)

        print("\n" + "=" * 60)
        print("SmartGrowth AI Database Setup Complete")
        print("=" * 60)
        print(f"Database created: {os.path.abspath(db_path)}")
        print(f"Customer records loaded: {customer_count:,}")
        print(f"Daily demand rows loaded: {demand_count:,}")
        print("Ready for analysis and ML")
        print("\nNext steps:")
        print("1. Explore data: python explore_data.py")
        print("2. Build forecasting model on fact_daily_demand")
        print("3. Start building ML models")

        return True
    except Exception as exc:
        logger.error("Database setup failed: %s", exc)
        return False


if __name__ == "__main__":
    success = setup_database()
    if not success:
        raise SystemExit(1)
