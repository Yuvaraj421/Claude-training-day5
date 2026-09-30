"""Pharma Risk Analyzer - Streamlit Application."""
import streamlit as st
import pandas as pd
import plotly.express as px
from risk_analyzer import PharmaRiskAnalyzer
import os

st.set_page_config(page_title="Pharma Risk Analyzer", layout="wide")

st.title("🏥 Pharma Shipment Risk Analyzer")
st.markdown("Analyze pharmaceutical supply chain shipments for temperature excursions and compliance risks.")

# Sidebar for file upload and settings
with st.sidebar:
    st.header("Configuration")
    uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
    risk_threshold = st.slider("High-Risk Threshold", 20, 80, 40, 5)
    show_sample = st.checkbox("Use sample data", value=True)

# Load data
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success(f"✅ Loaded {len(df)} shipments from uploaded file")
elif show_sample and os.path.exists("sample_shipments.xlsx"):
    df = pd.read_excel("sample_shipments.xlsx")
    st.info(f"📊 Using sample data: {len(df)} shipments")
else:
    st.warning("Please upload an Excel file or enable sample data")
    st.stop()

# Analyze data
analyzer = PharmaRiskAnalyzer(df)
stats = analyzer.get_statistics()

# Display key metrics
st.header("📈 Key Metrics")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Shipments", stats['total_shipments'])

with col2:
    st.metric("High-Risk Shipments", stats['high_risk_count'],
              f"{(stats['high_risk_count']/stats['total_shipments']*100):.1f}%")

with col3:
    st.metric("Temp Excursions", stats['excursion_count'],
              f"{(stats['excursion_count']/stats['total_shipments']*100):.1f}%")

with col4:
    st.metric("Avg Risk Score", f"{stats['avg_risk_score']:.1f}", delta=f"Max: {stats['max_risk_score']:.0f}")

with col5:
    status_colors = {"Delivered": "✅", "In Transit": "🚚", "Delayed": "⏱️"}
    delayed_count = len(df[df['Status'] == 'Delayed'])
    st.metric("Delayed Shipments", delayed_count, status_colors.get(df['Status'].iloc[0], "📦"))

# Charts and Details
col_chart, col_list = st.columns([2, 1])

with col_chart:
    st.subheader("Risk Distribution")
    risk_dist = analyzer.get_risk_distribution()

    # Create risk distribution chart
    fig = px.bar(
        x=risk_dist.index.astype(str),
        y=risk_dist.values,
        labels={'x': 'Risk Level', 'y': 'Number of Shipments'},
        color=risk_dist.index.astype(str),
        color_discrete_sequence=['#2ecc71', '#f39c12', '#e74c3c', '#c0392b', '#8b0000'],
        title="Shipment Risk Categories"
    )
    fig.update_layout(showlegend=False, hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

with col_list:
    st.subheader("Top 5 Highest-Risk")
    high_risk = analyzer.get_high_risk_shipments(risk_threshold).head(5)
    if len(high_risk) > 0:
        for idx, row in high_risk.iterrows():
            risk_icon = "🔴" if row['Risk_Score'] >= 60 else "🟠"
            st.write(f"{risk_icon} {row['Shipment_ID']}: {row['Risk_Score']:.0f}")
    else:
        st.info("No high-risk shipments found")

# AI-Style Recommendations
st.header("🤖 AI Recommendations")
recommendations = analyzer.generate_recommendations()
for rec in recommendations:
    st.markdown(rec)

# Detailed view
with st.expander("View Top 10 Highest-Risk Shipments", expanded=False):
    top_10 = analyzer.get_high_risk_shipments(risk_threshold).head(10)
    if len(top_10) > 0:
        display_cols = ['Shipment_ID', 'Product', 'Destination', 'Risk_Score', 'Temp_Excursion', 'Status']
        st.dataframe(top_10[display_cols].style.format({'Risk_Score': '{:.1f}'}), use_container_width=True)
    else:
        st.info("No high-risk shipments to display")

with st.expander("View Temperature Excursions", expanded=False):
    excursions = analyzer.get_temperature_excursions()
    if len(excursions) > 0:
        display_cols = ['Shipment_ID', 'Product', 'Temp_Min_C', 'Temp_Max_C', 'Required_Min_C', 'Required_Max_C']
        st.dataframe(excursions[display_cols].style.format({
            'Temp_Min_C': '{:.2f}',
            'Temp_Max_C': '{:.2f}',
            'Required_Min_C': '{:.2f}',
            'Required_Max_C': '{:.2f}',
        }), use_container_width=True)
    else:
        st.info("No temperature excursions detected")

# Footer
st.divider()
st.caption("Pharma Risk Analyzer v1.0 | Real-time supply chain compliance monitoring")
