import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SmartGrowth AI", layout="wide")

st.title("🚀 SmartGrowth AI: Customer Intelligence")

# Sidebar for inputs
st.sidebar.header("Customer Lookup")
cust_id = st.sidebar.text_input("Enter Customer ID", "CUST-1001")

if st.sidebar.button("Analyze Risk"):
    # Call our FastAPI backend
    response = requests.get(f"http://127.0.0.1:8000/predict/churn/{cust_id}")
    data = response.json()
    
    # Display results in cards
    col1, col2 = st.columns(2)
    col1.metric("Churn Probability", f"{data['churn_risk']*100}%")
    col2.info(f"System Status: {data['status']}")
    
    # Placeholder for a graph
    st.write("### Historical Usage Trend")
    chart_data = pd.DataFrame([0.1, 0.2, 0.5, 0.3, data['churn_risk']], columns=['Usage'])
    st.line_chart(chart_data)