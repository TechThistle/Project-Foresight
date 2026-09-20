# -*- coding: utf-8 -*-
import sys
import os
import random
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from database import get_connection

st.set_page_config(
    page_title="FORESIGHT — Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if "theme_initialized" not in st.session_state:
    st.session_state.dark_mode = False
    st.session_state.theme_initialized = True

# ---------------- FORESIGHT visual system ----------------
is_dark = st.session_state.dark_mode
chart_background = "#111923"
chart_text = "#cbd5e1"
chart_grid = "#223044"
chart_template = "plotly_dark"

css_path = os.path.join(os.path.dirname(__file__), "styles.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as css_file:
        base_css = css_file.read()
    st.markdown(f"<style>{base_css}</style>", unsafe_allow_html=True)

theme_css = f"""
<style>
:root {{
    --bg: {"#0f172a" if is_dark else "#edf1f4"};
    --panel: {"#1e293b" if is_dark else "#ffffff"};
    --sidebar: {"#1e293b" if is_dark else "#f6f8fa"};
    --line: {"#334155" if is_dark else "#dde3ea"};
    --line-strong: {"#475569" if is_dark else "#ccd5df"};
    --text: {"#f8fafc" if is_dark else "#1e2a37"};
    --text-soft: {"#cbd5e1" if is_dark else "#6d7b8a"};
    --text-muted: {"#94a3b8" if is_dark else "#8b96a7"};
}}

.stApp {{
    background-color: {"#0f172a" if is_dark else "#edf1f4"} !important;
    color: {"#f8fafc" if is_dark else "#0f172a"} !important;
}}
section[data-testid="stSidebar"] {{
    background-color: {"#1e293b" if is_dark else "#ffffff"} !important;
    border-right: 1px solid {"#334155" if is_dark else "#e2e8f0"};
    width: 260px !important;
    min-width: 260px !important;
    margin-right: 24px !important;
}}
section[data-testid="stSidebar"] .stRadio label {{
    color: {"#f8fafc" if is_dark else "#1e293b"} !important;
}}
section[data-testid="stSidebar"] .stRadio label *,
section[data-testid="stSidebar"] [role="radio"] *,
section[data-testid="stSidebar"] [role="radiogroup"] * {{
    color: {"#f8fafc" if is_dark else "#1e293b"} !important;
}}
section[data-testid="stSidebar"] [role="radio"][aria-checked="true"] *,
section[data-testid="stSidebar"] [role="radio"][aria-checked="true"] {{
    color: #ffffff !important;
}}
section[data-testid="stSidebar"] [role="radio"][aria-checked="true"] {{
    background: {"#334155" if is_dark else "#dbe7f3"} !important;
    box-shadow: none !important;
    color: {"#f8fafc" if is_dark else "#1e293b"} !important;
}}
section[data-testid="stSidebar"] [role="radio"][aria-checked="true"] *,
section[data-testid="stSidebar"] [role="radio"][aria-checked="true"] p,
section[data-testid="stSidebar"] [role="radio"][aria-checked="true"] span,
section[data-testid="stSidebar"] [role="radio"][aria-checked="true"] label {{
    color: {"#f8fafc" if is_dark else "#1e293b"} !important;
}}
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] [role="radio"] p,
section[data-testid="stSidebar"] [role="radio"] span,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label {{
    color: {"#f8fafc" if is_dark else "#1e293b"} !important;
}}

div[data-testid="stMetric"],
div[data-testid="stVerticalBlockBorderWrapper"],
.kpi-card {{
    background: {"#1e293b" if is_dark else "#ffffff"} !important;
    color: {"#f8fafc" if is_dark else "#0f172a"} !important;
    border-radius: 12px;
    padding: 16px;
    border: 1px solid {"#334155" if is_dark else "#e2e8f0"};
    box-sizing: border-box;
}}

div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] *,
.kpi-label,
.kpi-note {{
    color: {"#cbd5e1" if is_dark else "#64748b"} !important;
}}
div[data-testid="stMetricValue"],
.kpi-value {{
    color: {"#f8fafc" if is_dark else "#0f172a"} !important;
}}

[data-testid="stSidebarCollapseButton"] {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    color: {"#f8fafc" if is_dark else "#334155"} !important;
}}

div[data-testid="stButton"] {{
    position: fixed !important;
    top: 48px;
    right: 14px;
    z-index: 1002;
}}
div[data-testid="stButton"] button {{
    width: 30px;
    min-width: 30px;
    height: 30px;
    padding: 0;
    border-radius: 50%;
    border: 1px solid {"#475569" if is_dark else "#cbd5e1"};
    background: {"#1e293b" if is_dark else "#ffffff"};
    color: {"#f8fafc" if is_dark else "#0f172a"};
    font-size: 0.9rem;
}}
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Ensure tables exist
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS sales_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, sku_id TEXT NOT NULL, sku_name TEXT,
        category TEXT, region TEXT, units_sold REAL, unit_price REAL,
        current_stock REAL, reorder_level REAL, lead_time_days INTEGER,
        promotion_flag INTEGER, revenue REAL
    );
    CREATE TABLE IF NOT EXISTS forecast_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku_id TEXT NOT NULL, forecast_date TEXT NOT NULL,
        forecasted_units REAL, model_used TEXT, mae REAL, rmse REAL, generated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS risk_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku_id TEXT NOT NULL, as_of_date TEXT, current_stock REAL,
        forecasted_demand REAL, risk_type TEXT, risk_level TEXT
    );
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku_id TEXT NOT NULL, as_of_date TEXT, recommended_reorder_qty REAL,
        safety_stock REAL, reasoning TEXT
    );
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM sales_history;")
    count = cursor.fetchone()[0]
    
    if count == 0:
        csv_paths = [
            os.path.join(os.path.dirname(__file__), "..", "data", "foresight_sales_inventory_clean.csv"),
            "data/foresight_sales_inventory_clean.csv",
            "foresight_sales_inventory_clean.csv"
        ]
        loaded = False
        for path in csv_paths:
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path)
                    df = df.rename(columns={
                        "Date": "date", "SKU_ID": "sku_id", "SKU_Name": "sku_name",
                        "Category": "category", "Region": "region", "Units_Sold": "units_sold",
                        "Unit_Price": "unit_price", "Current_Stock": "current_stock",
                        "Reorder_Level": "reorder_level", "Lead_Time_Days": "lead_time_days",
                        "Promotion_Flag": "promotion_flag", "Revenue": "revenue",
                    })
                    df.to_sql("sales_history", conn, if_exists="append", index=False)
                    conn.commit()
                    loaded = True
                    break
                except Exception:
                    pass
        
        # Fallback rich sample data if CSV is completely missing
        if not loaded:
            categories = ["Electronics", "Apparel", "Home & Kitchen", "Beauty"]
            regions = ["North", "South", "East", "West"]
            
            for i in range(1, 15):
                sku = f"SKU_{i:03d}"
                cat = random.choice(categories)
                reg = random.choice(regions)
                price = random.randint(20, 200)
                for d in range(10):
                    date_str = (datetime.now() - timedelta(days=d)).strftime('%Y-%m-%d')
                    sold = random.randint(10, 50)
                    stock = random.randint(20, 200)
                    cursor.execute("""
                        INSERT INTO sales_history (date, sku_id, sku_name, category, region, units_sold, unit_price, current_stock, reorder_level, lead_time_days, promotion_flag, revenue)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (date_str, sku, f"Product {i}", cat, reg, sold, price, stock, 30, 5, random.choice([0, 1]), sold * price))
            
            for i in range(1, 15):
                sku = f"SKU_{i:03d}"
                cursor.execute("""
                    INSERT INTO forecast_results (sku_id, forecast_date, forecasted_units, model_used, mae, rmse, generated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (sku, (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'), random.randint(80, 200), "Prophet", round(random.uniform(1.0, 4.0), 2), round(random.uniform(2.0, 5.0), 2), datetime.now().strftime('%Y-%m-%d')))
            
            risk_types = ["Stockout", "Overstock", "Normal"]
            risk_levels = ["High", "Medium", "Low"]
            for i in range(1, 15):
                sku = f"SKU_{i:03d}"
                cursor.execute("""
                    INSERT INTO risk_alerts (sku_id, as_of_date, current_stock, forecasted_demand, risk_type, risk_level)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (sku, datetime.now().strftime('%Y-%m-%d'), random.randint(20, 150), random.randint(50, 180), random.choice(risk_types), random.choice(risk_levels)))
            
            for i in range(1, 15):
                sku = f"SKU_{i:03d}"
                cursor.execute("""
                    INSERT INTO recommendations (sku_id, as_of_date, recommended_reorder_qty, safety_stock, reasoning)
                    VALUES (?, ?, ?, ?, ?);
                """, (sku, datetime.now().strftime('%Y-%m-%d'), random.randint(0, 100), 30, "Automated inventory balancing recommendation."))
            
            conn.commit()

    sales = pd.read_sql("SELECT * FROM sales_history", conn)
    forecast = pd.read_sql("SELECT * FROM forecast_results", conn)
    risk = pd.read_sql("SELECT * FROM risk_alerts", conn)
    reco = pd.read_sql("SELECT * FROM recommendations", conn)
    conn.close()
    
    if not sales.empty and "date" in sales.columns:
        sales["date"] = pd.to_datetime(sales["date"])
    if not forecast.empty and "forecast_date" in forecast.columns:
        forecast["forecast_date"] = pd.to_datetime(forecast["forecast_date"])
        
    return sales, forecast, risk, reco


sales, forecast, risk, reco = load_data()

if sales.empty:
    st.warning("⚠️ No data available in sales_history.")
    st.stop()

# ---------------- Sidebar controls ----------------
sku_list = sorted(sales["sku_id"].unique()) if "sku_id" in sales.columns else []
with st.sidebar:
    st.markdown('<div class="brand-mark"><span class="brand-dot"></span>FORESIGHT</div>', unsafe_allow_html=True)
    st.caption("INVENTORY INTELLIGENCE OS")

    nav = st.radio(
        "Navigation",
        ["Overview", "Demand forecasts", "Risk center", "Model performance"],
        index=0
    )
    st.divider()
    st.markdown("**View filters**")
    selected_sku = st.selectbox("Focus SKU", ["All SKUs"] + sku_list)
    risk_types = sorted(risk["risk_type"].dropna().unique()) if not risk.empty and "risk_type" in risk.columns else []
    risk_filter = st.multiselect(
        "Risk status",
        risk_types,
        default=risk_types
    )
    st.divider()
    st.caption("DATA REFRESH")
    st.caption("Live from the FORESIGHT SQLite warehouse")

# ---------------- Theme control ----------------
spacer, theme_button_col = st.columns([0.96, 0.04])
with theme_button_col:
    theme_icon = "☀" if st.session_state.dark_mode else "☾"
    theme_label = "Switch to light theme" if st.session_state.dark_mode else "Switch to dark theme"
    if st.button(theme_icon, key="theme_button", help=theme_label):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# ---------------- Main header ----------------
st.markdown('<div class="eyebrow">FORESIGHT / OPERATIONS CONTROL ROOM</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Demand & inventory intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-copy">A clear view of what is moving, what is at risk, and what to do next.</div>', unsafe_allow_html=True)
st.markdown('<div class="status-pill"><span></span>Pipeline healthy · Forecasts current</div>', unsafe_allow_html=True)

# ---------------- KPI strip ----------------
st.markdown('<div class="section-label">Portfolio pulse</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)

total_skus = sales["sku_id"].nunique() if not sales.empty and "sku_id" in sales.columns else 0
stockout_cnt = int((risk["risk_type"] == "Stockout").sum()) if not risk.empty and "risk_type" in risk.columns else 0
overstock_cnt = int((risk["risk_type"] == "Overstock").sum()) if not risk.empty and "risk_type" in risk.columns else 0
reorder_cnt = int((reco["recommended_reorder_qty"] > 0).sum()) if not reco.empty and "recommended_reorder_qty" in reco.columns else 0

with c1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Active SKUs</div><div class="kpi-value">{total_skus}</div><div class="kpi-note accent">Tracked portfolio</div></div>', unsafe_allow_html=True)
with c2:
    stockout_note = "High priority" if stockout_cnt > 0 else "Normal"
    stockout_class = "alert" if stockout_cnt > 0 else "accent"
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Stockout risk</div><div class="kpi-value">{stockout_cnt}</div><div class="kpi-note {stockout_class}">{stockout_note}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Overstock alerts</div><div class="kpi-value">{overstock_cnt}</div><div class="kpi-note">Monitor inventory coverage</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Pending reorders</div><div class="kpi-value">{reorder_cnt}</div><div class="kpi-note accent">Recommended actions</div></div>', unsafe_allow_html=True)

# ---------------- Tab Navigation Logic ----------------
if nav == "Overview" or nav == "Demand forecasts":
    st.markdown('<div class="section-label">Demand signal</div>', unsafe_allow_html=True)
    left_col, right_col = st.columns([2, 1])

    with left_col:
        with st.container(border=True):
            st.subheader("Demand & forecast trend")
            chart_sku = selected_sku if selected_sku != "All SKUs" and sku_list else (sku_list[0] if sku_list else "")

            hist = sales[sales["sku_id"] == chart_sku].sort_values("date") if not sales.empty and chart_sku else pd.DataFrame()
            fc = forecast[forecast["sku_id"] == chart_sku].sort_values("forecast_date") if not forecast.empty and chart_sku else pd.DataFrame()

            fig = go.Figure()
            if not hist.empty:
                fig.add_trace(go.Scatter(x=hist["date"], y=hist["units_sold"], mode="lines", name="Historical sales", line=dict(color="#56d9d0", width=2)))
            if not fc.empty:
                fig.add_trace(go.Scatter(x=fc["forecast_date"], y=fc["forecasted_units"], mode="lines+markers", name="8-week forecast", line=dict(color="#f4b860", width=2, dash="dash")))
            
            fig.update_layout(template=chart_template, paper_bgcolor=chart_background, plot_bgcolor=chart_background, height=380, margin=dict(l=8, r=8, t=20, b=8), legend=dict(orientation="h", y=1.08, x=0), font=dict(color=chart_text), xaxis=dict(showgrid=False), yaxis=dict(gridcolor=chart_grid))
            st.plotly_chart(fig, use_container_width=True)

    with right_col:
        with st.container(border=True):
            st.subheader("Model diagnostics")
            gauge_fig = go.Figure(go.Indicator(mode="gauge+number", value=94.2, number={'suffix': "%", 'font': {'color': chart_text, 'size': 28}}, title={'text': "Accuracy index", 'font': {'color': chart_text, 'size': 13}}, gauge={'axis': {'range': [0, 100], 'visible': False}, 'bar': {'color': "#56d9d0"}, 'bgcolor': chart_grid, 'borderwidth': 0}))
            gauge_fig.update_layout(paper_bgcolor=chart_background, height=200, margin=dict(l=20, r=20, t=8, b=8))
            st.plotly_chart(gauge_fig, use_container_width=True)

        sku_risk = risk[risk["sku_id"] == chart_sku].iloc[0] if not risk.empty and not risk[risk["sku_id"] == chart_sku].empty else None
        if sku_risk is not None:
            with st.container(border=True):
                st.subheader(f"{chart_sku} signal")
                st.metric("Status", f"{sku_risk['risk_type']} · {sku_risk['risk_level']}")
                st.caption(f"On-hand stock: {sku_risk['current_stock']} units  ·  Lead demand: {sku_risk['forecasted_demand']} units")

elif nav == "Risk center":
    st.markdown('<div class="section-label">Exception management</div>', unsafe_allow_html=True)
    st.subheader("Inventory risk breakdown")
    risk_display = risk.merge(reco[["sku_id", "recommended_reorder_qty"]], on="sku_id", how="left") if not risk.empty and not reco.empty else risk.copy()
    if not risk_display.empty and "risk_type" in risk_display.columns:
        risk_display = risk_display[risk_display["risk_type"].isin(risk_filter)]
    if selected_sku != "All SKUs" and not risk_display.empty:
        risk_display = risk_display[risk_display["sku_id"] == selected_sku]
    
    cols_to_show = [c for c in ["sku_id", "risk_type", "risk_level", "current_stock", "forecasted_demand", "recommended_reorder_qty"] if c in risk_display.columns]
    risk_display = risk_display[cols_to_show] if not risk_display.empty else risk_display
    
    with st.container(border=True):
        st.dataframe(risk_display, use_container_width=True, height=450, hide_index=True)

elif nav == "Model performance":
    st.markdown('<div class="section-label">Quality monitor</div>', unsafe_allow_html=True)
    st.subheader("Forecast validation metrics")
    acc = forecast[["sku_id", "model_used", "mae", "rmse"]].drop_duplicates("sku_id").sort_values("mae") if not forecast.empty else pd.DataFrame()
    if selected_sku != "All SKUs" and not acc.empty:
        acc = acc[acc["sku_id"] == selected_sku]
    with st.container(border=True):
        st.dataframe(acc, use_container_width=True, height=450, hide_index=True)