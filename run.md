Set up your database:  python setup_database.py

Explore your data:  python explore_data.py

Query your data directly: sqlite3 smartgrowth.db


Terminal 1 (Backend): uvicorn app.main:app --reload

Terminal 2 (Frontend): streamlit run app/dashboard.py