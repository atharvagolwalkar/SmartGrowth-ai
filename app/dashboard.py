import os
import sys

import pandas as pd
import requests
import streamlit as st
from requests import RequestException

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config


settings = get_config()
API_BASE_URL = settings.dashboard.api_base_url

st.set_page_config(page_title="SmartGrowth AI", layout="wide")

st.title("SmartGrowth AI: Customer Intelligence")

st.sidebar.header("Customer Lookup")
cust_id = st.sidebar.text_input("Enter Customer ID", "7590-VHVEG")

if st.sidebar.button("Analyze Risk"):
    try:
        prediction_response = requests.get(
            f"{API_BASE_URL}/predict/churn/{cust_id}", timeout=10
        )
        customer_response = requests.get(f"{API_BASE_URL}/customer/{cust_id}", timeout=10)
        prediction_response.raise_for_status()
        customer_response.raise_for_status()

        prediction = prediction_response.json()
        customer = customer_response.json()

        col1, col2 = st.columns(2)
        col1.metric("Churn Probability", f"{prediction['churn_probability']:.1%}")
        col2.metric("Risk Level", prediction["risk_level"])

        st.write("### Customer Snapshot")
        st.write(f"Subscription type: {customer['subscription_type']}")
        st.write(f"Monthly charges: ${customer['monthly_charges']:.2f}")
        st.write(f"Tenure: {customer['tenure_months']} months")

        st.write("### Risk Trend")
        chart_data = pd.DataFrame(
            [0.1, 0.2, 0.5, 0.3, prediction["churn_probability"]],
            columns=["Churn Probability"],
        )
        st.line_chart(chart_data)

        st.write("### Recommendations")
        for recommendation in prediction["recommendations"][:3]:
            st.write(f"- {recommendation}")
    except RequestException as exc:
        st.error(f"API request failed: {exc}")
