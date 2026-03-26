"""
SmartGrowth AI — Production Dashboard v2
=========================================
A sharp, professional multi-page Streamlit dashboard.
Replaces dashboard.py and dashboard_enhanced.py entirely.

Run:
    streamlit run app/dashboard_v2.py
"""

import time
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="SmartGrowth AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = "http://localhost:8000"

# ── Design system ─────────────────────────────────────────────────────────────
COLORS = {
    "bg":        "#0A0E1A",
    "surface":   "#111827",
    "surface2":  "#1C2333",
    "border":    "#2D3748",
    "accent":    "#6366F1",       # indigo
    "accent2":   "#10B981",       # emerald
    "accent3":   "#F59E0B",       # amber
    "danger":    "#EF4444",
    "text":      "#F1F5F9",
    "muted":     "#94A3B8",
    "chart_grid":"#1E293B",
}

PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'DM Sans', sans-serif", color=COLORS["text"], size=13),
        xaxis=dict(gridcolor=COLORS["chart_grid"], linecolor=COLORS["border"],
                   tickfont=dict(color=COLORS["muted"])),
        yaxis=dict(gridcolor=COLORS["chart_grid"], linecolor=COLORS["border"],
                   tickfont=dict(color=COLORS["muted"])),
        hoverlabel=dict(bgcolor=COLORS["surface2"], font_color=COLORS["text"],
                        bordercolor=COLORS["border"]),
    )
)

# ── Global CSS ────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

    /* ── Root reset ── */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {COLORS["bg"]} !important;
        font-family: 'DM Sans', sans-serif;
        color: {COLORS["text"]};
    }}
    [data-testid="stHeader"] {{ background: {COLORS["bg"]}; border-bottom: 1px solid {COLORS["border"]}; }}
    [data-testid="stSidebar"] {{
        background-color: {COLORS["surface"]} !important;
        border-right: 1px solid {COLORS["border"]};
    }}
    [data-testid="stSidebar"] * {{ color: {COLORS["text"]} !important; }}

    /* ── Hide default decoration ── */
    #MainMenu, footer {{ display: none !important; }}
    .stDeployButton {{ display: none; }}

    /* ── Metric cards ── */
    [data-testid="metric-container"] {{
        background: {COLORS["surface"]} !important;
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        padding: 1rem 1.2rem !important;
        transition: border-color 0.2s;
    }}
    [data-testid="metric-container"]:hover {{ border-color: {COLORS["accent"]}; }}
    [data-testid="stMetricLabel"] {{ color: {COLORS["muted"]} !important; font-size: 0.78rem !important; letter-spacing: 0.06em; text-transform: uppercase; }}
    [data-testid="stMetricValue"] {{ color: {COLORS["text"]} !important; font-size: 1.7rem !important; font-weight: 600 !important; }}
    [data-testid="stMetricDelta"] {{ font-size: 0.8rem !important; }}

    /* ── Inputs ── */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stSelectbox"] select,
    .stSelectbox > div > div {{
        background: {COLORS["surface2"]} !important;
        border: 1px solid {COLORS["border"]} !important;
        border-radius: 8px !important;
        color: {COLORS["text"]} !important;
    }}
    [data-testid="stSlider"] {{ accent-color: {COLORS["accent"]}; }}

    /* ── Buttons ── */
    .stButton > button {{
        background: {COLORS["accent"]} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em;
        transition: opacity 0.15s;
    }}
    .stButton > button:hover {{ opacity: 0.85 !important; }}
    .stButton > button[kind="secondary"] {{
        background: {COLORS["surface2"]} !important;
        border: 1px solid {COLORS["border"]} !important;
        color: {COLORS["muted"]} !important;
    }}

    /* ── Tabs ── */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {{
        background: {COLORS["surface"]} !important;
        border-radius: 10px;
        padding: 4px;
        gap: 2px;
        border: 1px solid {COLORS["border"]};
    }}
    [data-testid="stTabs"] [data-baseweb="tab"] {{
        background: transparent !important;
        border-radius: 7px !important;
        color: {COLORS["muted"]} !important;
        font-weight: 500;
        padding: 6px 16px !important;
        border: none !important;
    }}
    [data-testid="stTabs"] [aria-selected="true"] {{
        background: {COLORS["accent"]} !important;
        color: white !important;
    }}

    /* ── Dataframes ── */
    [data-testid="stDataFrame"] {{
        border: 1px solid {COLORS["border"]};
        border-radius: 10px;
        overflow: hidden;
    }}

    /* ── Expander ── */
    [data-testid="stExpander"] {{
        background: {COLORS["surface"]} !important;
        border: 1px solid {COLORS["border"]} !important;
        border-radius: 10px !important;
    }}

    /* ── Alerts ── */
    [data-testid="stAlert"] {{
        border-radius: 10px !important;
        border-left-width: 3px !important;
    }}

    /* ── Custom components ── */
    .sg-card {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.75rem;
        transition: border-color 0.2s, transform 0.15s;
    }}
    .sg-card:hover {{ border-color: {COLORS["accent"]}; transform: translateY(-1px); }}

    .sg-badge {{
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }}
    .badge-high   {{ background: rgba(239,68,68,0.15);  color: #FCA5A5; border: 1px solid rgba(239,68,68,0.3); }}
    .badge-medium {{ background: rgba(245,158,11,0.15); color: #FCD34D; border: 1px solid rgba(245,158,11,0.3); }}
    .badge-low    {{ background: rgba(16,185,129,0.15); color: #6EE7B7; border: 1px solid rgba(16,185,129,0.3); }}

    .sg-section-header {{
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: {COLORS["muted"]};
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid {COLORS["border"]};
    }}

    .risk-bar-container {{
        background: {COLORS["surface2"]};
        border-radius: 100px;
        height: 6px;
        overflow: hidden;
        margin-top: 4px;
    }}
    .risk-bar-fill {{
        height: 100%;
        border-radius: 100px;
        transition: width 0.6s ease;
    }}

    .sg-logo {{
        font-size: 1.1rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: {COLORS["text"]};
    }}
    .sg-logo span {{ color: {COLORS["accent"]}; }}

    .stat-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.45rem 0;
        border-bottom: 1px solid {COLORS["border"]};
        font-size: 0.85rem;
    }}
    .stat-row:last-child {{ border-bottom: none; }}
    .stat-label {{ color: {COLORS["muted"]}; }}
    .stat-value {{ color: {COLORS["text"]}; font-weight: 500; font-family: 'DM Mono', monospace; }}

    div[data-testid="column"] > div {{ height: 100%; }}

    /* ── Toolbar styling ── */
    [data-testid="stToolbar"] {{
        background: {COLORS["bg"]} !important;
        border-bottom: 1px solid {COLORS["border"]};
    }}
    </style>
    """, unsafe_allow_html=True)


# ── API helpers ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def api_get(endpoint: str, params: dict = None):
    try:
        r = requests.get(f"{API_BASE}{endpoint}", params=params, timeout=8)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "API offline — start with: uvicorn app.main:app --reload"
    except Exception as e:
        return None, str(e)


def api_post(endpoint: str, payload: dict):
    try:
        r = requests.post(f"{API_BASE}{endpoint}", json=payload, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)


def check_api() -> bool:
    data, err = api_get("/health")
    return err is None


# ── Chart factories ───────────────────────────────────────────────────────────
def make_gauge(value: float, title: str, color: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100,
        number={"suffix": "%", "font": {"size": 28, "color": COLORS["text"]}},
        title={"text": title, "font": {"size": 12, "color": COLORS["muted"]}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": COLORS["muted"],
                     "tickfont": {"color": COLORS["muted"], "size": 10}},
            "bar":  {"color": color, "thickness": 0.25},
            "bgcolor": COLORS["surface2"],
            "bordercolor": COLORS["border"],
            "steps": [
                {"range": [0,  40], "color": "rgba(16,185,129,0.08)"},
                {"range": [40, 70], "color": "rgba(245,158,11,0.08)"},
                {"range": [70,100], "color": "rgba(239,68,68,0.08)"},
            ],
            "threshold": {"line": {"color": color, "width": 2},
                          "thickness": 0.75, "value": value * 100},
        },
    ))
    fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=200,
                  margin=dict(l=20, r=20, t=40, b=10),
                  legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["muted"])))
    return fig


def make_forecast_chart(forecast_data: list, title: str = "Demand Forecast") -> go.Figure:
    if not forecast_data:
        return go.Figure()

    df = pd.DataFrame(forecast_data)
    df["date"] = pd.to_datetime(df["date"])

    fig = go.Figure()

    # Confidence band
    fig.add_trace(go.Scatter(
        x=pd.concat([df["date"], df["date"][::-1]]),
        y=pd.concat([df["upper_bound"], df["lower_bound"][::-1]]),
        fill="toself",
        fillcolor="rgba(99,102,241,0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        name="90% CI",
        hoverinfo="skip",
    ))

    # Forecast line
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["forecast"],
        mode="lines+markers",
        name="Forecast",
        line=dict(color=COLORS["accent"], width=2.5),
        marker=dict(size=4, color=COLORS["accent"]),
        hovertemplate="<b>%{x|%b %d}</b><br>Demand: %{y:,.0f} units<extra></extra>",
    ))

    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title=dict(text=title, font=dict(size=14, color=COLORS["text"]), x=0),
        height=320,
        showlegend=True,
        hovermode="x unified",
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["muted"])),
    )
    return fig


def make_model_comparison_chart(all_forecasts: dict) -> go.Figure:
    colors = {
        "ARIMA":   COLORS["accent3"],
        "Prophet": COLORS["accent2"],
        "N-BEATS": COLORS["accent"],
    }
    fig = go.Figure()
    for model_name, points in all_forecasts.items():
        if not points:
            continue
        df = pd.DataFrame(points)
        df["date"] = pd.to_datetime(df["date"])
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["forecast"],
            mode="lines",
            name=model_name,
            line=dict(color=colors.get(model_name, "#888"), width=2),
            hovertemplate=f"<b>{model_name}</b><br>%{{x|%b %d}}: %{{y:,.0f}}<extra></extra>",
        ))

    fig.update_layout(
    **PLOTLY_TEMPLATE["layout"],
    title=dict(text="Model comparison — all 3 forecasts", font=dict(size=14), x=0),
    height=320,
    hovermode="x unified",
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h",
                yanchor="bottom", y=1.02, xanchor="right", x=1),
)
    return fig


def make_risk_distribution(customers: list) -> go.Figure:
    if not customers:
        return go.Figure()
    risks = [c.get("risk_level", "Unknown") for c in customers]
    counts = pd.Series(risks).value_counts()
    color_map = {"High": COLORS["danger"], "Medium": COLORS["accent3"],
                 "Low": COLORS["accent2"], "Unknown": COLORS["muted"]}

    fig = go.Figure(go.Bar(
        x=counts.index.tolist(),
        y=counts.values.tolist(),
        marker_color=[color_map.get(r, COLORS["muted"]) for r in counts.index],
        text=counts.values.tolist(),
        textposition="outside",
        textfont=dict(color=COLORS["text"], size=13),
        hovertemplate="<b>%{x}</b><br>%{y} customers<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title=dict(text="Churn risk distribution", font=dict(size=14), x=0),
        height=280,
        showlegend=False,
        xaxis_title=None,
        yaxis_title=None,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["muted"])),
    )
    return fig


def make_spend_vs_churn(customers: list) -> go.Figure:
    if not customers:
        return go.Figure()
    df = pd.DataFrame(customers)
    if "monthly_charges" not in df.columns or "churn_probability" not in df.columns:
        return go.Figure()

    color_map = {"High": COLORS["danger"], "Medium": COLORS["accent3"], "Low": COLORS["accent2"]}
    df["color"] = df["risk_level"].map(color_map).fillna(COLORS["muted"])

    fig = go.Figure(go.Scatter(
        x=df["monthly_charges"],
        y=(df["churn_probability"] * 100).round(1),
        mode="markers",
        marker=dict(
            color=df["color"],
            size=7,
            opacity=0.75,
            line=dict(width=0.5, color=COLORS["surface"]),
        ),
        text=df.get("customer_id", df.index),
        hovertemplate="<b>%{text}</b><br>Monthly: $%{x:.0f}<br>Churn: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title=dict(text="Monthly spend vs churn risk", font=dict(size=14), x=0),
        height=300,
        xaxis_title="Monthly charges ($)",
        yaxis_title="Churn probability (%)",
        showlegend=False,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["muted"])),
    )
    return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("""
        <div style="padding: 0.5rem 0 1.5rem 0;">
            <div class="sg-logo">Smart<span>Growth</span> AI</div>
            <div style="font-size:0.72rem; color:#64748B; margin-top:3px; letter-spacing:0.05em;">
                CUSTOMER INTELLIGENCE PLATFORM
            </div>
        </div>
        """, unsafe_allow_html=True)

        # API status
        is_online = check_api()
        status_color = "#10B981" if is_online else "#EF4444"
        status_text  = "API Online" if is_online else "API Offline"
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:1.5rem;
                    padding:8px 12px;background:{COLORS['surface2']};
                    border-radius:8px;border:1px solid {COLORS['border']};">
            <div style="width:7px;height:7px;border-radius:50%;background:{status_color};
                        box-shadow:0 0 6px {status_color};"></div>
            <span style="font-size:0.78rem;color:{COLORS['muted']}">{status_text}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sg-section-header">Navigation</div>', unsafe_allow_html=True)
        page = st.radio(
            label="nav",
            options=["Overview", "Customer Analysis", "Demand Forecast", "High Risk", "Batch", "NLP Insights"],
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown('<div class="sg-section-header">Quick lookup</div>', unsafe_allow_html=True)
        quick_id = st.text_input("Customer ID", placeholder="e.g. 7590-VHVEG",
                                  label_visibility="collapsed")
        if quick_id and st.button("Look up →", use_container_width=True):
            st.session_state["quick_lookup"] = quick_id

        st.markdown("---")
        st.markdown(f"""
        <div style="font-size:0.7rem;color:{COLORS['muted']};line-height:1.6;">
            SmartGrowth AI v2.0<br>
            Models: RF Churn · Prophet · N-BEATS<br>
            Data: Telco + Synthetic
        </div>
        """, unsafe_allow_html=True)

    return page


# ── Pages ─────────────────────────────────────────────────────────────────────

def page_overview():
    st.markdown("## Overview")
    st.markdown(f"<span style='color:{COLORS['muted']};font-size:0.85rem;'>"
                f"Last refreshed: {datetime.now().strftime('%H:%M:%S')}</span>",
                unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── KPI cards ──
    data, err = api_get("/customers/all")
    if err:
        st.error(f"Could not load customers: {err}")
        return

    customers = data if isinstance(data, list) else data.get("customers", [])
    df = pd.DataFrame(customers)

    if df.empty:
        st.warning("No customer data found. Make sure the database is seeded.")
        return

    total       = len(df)
    churned     = int(df["churn"].sum()) if "churn" in df.columns else 0
    churn_rate  = churned / total * 100 if total else 0
    avg_charges = df["monthly_charges"].mean() if "monthly_charges" in df.columns else 0
    avg_tenure  = df["tenure"].mean() if "tenure" in df.columns else 0
    revenue_risk = df[df["churn"] == 1]["monthly_charges"].sum() \
                   if "churn" in df.columns and "monthly_charges" in df.columns else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Customers", f"{total:,}")
    c2.metric("Churn Rate", f"{churn_rate:.1f}%",
              delta=f"{'▲' if churn_rate > 20 else '▼'} vs 20% baseline",
              delta_color="inverse")
    c3.metric("Avg Monthly Charges", f"${avg_charges:.0f}")
    c4.metric("Avg Tenure", f"{avg_tenure:.0f} mo")
    c5.metric("Revenue at Risk", f"${revenue_risk:,.0f}", delta="monthly",
              delta_color="off")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts row ──
    col_left, col_right = st.columns([3, 2])

    with col_left:
        # Churn by contract type
        if "contract" in df.columns:
            contract_churn = df.groupby("contract")["churn"].mean().reset_index()
            contract_churn.columns = ["Contract", "Churn Rate"]
            contract_churn["Churn Rate"] = (contract_churn["Churn Rate"] * 100).round(1)
            fig = go.Figure(go.Bar(
                x=contract_churn["Contract"],
                y=contract_churn["Churn Rate"],
                marker=dict(
                    color=contract_churn["Churn Rate"],
                    colorscale=[[0, COLORS["accent2"]], [0.5, COLORS["accent3"]], [1, COLORS["danger"]]],
                    showscale=False,
                ),
                text=[f"{v}%" for v in contract_churn["Churn Rate"]],
                textposition="outside",
                textfont=dict(color=COLORS["text"]),
                hovertemplate="<b>%{x}</b><br>Churn rate: %{y:.1f}%<extra></extra>",
            ))
            fig.update_layout(
                **PLOTLY_TEMPLATE["layout"],
                title=dict(text="Churn rate by contract type", font=dict(size=14), x=0),
                height=300, showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_right:
        # Segment distribution (internet service proxy)
        if "internet_service" in df.columns:
            seg = df["internet_service"].value_counts().reset_index()
            seg.columns = ["Service", "Count"]
            fig2 = go.Figure(go.Pie(
                labels=seg["Service"],
                values=seg["Count"],
                hole=0.55,
                marker=dict(colors=[COLORS["accent"], COLORS["accent2"], COLORS["accent3"]],
                            line=dict(color=COLORS["bg"], width=2)),
                textfont=dict(color=COLORS["text"]),
                hovertemplate="<b>%{label}</b><br>%{value:,} customers (%{percent})<extra></extra>",
            ))
            fig2.update_layout(
                **PLOTLY_TEMPLATE["layout"],
                title=dict(text="Customers by internet service", font=dict(size=14), x=0),
                height=300,
                legend=dict(orientation="v", x=0.75, y=0.5),
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # ── Tenure histogram ──
    if "tenure" in df.columns:
        st.markdown('<div class="sg-section-header">Tenure distribution</div>',
                    unsafe_allow_html=True)
        fig3 = go.Figure(go.Histogram(
            x=df["tenure"],
            nbinsx=24,
            marker=dict(
                color=COLORS["accent"],
                opacity=0.8,
                line=dict(color=COLORS["bg"], width=0.5),
            ),
            hovertemplate="Tenure %{x} mo: %{y} customers<extra></extra>",
        ))
        churn_tenure = df[df["churn"] == 1]["tenure"] if "churn" in df.columns else None
        if churn_tenure is not None:
            fig3.add_trace(go.Histogram(
                x=churn_tenure,
                nbinsx=24,
                marker=dict(color=COLORS["danger"], opacity=0.7,
                            line=dict(color=COLORS["bg"], width=0.5)),
                name="Churned",
            ))
        fig3.update_layout(
            **PLOTLY_TEMPLATE["layout"],
            height=240,
            barmode="overlay",
            showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=1.1, xanchor="right", x=1),
            xaxis_title="Tenure (months)",
            yaxis_title="Count",
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})


def page_customer_analysis():
    st.markdown("## Customer Analysis")

    # ── Input ──
    col_input, col_btn, _ = st.columns([3, 1, 3])
    with col_input:
        customer_id = st.text_input("Enter Customer ID", placeholder="e.g. 7590-VHVEG",
                                     label_visibility="visible")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        search = st.button("Analyse →", use_container_width=True)

    # Handle quick lookup from sidebar
    if "quick_lookup" in st.session_state:
        customer_id = st.session_state.pop("quick_lookup")
        search = True

    if not customer_id:
        st.markdown(f"""
        <div style="text-align:center;padding:3rem;color:{COLORS['muted']};">
            <div style="font-size:2.5rem;margin-bottom:0.5rem;">🔍</div>
            <div style="font-size:0.95rem;">Enter a customer ID above to see their full profile and churn risk.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    with st.spinner("Loading customer data..."):
        cust_data, err = api_get(f"/customer/{customer_id}")

    if err or cust_data is None:
        st.error(f"Customer not found: {customer_id}")
        return

    with st.spinner("Running churn model..."):
        pred_data, perr = api_get(f"/predict/churn/{customer_id}")

    if perr or pred_data is None:
        st.warning("Could not generate churn prediction. Customer data loaded.")
        pred_data = {}

    # ── Layout ──
    col_profile, col_risk = st.columns([2, 1])

    with col_profile:
        st.markdown('<div class="sg-section-header">Customer Profile</div>',
                    unsafe_allow_html=True)

        fields = [
            ("Customer ID",      cust_data.get("customer_id",     "—")),
            ("Gender",           cust_data.get("gender",          "—")),
            ("Senior Citizen",   "Yes" if cust_data.get("senior_citizen") else "No"),
            ("Partner",          "Yes" if cust_data.get("partner") else "No"),
            ("Dependents",       "Yes" if cust_data.get("dependents") else "No"),
            ("Tenure",           f"{cust_data.get('tenure', 0)} months"),
            ("Contract",         cust_data.get("contract",        "—")),
            ("Internet Service", cust_data.get("internet_service","—")),
            ("Monthly Charges",  f"${cust_data.get('monthly_charges', 0):.2f}"),
            ("Total Charges",    f"${float(cust_data.get('total_charges', 0) or 0):.2f}"),
            ("Payment Method",   cust_data.get("payment_method",  "—")),
        ]

        rows_html = "".join(
            f'<div class="stat-row"><span class="stat-label">{k}</span>'
            f'<span class="stat-value">{v}</span></div>'
            for k, v in fields
        )
        st.markdown(f'<div class="sg-card">{rows_html}</div>', unsafe_allow_html=True)

    with col_risk:
        if pred_data:
            prob    = pred_data.get("churn_probability", 0)
            risk    = pred_data.get("risk_level", "Unknown")
            badge_c = {"High": "badge-high", "Medium": "badge-medium",
                       "Low": "badge-low"}.get(risk, "badge-low")
            gauge_c = {"High": COLORS["danger"], "Medium": COLORS["accent3"],
                       "Low": COLORS["accent2"]}.get(risk, COLORS["accent"])

            st.markdown('<div class="sg-section-header">Churn Risk</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(make_gauge(prob, "Churn Probability", gauge_c),
                            use_container_width=True, config={"displayModeBar": False})

            st.markdown(f"""
            <div class="sg-card" style="text-align:center;">
                <div style="font-size:0.78rem;color:{COLORS['muted']};margin-bottom:6px;">RISK LEVEL</div>
                <span class="sg-badge {badge_c}">{risk}</span>
                <div style="margin-top:10px;font-size:0.85rem;color:{COLORS['muted']};">
                    Probability: <span style="color:{gauge_c};font-weight:600;">{prob*100:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Recommendations
            recs = pred_data.get("recommendations", [])
            if recs:
                st.markdown('<div class="sg-section-header" style="margin-top:1rem;">Recommendations</div>',
                            unsafe_allow_html=True)
                for rec in recs[:4]:
                    st.markdown(f"""
                    <div class="sg-card" style="padding:0.7rem 1rem;">
                        <span style="color:{COLORS['accent']};margin-right:8px;">→</span>
                        <span style="font-size:0.85rem;">{rec}</span>
                    </div>
                    """, unsafe_allow_html=True)


def page_forecast():
    st.markdown("## Demand Forecast")

    # ── Controls ──
    col1, col2, col3, _ = st.columns([1, 1, 1, 2])
    with col1:
        horizon = st.slider("Forecast horizon (days)", 7, 90, 30)
    with col2:
        model = st.selectbox("Model", ["best", "Prophet", "N-BEATS", "ARIMA"])
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        compare_all = st.checkbox("Compare all models", value=False)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.spinner("Generating forecast..."):
        if compare_all:
            data, err = api_get("/forecast/predict/all", {"horizon": horizon})
        else:
            data, err = api_get("/forecast/predict", {"horizon": horizon, "model": model})

    if err:
        st.error(f"Forecast API error: {err}")
        st.info("Make sure you've trained the models first:\n```\npython -m ml_models.forecasting.pipeline\n```")
        return

    if compare_all and data:
        forecasts = data.get("forecasts", {})
        best = data.get("best_model", "Prophet")

        st.markdown(f'<span class="sg-badge badge-low">Best model: {best}</span>',
                    unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        st.plotly_chart(make_model_comparison_chart(forecasts),
                        use_container_width=True, config={"displayModeBar": False})

        # Side-by-side summary stats
        cols = st.columns(len(forecasts))
        for i, (mname, points) in enumerate(forecasts.items()):
            if not points:
                continue
            vals = [p["forecast"] for p in points]
            with cols[i]:
                st.markdown(f'<div class="sg-section-header">{mname}</div>',
                            unsafe_allow_html=True)
                st.metric("Avg daily", f"{np.mean(vals):,.0f}")
                st.metric("Peak",      f"{max(vals):,.0f}")
                st.metric("Total",     f"{sum(vals):,.0f}")

    elif data:
        forecast_points = data.get("forecast", [])
        summary         = data.get("business_summary", {})
        model_used      = data.get("model_used", model)

        st.markdown(f'<span class="sg-badge badge-low">Model: {model_used}</span>',
                    unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Main chart
        st.plotly_chart(
            make_forecast_chart(forecast_points, f"{horizon}-day demand forecast"),
            use_container_width=True, config={"displayModeBar": False},
        )

        # Summary KPIs
        if summary:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total forecast units", f"{summary.get('total_forecast_units', 0):,.0f}")
            c2.metric("Avg daily demand",     f"{summary.get('avg_daily_demand', 0):,.1f}")
            c3.metric("Peak day",
                      summary.get("peak_day", "—"),
                      delta=f"{summary.get('peak_demand', 0):,.0f} units",
                      delta_color="off")
            c4.metric("Demand volatility", f"±{summary.get('demand_volatility', 0):,.0f}")

        # Forecast table (expandable)
        with st.expander("View full forecast table"):
            if forecast_points:
                df_table = pd.DataFrame(forecast_points)
                df_table.columns = ["Date", "Forecast", "Lower Bound", "Upper Bound", "Model"]
                df_table["Forecast"]    = df_table["Forecast"].apply(lambda x: f"{x:,.1f}")
                df_table["Lower Bound"] = df_table["Lower Bound"].apply(lambda x: f"{x:,.1f}")
                df_table["Upper Bound"] = df_table["Upper Bound"].apply(lambda x: f"{x:,.1f}")
                st.dataframe(df_table, use_container_width=True, hide_index=True)

    # ── Model metrics ──
    metrics_data, _ = api_get("/forecast/metrics")
    if metrics_data and "models" in metrics_data:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="sg-section-header">Model evaluation (30-day holdout)</div>',
                    unsafe_allow_html=True)

        models_info = metrics_data["models"]
        rows = []
        for mname, m in models_info.items():
            if "error" not in m:
                rows.append({
                    "Model":    mname,
                    "MAE":      f"{m.get('MAE', 0):.2f}",
                    "RMSE":     f"{m.get('RMSE', 0):.2f}",
                    "MAPE":     f"{m.get('MAPE', 0):.2f}%",
                    "Fit Time": f"{m.get('fit_time_s', 0):.1f}s",
                    "Status":   "✓ Best" if mname == metrics_data.get("best_model") else "—",
                })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def page_high_risk():
    st.markdown("## High Risk Customers")

    with st.spinner("Scanning for high-risk customers..."):
        data, err = api_get("/customers/high-risk")

    if err:
        st.error(f"Error: {err}")
        return

    customers = data if isinstance(data, list) else data.get("high_risk_customers", [])

    if not customers:
        st.success("No high-risk customers found.")
        return

    # Summary row
    total_hr = len(customers)
    avg_prob  = np.mean([c.get("churn_probability", 0) for c in customers]) * 100
    total_rev = sum(c.get("monthly_charges", 0) for c in customers)

    c1, c2, c3 = st.columns(3)
    c1.metric("High Risk Count",    f"{total_hr:,}")
    c2.metric("Avg Churn Prob",     f"{avg_prob:.1f}%")
    c3.metric("Monthly Rev at Risk",f"${total_rev:,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_risk_distribution(customers),
                        use_container_width=True, config={"displayModeBar": False})
    with col_r:
        st.plotly_chart(make_spend_vs_churn(customers),
                        use_container_width=True, config={"displayModeBar": False})

    # Customer cards
    st.markdown('<div class="sg-section-header">High-risk customers</div>',
                unsafe_allow_html=True)

    # Sort by probability descending
    customers_sorted = sorted(customers,
                               key=lambda x: x.get("churn_probability", 0), reverse=True)

    for c in customers_sorted[:20]:
        prob  = c.get("churn_probability", 0)
        risk  = c.get("risk_level", "Unknown")
        badge = {"High": "badge-high", "Medium": "badge-medium",
                 "Low": "badge-low"}.get(risk, "badge-low")
        bar_color = {"High": COLORS["danger"], "Medium": COLORS["accent3"],
                     "Low": COLORS["accent2"]}.get(risk, COLORS["accent"])

        st.markdown(f"""
        <div class="sg-card">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <span style="font-weight:600;font-family:'DM Mono',monospace;font-size:0.9rem;">
                        {c.get('customer_id','—')}
                    </span>
                    &nbsp;&nbsp;<span class="sg-badge {badge}">{risk}</span>
                </div>
                <div style="font-size:1.1rem;font-weight:600;color:{bar_color};">
                    {prob*100:.1f}%
                </div>
            </div>
            <div class="risk-bar-container" style="margin-top:8px;">
                <div class="risk-bar-fill"
                     style="width:{prob*100:.1f}%;background:{bar_color};"></div>
            </div>
            <div style="margin-top:8px;display:flex;gap:1.5rem;font-size:0.78rem;color:{COLORS['muted']};">
                <span>Tenure: {c.get('tenure_months', c.get('tenure','—'))} mo</span>
                <span>Monthly: ${c.get('monthly_charges',0):.0f}</span>
                <span>Contract: {c.get('contract','—')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if len(customers_sorted) > 20:
        st.markdown(f"<div style='color:{COLORS['muted']};font-size:0.82rem;text-align:center;'>"
                    f"Showing top 20 of {len(customers_sorted)} high-risk customers</div>",
                    unsafe_allow_html=True)


def page_batch():
    st.markdown("## Batch Prediction")

    st.markdown(f"""
    <div class="sg-card" style="margin-bottom:1.5rem;">
        <div style="font-size:0.85rem;color:{COLORS['muted']};line-height:1.7;">
            Upload a CSV file or enter customer IDs manually to run churn
            predictions at scale. Results are downloadable as CSV.
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_manual, tab_upload = st.tabs(["Manual IDs", "Upload CSV"])

    with tab_manual:
        ids_input = st.text_area(
            "Customer IDs (one per line or comma-separated)",
            height=120,
            placeholder="7590-VHVEG\n5575-GNVDE\n3668-QPYBK",
        )
        if st.button("Run Batch Prediction", use_container_width=False):
            raw = ids_input.replace(",", "\n").strip()
            ids = [x.strip() for x in raw.splitlines() if x.strip()]

            if not ids:
                st.warning("Please enter at least one customer ID.")
            else:
                with st.spinner(f"Running predictions for {len(ids)} customers..."):
                    result, err = api_post("/predict/churn/batch", {"customer_ids": ids})

                if err:
                    st.error(f"Batch prediction failed: {err}")
                elif result:
                    _render_batch_results(result)

    with tab_upload:
        uploaded = st.file_uploader("Upload CSV with 'customer_id' column",
                                     type=["csv"])
        if uploaded:
            df_up = pd.read_csv(uploaded)
            if "customer_id" not in df_up.columns:
                st.error("CSV must contain a 'customer_id' column.")
            else:
                st.info(f"Found {len(df_up)} customer IDs.")
                if st.button("Run Batch Prediction from CSV"):
                    ids = df_up["customer_id"].dropna().tolist()
                    with st.spinner(f"Running predictions for {len(ids)} customers..."):
                        result, err = api_post("/predict/churn/batch", {"customer_ids": ids})
                    if err:
                        st.error(err)
                    elif result:
                        _render_batch_results(result)


def _render_batch_results(result: dict | list):
    predictions = result if isinstance(result, list) else result.get("batch_results", [])

    cleaned = []
    for p in predictions:
        cleaned.append({k: (v.item() if hasattr(v, 'item') else v) for k, v in p.items()})
    predictions = cleaned

    if not predictions:
        st.warning("No predictions returned.")
        return

    df = pd.DataFrame(predictions)
    if "churn_probability" in df.columns:
        df["churn_probability"] = (df["churn_probability"] * 100).round(1)

    # Summary
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Processed", len(df))
    if "churn_probability" in df.columns:
        df["churn_probability"] = pd.to_numeric(df["churn_probability"], errors="coerce") * 100
    if "risk_level" in df.columns:
        c2.metric("High Risk",   int((df["risk_level"] == "High").sum()))
        c3.metric("Medium Risk", int((df["risk_level"] == "Medium").sum()))
        c4.metric("Low Risk",    int((df["risk_level"] == "Low").sum()))

    st.markdown("<br>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download results as CSV",
        data=csv,
        file_name=f"churn_batch_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )



# ── Paste everything below this line into dashboard_v2.py ────────────────────


def page_nlp():
    st.markdown("## NLP Insights")

    # ── Check pipeline status ──────────────────────────────────────────────
    stats_data, stats_err = api_get("/nlp/stats")
    if stats_err or not stats_data:
        st.error("NLP pipeline not ready.")
        st.code("python -m ml_models.nlp.pipeline", language="bash")
        st.info("Run the command above to build the search index and sentiment scores, then restart the API.")
        return

    # ── Top KPI strip ──────────────────────────────────────────────────────
    total_fb   = stats_data.get("total_feedback", 0)
    sent_dist  = stats_data.get("sentiment_distribution", {})
    trend_info = stats_data.get("trend", {})
    backend    = stats_data.get("index_stats", {}).get("backend", "unknown")

    pos_pct = sent_dist.get("positive", 0)
    neg_pct = sent_dist.get("negative", 0)
    neu_pct = sent_dist.get("neutral",  0)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Feedback",    f"{total_fb:,}")
    c2.metric("Positive",          f"{pos_pct:.1f}%",   delta_color="normal")
    c3.metric("Negative",          f"{neg_pct:.1f}%",   delta_color="inverse")
    c4.metric("Neutral",           f"{neu_pct:.1f}%",   delta_color="off")
    c5.metric("Search Backend",    backend.upper())

    if trend_info:
        direction = trend_info.get("direction", "stable")
        color_map = {"improving": COLORS["accent2"], "worsening": COLORS["danger"],
                     "stable": COLORS["muted"]}
        st.markdown(
            f'<div style="margin:0.5rem 0 1.5rem;padding:10px 16px;'
            f'background:{COLORS["surface"]};border-radius:8px;'
            f'border-left:3px solid {color_map.get(direction, COLORS["muted"])};">'
            f'<span style="color:{COLORS["muted"]};font-size:0.78rem;">SENTIMENT TREND &nbsp;</span>'
            f'<span style="font-size:0.88rem;">{trend_info.get("summary","")}</span></div>',
            unsafe_allow_html=True,
        )

    # ── Tabs ───────────────────────────────────────────────────────────────
    tab_search, tab_timeline, tab_breakdown = st.tabs(
        ["Semantic Search", "Sentiment Timeline", "Breakdown by Category"]
    )

    # ════════════════════════════════════════════════════════
    # TAB 1 — Semantic Search
    # ════════════════════════════════════════════════════════
    with tab_search:
        st.markdown(f"""
        <div class="sg-card" style="margin-bottom:1rem;">
            <div style="font-size:0.85rem;color:{COLORS['muted']};line-height:1.7;">
                Search customer feedback by <b>meaning</b>, not keywords.
                Try <em>"billing problem"</em> — it will find <em>"charged twice"</em>,
                <em>"wrong invoice"</em>, and <em>"unexpected fee"</em> even with zero
                word overlap.
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_q, col_k, col_s, col_btn = st.columns([4, 1, 2, 1])
        with col_q:
            query = st.text_input("Search query", placeholder="e.g. billing problem, slow internet, great support",
                                   label_visibility="collapsed")
        with col_k:
            top_k = st.number_input("Results", min_value=3, max_value=30, value=8,
                                     label_visibility="visible")
        with col_s:
            sentiment_filter = st.selectbox("Sentiment filter",
                                             ["All", "positive", "negative", "neutral"],
                                             label_visibility="visible")
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            do_search = st.button("Search →", use_container_width=True)

        # Suggested queries
        st.markdown(f'<div style="font-size:0.75rem;color:{COLORS["muted"]};margin-bottom:0.75rem;">'
                    f'Suggestions: &nbsp;', unsafe_allow_html=True)
        sugg_cols = st.columns(6)
        suggestions = ["billing problem", "slow internet", "great support",
                        "cancel service", "technical issue", "refund request"]
        for i, sugg in enumerate(suggestions):
            with sugg_cols[i]:
                if st.button(sugg, key=f"sugg_{i}", use_container_width=True):
                    query = sugg
                    do_search = True

        if do_search and query:
            params = {"q": query, "top_k": top_k}
            if sentiment_filter != "All":
                params["filter_sentiment"] = sentiment_filter

            with st.spinner(f'Searching for "{query}"...'):
                data, err = api_get("/nlp/search", params)

            if err:
                st.error(f"Search error: {err}")
            elif data and data.get("results"):
                results = data["results"]
                backend_used = data.get("backend", "unknown")

                st.markdown(
                    f'<div style="font-size:0.8rem;color:{COLORS["muted"]};margin-bottom:0.75rem;">'
                    f'Found <b style="color:{COLORS["text"]}">{len(results)}</b> results · '
                    f'Backend: <code style="color:{COLORS["accent"]}">{backend_used}</code></div>',
                    unsafe_allow_html=True,
                )

                for r in results:
                    score      = r.get("similarity_score", 0)
                    sentiment  = r.get("sentiment_label", "neutral")
                    sent_color = {"positive": COLORS["accent2"],
                                  "negative": COLORS["danger"],
                                  "neutral":  COLORS["muted"]}.get(sentiment, COLORS["muted"])
                    bar_width  = int(score * 100)

                    st.markdown(f"""
                    <div class="sg-card" style="padding:0.9rem 1.1rem;">
                        <div style="display:flex;justify-content:space-between;
                                    align-items:flex-start;gap:1rem;">
                            <div style="flex:1;font-size:0.88rem;line-height:1.55;">
                                {r.get("feedback_text","")}
                            </div>
                            <div style="text-align:right;min-width:90px;">
                                <div style="font-size:1.1rem;font-weight:600;
                                            color:{COLORS['accent']};">{score*100:.0f}%</div>
                                <div style="font-size:0.7rem;color:{COLORS['muted']};">match</div>
                            </div>
                        </div>
                        <div style="margin-top:8px;display:flex;gap:1rem;
                                    align-items:center;flex-wrap:wrap;">
                            <span style="font-size:0.75rem;color:{sent_color};">
                                ● {sentiment}
                            </span>
                            {'<span style="font-size:0.75rem;color:' + COLORS["muted"] + ';">' +
                              str(r.get("category","")).replace("_"," ") + '</span>'
                              if r.get("category") else ""}
                            {'<span style="font-size:0.75rem;color:' + COLORS["muted"] + ';">' +
                              str(r.get("channel","")) + '</span>'
                              if r.get("channel") else ""}
                            <span style="font-size:0.75rem;color:{COLORS['muted']};">
                                {str(r.get("customer_id",""))}
                            </span>
                        </div>
                        <div class="risk-bar-container" style="margin-top:8px;">
                            <div class="risk-bar-fill"
                                 style="width:{bar_width}%;background:{COLORS['accent']};
                                        opacity:0.5;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No results found. Try a different query.")

    # ════════════════════════════════════════════════════════
    # TAB 2 — Sentiment Timeline
    # ════════════════════════════════════════════════════════
    with tab_timeline:
        col_freq, _ = st.columns([2, 5])
        with col_freq:
            freq = st.selectbox("Aggregation", ["W — Weekly", "ME — Monthly", "D — Daily"],
                                 label_visibility="visible")
        freq_code = freq.split(" ")[0]

        with st.spinner("Loading sentiment timeline..."):
            tl_data, tl_err = api_get("/nlp/sentiment/timeline", {"freq": freq_code})

        if tl_err or not tl_data:
            st.error(f"Timeline error: {tl_err}")
        else:
            timeline = tl_data.get("timeline", [])
            trend    = tl_data.get("trend", {})

            if trend:
                direction = trend.get("direction", "stable")
                col_map   = {"improving": COLORS["accent2"], "worsening": COLORS["danger"],
                             "stable": COLORS["muted"]}
                st.markdown(
                    f'<div class="sg-card" style="border-left:3px solid '
                    f'{col_map.get(direction, COLORS["muted"])};padding:0.75rem 1rem;'
                    f'margin-bottom:1rem;">'
                    f'<span style="font-size:0.88rem;">{trend.get("summary","")}</span>'
                    f'<span style="font-size:0.78rem;color:{COLORS["muted"]};margin-left:1rem;">'
                    f'Recent avg: {trend.get("recent_avg",""):.1f}pp &nbsp; vs &nbsp; '
                    f'Prior avg: {trend.get("older_avg",""):.1f}pp</span></div>',
                    unsafe_allow_html=True,
                )

            if timeline:
                df_tl = pd.DataFrame(timeline)

                # ── Stacked area chart ──
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_tl["period"], y=df_tl["positive_pct"],
                    name="Positive", mode="lines",
                    line=dict(color=COLORS["accent2"], width=2),
                    fill="tozeroy",
                    fillcolor="rgba(16,185,129,0.12)",
                    hovertemplate="%{x}: %{y:.1f}%<extra>Positive</extra>",
                ))
                fig.add_trace(go.Scatter(
                    x=df_tl["period"], y=df_tl["negative_pct"],
                    name="Negative", mode="lines",
                    line=dict(color=COLORS["danger"], width=2),
                    fill="tozeroy",
                    fillcolor="rgba(239,68,68,0.10)",
                    hovertemplate="%{x}: %{y:.1f}%<extra>Negative</extra>",
                ))
                # Net sentiment line
                fig.add_trace(go.Scatter(
                    x=df_tl["period"], y=df_tl["net_sentiment"],
                    name="Net sentiment", mode="lines+markers",
                    line=dict(color=COLORS["accent"], width=2.5, dash="dot"),
                    marker=dict(size=5),
                    hovertemplate="%{x}: %{y:.1f}pp<extra>Net</extra>",
                ))
                # Zero line
                fig.add_hline(y=0, line_color=COLORS["border"], line_width=1)

                fig.update_layout(
                    **PLOTLY_TEMPLATE["layout"],
                    title=dict(text="Sentiment over time", font=dict(size=14), x=0),
                    height=340,
                    hovermode="x unified",
                    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h",
                                yanchor="bottom", y=1.02, xanchor="right", x=1),
                    yaxis_title="% of feedback",
                    margin=dict(l=10, r=10, t=40, b=10),
                )
                st.plotly_chart(fig, use_container_width=True,
                                config={"displayModeBar": False})

                # Volume bars
                fig2 = go.Figure(go.Bar(
                    x=df_tl["period"], y=df_tl["total_count"],
                    marker_color=COLORS["accent"],
                    opacity=0.6,
                    hovertemplate="%{x}: %{y} tickets<extra></extra>",
                ))
                fig2.update_layout(
                    **PLOTLY_TEMPLATE["layout"],
                    title=dict(text="Feedback volume", font=dict(size=13), x=0),
                    height=160,
                    showlegend=False,
                    margin=dict(l=10, r=10, t=35, b=10),
                )
                st.plotly_chart(fig2, use_container_width=True,
                                config={"displayModeBar": False})

    # ════════════════════════════════════════════════════════
    # TAB 3 — Breakdown
    # ════════════════════════════════════════════════════════
    with tab_breakdown:
        with st.spinner("Loading sentiment breakdown..."):
            summ_data, summ_err = api_get("/nlp/sentiment/summary")

        if summ_err or not summ_data:
            st.error(f"Summary error: {summ_err}")
            return

        col_overall, col_channel = st.columns(2)

        with col_overall:
            # Overall donut
            overall = summ_data.get("overall", {})
            if overall:
                fig = go.Figure(go.Pie(
                    labels=list(overall.keys()),
                    values=list(overall.values()),
                    hole=0.55,
                    marker=dict(
                        colors=[
                            COLORS["accent2"] if k == "positive"
                            else COLORS["danger"] if k == "negative"
                            else COLORS["muted"]
                            for k in overall.keys()
                        ],
                        line=dict(color=COLORS["bg"], width=2),
                    ),
                    textfont=dict(color=COLORS["text"]),
                    hovertemplate="<b>%{label}</b>: %{value:.1f}%<extra></extra>",
                ))
                fig.update_layout(
                    **PLOTLY_TEMPLATE["layout"],
                    title=dict(text="Overall sentiment", font=dict(size=14), x=0),
                    height=280,
                    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="v"),
                    margin=dict(l=10, r=10, t=40, b=10),
                )
                st.plotly_chart(fig, use_container_width=True,
                                config={"displayModeBar": False})

        with col_channel:
            # Negative rate by channel
            by_channel = summ_data.get("by_channel", {})
            if by_channel:
                channels   = list(by_channel.keys())
                neg_rates  = [by_channel[ch].get("negative", 0) for ch in channels]
                fig2 = go.Figure(go.Bar(
                    x=channels, y=neg_rates,
                    marker=dict(
                        color=neg_rates,
                        colorscale=[[0, COLORS["accent2"]], [1, COLORS["danger"]]],
                    ),
                    text=[f"{v:.0f}%" for v in neg_rates],
                    textposition="outside",
                    textfont=dict(color=COLORS["text"]),
                    hovertemplate="<b>%{x}</b><br>Negative: %{y:.1f}%<extra></extra>",
                ))
                fig2.update_layout(
                    **PLOTLY_TEMPLATE["layout"],
                    title=dict(text="Negative rate by channel", font=dict(size=14), x=0),
                    height=280,
                    showlegend=False,
                    margin=dict(l=10, r=10, t=40, b=10),
                )
                st.plotly_chart(fig2, use_container_width=True,
                                config={"displayModeBar": False})

        # Category breakdown heatmap-style bars
        by_category = summ_data.get("by_category", {})
        if by_category:
            st.markdown('<div class="sg-section-header" style="margin-top:1rem;">'
                        'Sentiment by category</div>', unsafe_allow_html=True)

            for cat, dist in by_category.items():
                pos = dist.get("positive", 0)
                neg = dist.get("negative", 0)
                neu = dist.get("neutral", 0)
                st.markdown(f"""
                <div class="sg-card" style="padding:0.7rem 1rem;">
                    <div style="display:flex;justify-content:space-between;
                                align-items:center;margin-bottom:6px;">
                        <span style="font-size:0.83rem;font-weight:500;">
                            {cat.replace("_"," ").title()}
                        </span>
                        <span style="font-size:0.75rem;color:{COLORS['muted']};">
                            <span style="color:{COLORS['accent2']};">+{pos:.0f}%</span>
                            &nbsp;
                            <span style="color:{COLORS['danger']}">{neg:.0f}%</span>
                        </span>
                    </div>
                    <div style="display:flex;height:6px;border-radius:100px;overflow:hidden;">
                        <div style="width:{pos}%;background:{COLORS['accent2']};"></div>
                        <div style="width:{neu}%;background:{COLORS['muted']};opacity:0.4;"></div>
                        <div style="width:{neg}%;background:{COLORS['danger']};"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    inject_css()
    page = render_sidebar()

    if page == "Overview":
        page_overview()
    elif page == "Customer Analysis":
        page_customer_analysis()
    elif page == "Demand Forecast":
        page_forecast()
    elif page == "High Risk":
        page_high_risk()
    elif page == "Batch":
        page_batch()
    elif page == "NLP Insights":
        page_nlp()



if __name__ == "__main__":
    main()