from datetime import datetime
import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from requests import RequestException

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config


settings = get_config()
API_BASE_URL = settings.dashboard.api_base_url

st.set_page_config(
    page_title=settings.dashboard.page_title,
    page_icon="SG",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.main-header {
    font-size: 3rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
    border-bottom: 3px solid #1f77b4;
    padding-bottom: 1rem;
}
.risk-high {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
    color: white;
    padding: 0.5rem;
    border-radius: 5px;
    text-align: center;
    font-weight: bold;
}
.risk-medium {
    background: linear-gradient(135deg, #feca57 0%, #ff9f43 100%);
    color: white;
    padding: 0.5rem;
    border-radius: 5px;
    text-align: center;
    font-weight: bold;
}
.risk-low {
    background: linear-gradient(135deg, #48dbfb 0%, #0abde3 100%);
    color: white;
    padding: 0.5rem;
    border-radius: 5px;
    text-align: center;
    font-weight: bold;
}
</style>
""",
    unsafe_allow_html=True,
)


def check_api_health():
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except RequestException:
        return False


def fetch_json(path, timeout=10, params=None, method="get", json=None):
    try:
        response = requests.request(
            method,
            f"{API_BASE_URL}{path}",
            params=params,
            json=json,
            timeout=timeout,
        )
        if response.status_code == 200:
            return response.json()
        return None
    except RequestException:
        return None


def get_customer_data(customer_id):
    return fetch_json(f"/customer/{customer_id}")


def predict_churn(customer_id):
    return fetch_json(f"/predict/churn/{customer_id}")


def get_model_info():
    return fetch_json("/model/info")


def get_high_risk_customers():
    return fetch_json("/customers/high-risk", timeout=20)


def format_risk_level(risk_level, probability):
    if risk_level == "High Risk":
        return f'<div class="risk-high">{risk_level} ({probability:.1%})</div>'
    if risk_level == "Medium Risk":
        return f'<div class="risk-medium">{risk_level} ({probability:.1%})</div>'
    return f'<div class="risk-low">{risk_level} ({probability:.1%})</div>'


def main():
    st.markdown('<h1 class="main-header">SmartGrowth AI Dashboard</h1>', unsafe_allow_html=True)

    if not check_api_health():
        st.error("API connection failed.")
        st.info("Start the backend with `python app/main.py` from the project root.")
        st.stop()

    st.success("Connected to SmartGrowth AI API")

    page = st.sidebar.selectbox(
        "Choose a page:",
        [
            "Dashboard Overview",
            "Customer Risk Analysis",
            "Model Performance",
            "High-Risk Customers",
            "Batch Prediction",
        ],
    )

    if page == "Dashboard Overview":
        dashboard_overview()
    elif page == "Customer Risk Analysis":
        customer_risk_analysis()
    elif page == "Model Performance":
        model_performance()
    elif page == "High-Risk Customers":
        high_risk_customers()
    else:
        batch_prediction()


def dashboard_overview():
    st.header("Business Intelligence Dashboard")
    model_info = get_model_info() or {}

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Model Status", "Active" if model_info.get("model_loaded") else "Inactive")
    col2.metric("Model AUC", f"{model_info.get('performance_metrics', {}).get('auc', 'N/A')}")
    col3.metric("Features", model_info.get("feature_count", "N/A"))
    col4.metric("Threshold", f"{model_info.get('optimal_threshold', 0.5):.3f}")

    st.markdown("---")
    st.subheader("Quick Customer Lookup")

    customer_id = st.text_input("Enter Customer ID:", placeholder="e.g., 7590-VHVEG")
    if st.button("Analyze Customer", type="primary") and customer_id:
        with st.spinner("Analyzing customer..."):
            customer_data = get_customer_data(customer_id)
            prediction_data = predict_churn(customer_id)

        if not customer_data or not prediction_data:
            st.error("Customer not found or prediction failed.")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Customer Profile")
            st.write(f"Gender: {customer_data.get('gender', 'N/A')}")
            st.write(f"Tenure: {customer_data.get('tenure_months', 'N/A')} months")
            st.write(f"Monthly Charges: ${customer_data.get('monthly_charges', 0):.2f}")
            st.write(f"Total Charges: ${customer_data.get('total_charges', 0):.2f}")

        with col2:
            st.subheader("Churn Risk Analysis")
            st.markdown(
                format_risk_level(
                    prediction_data["risk_level"],
                    prediction_data["churn_probability"],
                ),
                unsafe_allow_html=True,
            )
            st.progress(prediction_data["churn_probability"], text="Churn Probability")
            st.subheader("Recommendations")
            for recommendation in prediction_data["recommendations"][:3]:
                st.write(f"- {recommendation}")


def customer_risk_analysis():
    st.header("Customer Risk Analysis")
    customer_id = st.text_input(
        "Enter Customer ID for detailed analysis:",
        placeholder="e.g., 7590-VHVEG",
    )

    if st.button("Generate Full Analysis", type="primary") and customer_id:
        with st.spinner("Generating analysis..."):
            customer_data = get_customer_data(customer_id)
            prediction_data = predict_churn(customer_id)

        if not customer_data or not prediction_data:
            st.error("Customer not found or analysis failed.")
            return

        col1, col2, col3 = st.columns(3)
        col1.metric("Customer ID", customer_id)
        col1.metric("Gender", customer_data.get("gender", "N/A"))
        col1.metric("Senior Citizen", "Yes" if customer_data.get("senior_citizen") else "No")
        col2.metric("Partner", "Yes" if customer_data.get("partner") else "No")
        col2.metric("Dependents", "Yes" if customer_data.get("dependents") else "No")
        col2.metric("Tenure (months)", customer_data.get("tenure_months", "N/A"))
        col3.metric("Subscription Type", customer_data.get("subscription_type", "N/A"))
        col3.metric("Payment Method", customer_data.get("payment_method", "N/A"))
        col3.metric("Monthly Charges", f"${customer_data.get('monthly_charges', 0):.2f}")

        st.markdown("---")
        left, right = st.columns(2)

        with left:
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=prediction_data["churn_probability"] * 100,
                    title={"text": "Churn Risk Score"},
                    gauge={
                        "axis": {"range": [None, 100]},
                        "bar": {"color": "darkblue"},
                        "steps": [
                            {"range": [0, 40], "color": "lightgreen"},
                            {"range": [40, 70], "color": "khaki"},
                            {"range": [70, 100], "color": "lightcoral"},
                        ],
                    },
                )
            )
            fig_gauge.update_layout(height=380)
            st.plotly_chart(fig_gauge, use_container_width=True)

        with right:
            st.markdown(
                format_risk_level(
                    prediction_data["risk_level"],
                    prediction_data["churn_probability"],
                ),
                unsafe_allow_html=True,
            )
            st.write(f"Probability: {prediction_data['churn_probability']:.1%}")
            st.write(f"Threshold: {prediction_data['optimal_threshold']:.3f}")
            st.write(
                f"Prediction: {'Will Churn' if prediction_data['churn_prediction'] else 'Will Stay'}"
            )
            model_info = prediction_data.get("model_info", {})
            st.write(f"Model: {model_info.get('model_name', 'N/A')}")
            auc_score = model_info.get("auc_score")
            if isinstance(auc_score, (float, int)):
                st.write(f"Model AUC: {auc_score:.3f}")

        st.subheader("Strategic Recommendations")
        for index, recommendation in enumerate(prediction_data["recommendations"], start=1):
            st.write(f"{index}. {recommendation}")


def model_performance():
    st.header("Model Performance Dashboard")
    model_info = get_model_info()

    if not model_info:
        st.error("Unable to retrieve model information.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Model Information")
        st.write(f"Model Type: {model_info.get('model_type', 'N/A')}")
        st.write(f"Status: {'Loaded' if model_info.get('model_loaded') else 'Not Loaded'}")
        st.write(f"Feature Count: {model_info.get('feature_count', 'N/A')}")
        st.write(f"Optimal Threshold: {model_info.get('optimal_threshold', 'N/A')}")

        if "performance_metrics" in model_info:
            st.subheader("Performance Metrics")
            for metric, value in model_info["performance_metrics"].items():
                st.metric(metric.upper(), f"{value:.4f}" if isinstance(value, float) else str(value))

    with col2:
        st.subheader("Feature Information")
        features = model_info.get("features", [])
        st.write(f"Total Features: {len(features)}")
        if features:
            feature_df = pd.DataFrame({"Feature": features})
            feature_df.index = feature_df.index + 1
            st.dataframe(feature_df, use_container_width=True)


def high_risk_customers():
    st.header("High-Risk Customer Monitoring")

    if not st.button("Refresh High-Risk Analysis", type="primary"):
        return

    with st.spinner("Analyzing customer base..."):
        high_risk_data = get_high_risk_customers()

    if not high_risk_data or "high_risk_customers" not in high_risk_data:
        st.error("Unable to retrieve high-risk customer data.")
        return

    customers = high_risk_data["high_risk_customers"]
    st.subheader(f"Found {len(customers)} High-Risk Customers")

    if not customers:
        st.success("No high-risk customers found.")
        return

    df = pd.DataFrame(customers)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("High-Risk Count", len(customers))
    col2.metric("Avg Risk Score", f"{df['churn_probability'].mean():.1%}")
    col3.metric("High-Value at Risk", len(df[df["monthly_charges"] > 70]))
    col4.metric("New Customers at Risk", len(df[df["tenure_months"] < 12]))

    fig_hist = px.histogram(
        df,
        x="churn_probability",
        nbins=20,
        title="Risk Score Distribution",
        labels={"churn_probability": "Churn Probability", "count": "Number of Customers"},
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    display_df = df.copy()
    display_df["churn_probability"] = display_df["churn_probability"].map(lambda value: f"{value:.1%}")
    display_df["monthly_charges"] = display_df["monthly_charges"].map(lambda value: f"${value:.2f}")
    st.dataframe(display_df, use_container_width=True)

    st.download_button(
        label="Download High-Risk Report",
        data=df.to_csv(index=False),
        file_name=f"high_risk_customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )


def batch_prediction():
    st.header("Batch Churn Prediction")
    customer_ids_text = st.text_area(
        "Enter Customer IDs (one per line):",
        placeholder="7590-VHVEG\n5575-GNVDE\n3668-QPYBK",
        height=150,
    )

    if not st.button("Run Batch Analysis", type="primary"):
        return

    customer_ids = [value.strip() for value in customer_ids_text.splitlines() if value.strip()]
    if not customer_ids:
        st.warning("Please enter at least one Customer ID.")
        return

    with st.spinner("Running batch predictions..."):
        batch_results = fetch_json(
            "/predict/churn/batch",
            timeout=30,
            method="post",
            json={"customer_ids": customer_ids},
        )

    if not batch_results:
        st.error("Batch prediction failed.")
        return

    summary = batch_results["summary"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Processed", summary["total_requested"])
    col2.metric("Successful", summary["successful_predictions"])
    col3.metric("Failed", summary["failed_predictions"])
    col4.metric("Success Rate", f"{summary['success_rate']:.1f}%")

    results = batch_results["batch_results"]
    successful_results = [result for result in results if "error" not in result]
    failed_results = [result for result in results if "error" in result]

    if successful_results:
        df = pd.DataFrame(successful_results)
        fig_pie = px.pie(df, names="risk_level", title="Risk Level Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)

        display_df = df[["customer_id", "churn_probability", "risk_level"]].copy()
        display_df["churn_probability"] = display_df["churn_probability"].map(lambda value: f"{value:.1%}")
        st.dataframe(display_df, use_container_width=True)

        st.download_button(
            label="Download Batch Results",
            data=df.to_csv(index=False),
            file_name=f"batch_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    if failed_results:
        st.subheader("Failed Predictions")
        for failed in failed_results:
            st.error(f"Customer {failed['customer_id']}: {failed['error']}")


if __name__ == "__main__":
    main()
