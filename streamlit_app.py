"""
Entry point for Streamlit Community Cloud.
Cloud runs this file by convention — it just imports the real dashboard.

Deploy steps:
  1. Push repo to GitHub
  2. Go to share.streamlit.io → New app
  3. Set main file path: streamlit_app.py
  4. Add secrets in Streamlit Cloud dashboard (copy from .env.example)
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

# On Streamlit Cloud the FastAPI runs separately (Railway/Render).
# Set API_BASE_URL in Streamlit Cloud Secrets to point at it.
if "API_BASE" not in os.environ:
    os.environ["API_BASE"] = os.environ.get("API_BASE_URL", "http://localhost:8000")

from app.dashboard_v2 import main
main()