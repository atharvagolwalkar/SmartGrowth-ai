import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Configure page
st.set_page_config(
    page_title="SmartGrowth AI Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_BASE_URL = "http://localhost:8000"

# Custom CSS for better styling
st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
    border-bottom: 3px solid #1f77b4;
    padding-bottom: 1rem;
}
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
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
    background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);
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
""", unsafe_allow_html=True)

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_customer_data(customer_id):
    """Get customer data from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/customer/{customer_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def predict_churn(customer_id):
    """Get churn prediction from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/predict/churn/{customer_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def get_all_customers(limit=100):
    """Get all customers from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/customers/all", params={"limit": limit})
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def get_model_info():
    """Get model information from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/model/info")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def get_high_risk_customers():
    """Get high risk customers from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/customers/high-risk")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def format_risk_level(risk_level, probability):
    """Format risk level with color coding"""
    if risk_level == "High Risk":
        return f'<div class="risk-high">🔴 {risk_level} ({probability:.1%})</div>'
    elif risk_level == "Medium Risk":
        return f'<div class="risk-medium">🟡 {risk_level} ({probability:.1%})</div>'
    else:
        return f'<div class="risk-low">🟢 {risk_level} ({probability:.1%})</div>'

# Main app
def main():
    st.markdown('<h1 class="main-header">🚀 SmartGrowth AI Dashboard</h1>', unsafe_allow_html=True)
    
    # Check API status
    if not check_api_health():
        st.error("🔴 **API Connection Failed**")
        st.info("Please ensure the FastAPI backend is running:")
        st.code("cd app && python main.py")
        st.stop()
    
    st.success("🟢 **Connected to SmartGrowth AI API**")
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.selectbox("Choose a page:", [
        "🏠 Dashboard Overview",
        "🔍 Customer Risk Analysis", 
        "📊 Model Performance",
        "⚠️  High-Risk Customers",
        "🔄 Batch Prediction"
    ])
    
    if page == "🏠 Dashboard Overview":
        dashboard_overview()
    elif page == "🔍 Customer Risk Analysis":
        customer_risk_analysis()
    elif page == "📊 Model Performance":
        model_performance()
    elif page == "⚠️  High-Risk Customers":
        high_risk_customers()
    elif page == "🔄 Batch Prediction":
        batch_prediction()

def dashboard_overview():
    """Dashboard overview page"""
    st.header("📈 Business Intelligence Dashboard")
    
    # Get model info
    model_info = get_model_info()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🤖 Model Status", "Active" if model_info and model_info['model_loaded'] else "Inactive")
    
    with col2:
        if model_info and 'performance_metrics' in model_info:
            auc_score = model_info['performance_metrics'].get('auc', 'N/A')
            st.metric("🎯 Model AUC", f"{auc_score:.3f}" if isinstance(auc_score, float) else str(auc_score))
        else:
            st.metric("🎯 Model AUC", "N/A")
    
    with col3:
        if model_info:
            st.metric("🔧 Features", model_info.get('feature_count', 'N/A'))
        else:
            st.metric("🔧 Features", "N/A")
    
    with col4:
        if model_info:
            threshold = model_info.get('optimal_threshold', 0.5)
            st.metric("⚖️ Threshold", f"{threshold:.3f}")
        else:
            st.metric("⚖️ Threshold", "N/A")
    
    st.markdown("---")
    
    # Quick customer lookup
    st.subheader("🔍 Quick Customer Lookup")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        customer_id = st.text_input("Enter Customer ID:", placeholder="e.g., 7590-VHVEG")
    
    with col2:
        st.write("")  # Spacing
        analyze_button = st.button("🔍 Analyze Customer", type="primary")
    
    if analyze_button and customer_id:
        with st.spinner("Analyzing customer..."):
            customer_data = get_customer_data(customer_id)
            prediction_data = predict_churn(customer_id)
            
            if customer_data and prediction_data:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("👤 Customer Profile")
                    st.write(f"**Gender:** {customer_data.get('gender', 'N/A')}")
                    st.write(f"**Tenure:** {customer_data.get('tenure_months', 'N/A')} months")
                    st.write(f"**Monthly Charges:** ${customer_data.get('monthly_charges', 'N/A'):.2f}")
                    st.write(f"**Total Charges:** ${customer_data.get('total_charges', 'N/A'):.2f}")
                
                with col2:
                    st.subheader("⚠️  Churn Risk Analysis")
                    risk_html = format_risk_level(
                        prediction_data['risk_level'],
                        prediction_data['churn_probability']
                    )
                    st.markdown(risk_html, unsafe_allow_html=True)
                    
                    # Progress bar for risk
                    st.progress(prediction_data['churn_probability'], text="Churn Probability")
                    
                    # Recommendations
                    st.subheader("💡 Recommendations")
                    for rec in prediction_data['recommendations'][:3]:
                        st.write(f"• {rec}")
                        
            else:
                st.error("Customer not found or prediction failed")

def customer_risk_analysis():
    """Customer risk analysis page"""
    st.header("🔍 Customer Risk Analysis")
    
    customer_id = st.text_input("Enter Customer ID for detailed analysis:", placeholder="e.g., 7590-VHVEG")
    
    if customer_id:
        if st.button("📊 Generate Full Analysis", type="primary"):
            with st.spinner("Generating comprehensive analysis..."):
                customer_data = get_customer_data(customer_id)
                prediction_data = predict_churn(customer_id)
                
                if customer_data and prediction_data:
                    # Customer Overview
                    st.subheader("👤 Customer Overview")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Customer ID", customer_id)
                        st.metric("Gender", customer_data.get('gender', 'N/A'))
                        st.metric("Senior Citizen", "Yes" if customer_data.get('senior_citizen') else "No")
                    
                    with col2:
                        st.metric("Partner", "Yes" if customer_data.get('partner') else "No")
                        st.metric("Dependents", "Yes" if customer_data.get('dependents') else "No")
                        st.metric("Tenure (months)", customer_data.get('tenure_months', 'N/A'))
                    
                    with col3:
                        st.metric("Subscription Type", customer_data.get('subscription_type', 'N/A'))
                        st.metric("Payment Method", customer_data.get('payment_method', 'N/A'))
                        st.metric("Monthly Charges", f"${customer_data.get('monthly_charges', 0):.2f}")
                    
                    st.markdown("---")
                    
                    # Risk Analysis
                    st.subheader("⚠️  Risk Assessment")
                    
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        # Risk gauge chart
                        fig_gauge = go.Figure(go.Indicator(
                            mode = "gauge+number+delta",
                            value = prediction_data['churn_probability'] * 100,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': "Churn Risk Score"},
                            gauge = {
                                'axis': {'range': [None, 100]},
                                'bar': {'color': "darkblue"},
                                'steps': [
                                    {'range': [0, 40], 'color': "lightgreen"},
                                    {'range': [40, 70], 'color': "yellow"},
                                    {'range': [70, 100], 'color': "lightcoral"}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': 80
                                }
                            }
                        ))
                        fig_gauge.update_layout(height=400)
                        st.plotly_chart(fig_gauge, use_container_width=True)
                    
                    with col2:
                        st.markdown("### 📊 Risk Details")
                        risk_html = format_risk_level(
                            prediction_data['risk_level'],
                            prediction_data['churn_probability']
                        )
                        st.markdown(risk_html, unsafe_allow_html=True)
                        
                        st.write(f"**Probability:** {prediction_data['churn_probability']:.1%}")
                        st.write(f"**Threshold:** {prediction_data['optimal_threshold']:.3f}")
                        st.write(f"**Prediction:** {'Will Churn' if prediction_data['churn_prediction'] else 'Will Stay'}")
                        
                        # Model info
                        model_info = prediction_data.get('model_info', {})
                        st.write(f"**Model:** {model_info.get('model_name', 'N/A')}")
                        if 'auc_score' in model_info:
                            st.write(f"**Model AUC:** {model_info['auc_score']:.3f}")
                    
                    st.markdown("---")
                    
                    # Recommendations
                    st.subheader("💡 Strategic Recommendations")
                    for i, rec in enumerate(prediction_data['recommendations'], 1):
                        st.write(f"**{i}.** {rec}")
                        
                else:
                    st.error("❌ Customer not found or analysis failed")

def model_performance():
    """Model performance page"""
    st.header("📊 Model Performance Dashboard")
    
    model_info = get_model_info()
    
    if model_info:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🤖 Model Information")
            st.write(f"**Model Type:** {model_info.get('model_type', 'N/A')}")
            st.write(f"**Status:** {'✅ Loaded' if model_info.get('model_loaded') else '❌ Not Loaded'}")
            st.write(f"**Feature Count:** {model_info.get('feature_count', 'N/A')}")
            st.write(f"**Optimal Threshold:** {model_info.get('optimal_threshold', 'N/A')}")
            
            # Performance metrics
            if 'performance_metrics' in model_info:
                st.subheader("📈 Performance Metrics")
                metrics = model_info['performance_metrics']
                for metric, value in metrics.items():
                    if isinstance(value, float):
                        st.metric(metric.upper(), f"{value:.4f}")
                    else:
                        st.metric(metric.upper(), str(value))
        
        with col2:
            st.subheader("🔧 Feature Information")
            features = model_info.get('features', [])
            if features:
                st.write(f"**Total Features:** {len(features)}")
                
                # Create feature importance visualization (mock data for demo)
                feature_data = pd.DataFrame({
                    'Feature': features[:10],  # Show top 10 features
                    'Importance': [0.15, 0.12, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03]
                })
                
                fig = px.bar(
                    feature_data, 
                    x='Importance', 
                    y='Feature',
                    orientation='h',
                    title="Top Feature Importance (Demo)",
                    color='Importance',
                    color_continuous_scale='viridis'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Features list
                with st.expander("📋 All Features"):
                    for i, feature in enumerate(features, 1):
                        st.write(f"{i}. {feature}")
    else:
        st.error("❌ Unable to retrieve model information")

def high_risk_customers():
    """High-risk customers page"""
    st.header("⚠️  High-Risk Customer Monitoring")
    
    if st.button("🔍 Refresh High-Risk Analysis", type="primary"):
        with st.spinner("Analyzing customer base for high-risk customers..."):
            high_risk_data = get_high_risk_customers()
            
            if high_risk_data and 'high_risk_customers' in high_risk_data:
                customers = high_risk_data['high_risk_customers']
                
                st.subheader(f"🔴 Found {len(customers)} High-Risk Customers")
                
                if customers:
                    # Convert to DataFrame for better display
                    df = pd.DataFrame(customers)
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("High-Risk Count", len(customers))
                    with col2:
                        avg_risk = df['churn_probability'].mean()
                        st.metric("Avg Risk Score", f"{avg_risk:.1%}")
                    with col3:
                        high_value = df[df['monthly_charges'] > 70]
                        st.metric("High-Value at Risk", len(high_value))
                    with col4:
                        short_tenure = df[df['tenure_months'] < 12]
                        st.metric("New Customers at Risk", len(short_tenure))
                    
                    # Risk distribution chart
                    fig_hist = px.histogram(
                        df, 
                        x='churn_probability', 
                        nbins=20,
                        title="Risk Score Distribution",
                        labels={'churn_probability': 'Churn Probability', 'count': 'Number of Customers'}
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                    
                    # Customer table
                    st.subheader("📋 High-Risk Customer Details")
                    
                    # Format the dataframe for display
                    display_df = df.copy()
                    display_df['churn_probability'] = display_df['churn_probability'].apply(lambda x: f"{x:.1%}")
                    display_df['monthly_charges'] = display_df['monthly_charges'].apply(lambda x: f"${x:.2f}")
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        column_config={
                            "customer_id": "Customer ID",
                            "churn_probability": "Risk Score",
                            "risk_level": "Risk Level",
                            "monthly_charges": "Monthly Revenue",
                            "tenure_months": "Tenure (months)"
                        }
                    )
                    
                    # Download option
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download High-Risk Report",
                        data=csv,
                        file_name=f"high_risk_customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                else:
                    st.success("🎉 No high-risk customers found!")
                    
            else:
                st.error("❌ Unable to retrieve high-risk customer data")

def batch_prediction():
    """Batch prediction page"""
    st.header("🔄 Batch Churn Prediction")
    
    st.write("Analyze multiple customers at once by entering their Customer IDs.")
    
    # Text area for multiple customer IDs
    customer_ids_text = st.text_area(
        "Enter Customer IDs (one per line):",
        placeholder="7590-VHVEG\n5575-GNVDE\n3668-QPYBK\n...",
        height=150
    )
    
    if st.button("📊 Run Batch Analysis", type="primary"):
        if customer_ids_text:
            # Parse customer IDs
            customer_ids = [id.strip() for id in customer_ids_text.split('\n') if id.strip()]
            
            if customer_ids:
                st.write(f"Processing {len(customer_ids)} customers...")
                
                with st.spinner("Running batch predictions..."):
                    # Make batch prediction request
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/predict/churn/batch",
                            json={"customer_ids": customer_ids}
                        )
                        
                        if response.status_code == 200:
                            batch_results = response.json()
                            
                            # Display summary
                            summary = batch_results['summary']
                            st.subheader("📊 Batch Analysis Summary")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Total Processed", summary['total_requested'])
                            with col2:
                                st.metric("Successful", summary['successful_predictions'])
                            with col3:
                                st.metric("Failed", summary['failed_predictions'])
                            with col4:
                                st.metric("Success Rate", f"{summary['success_rate']:.1f}%")
                            
                            # Process results
                            results = batch_results['batch_results']
                            successful_results = [r for r in results if 'error' not in r]
                            failed_results = [r for r in results if 'error' in r]
                            
                            if successful_results:
                                # Convert to DataFrame
                                df = pd.DataFrame(successful_results)
                                
                                # Risk distribution
                                fig_pie = px.pie(
                                    df, 
                                    names='risk_level', 
                                    title="Risk Level Distribution"
                                )
                                st.plotly_chart(fig_pie, use_container_width=True)
                                
                                # Results table
                                st.subheader("📋 Detailed Results")
                                display_df = df[['customer_id', 'churn_probability', 'risk_level']].copy()
                                display_df['churn_probability'] = display_df['churn_probability'].apply(lambda x: f"{x:.1%}")
                                
                                st.dataframe(display_df, use_container_width=True)
                                
                                # Download option
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    label="📥 Download Batch Results",
                                    data=csv,
                                    file_name=f"batch_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                            
                            if failed_results:
                                st.subheader("❌ Failed Predictions")
                                for failed in failed_results:
                                    st.error(f"Customer {failed['customer_id']}: {failed['error']}")
                                    
                        else:
                            st.error("❌ Batch prediction failed")
                            
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                        
            else:
                st.warning("⚠️  Please enter at least one Customer ID")
        else:
            st.warning("⚠️  Please enter Customer IDs to analyze")

if __name__ == "__main__":
    main()