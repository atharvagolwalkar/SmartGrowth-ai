"""
Database Setup Script for SmartGrowth AI

This is the MAIN script to set up your database.
Creates schema + loads customer data in one go.
"""

import sqlite3
import os
import logging
from sqlalchemy import create_engine
from database.loader import load_customer_data

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_database():
    """Create database schema and load initial data"""
    
    logger.info("🚀 Starting SmartGrowth AI Database Setup...")
    
    try:
        # 1. Create database path and engine
        db_path = 'smartgrowth.db'
        logger.info(f"Creating database at: {os.path.abspath(db_path)}")
        
        # Create SQLAlchemy engine for data loading
        engine = create_engine(f'sqlite:///{db_path}')
        
        # Also create direct SQLite connection for schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 2. Read and execute schema
        logger.info("Creating database schema...")
        with open('database/schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Execute each statement (split by semicolon)
        for statement in schema_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        conn.commit()
        logger.info("✅ Database schema created successfully")
        
        # 3. Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        logger.info(f"Created tables: {[table[0] for table in tables]}")
        
        conn.close()
        
        # 4. Load customer data using the loader module
        logger.info("Loading customer data...")
        success, count = load_customer_data(engine)
        
        if success:
            # 5. Get final statistics
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM dim_customers WHERE churn_status = 1")
            churn_count = cursor.fetchone()[0]
            
            conn.close()
            
            logger.info(f"📊 Database Summary:")
            logger.info(f"  - Total customers: {count}")
            logger.info(f"  - Churned customers: {churn_count}")
            logger.info(f"  - Churn rate: {churn_count/count:.1%}")
            
            print("\n" + "="*60)
            print("🎉 SmartGrowth AI Database Setup Complete!")
            print("="*60)
            print(f"✅ Database created: {os.path.abspath(db_path)}")
            print(f"✅ Customer records loaded: {count:,}")
            print(f"✅ Ready for analysis and ML!")
            print("\nNext steps:")
            print("1. Explore data: python explore_data.py")
            print("2. Query directly: sqlite3 smartgrowth.db")
            print("3. Start building ML models!")
            
            return True
        else:
            logger.error("❌ Failed to load customer data")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    success = setup_database()
    if not success:
        exit(1)