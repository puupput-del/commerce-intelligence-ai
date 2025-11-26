# app.py
"""Main Streamlit app (lightweight).
This file keeps UI flow simple and imports helpers from utils.py and groq_client.py
"""
import streamlit as st
from utils import (
    infer_and_prepare_df, aggregate_sales, compute_key_metrics,
    prepare_groq_context_for_summary
)
from groq_client import GroqClient
import pandas as pd

st.set_page_config(page_title="Digital Commerce Intelligence AI", layout="wide")
st.title("Digital Commerce Intelligence AI – Sales Insight & Smart Decisions")
st.markdown("Upload your transactions (.xlsx) and explore sales analytics with optional AI insights.")

# Sidebar: upload and settings
with st.sidebar:
    uploaded = st.file_uploader("Upload transactions Excel (.xlsx)", type=["xlsx"])
    sample = st.button("Use sample data")
    st.markdown("---")
    st.write("Groq API Key: set in .env or Streamlit Secrets")
    st.markdown("If Groq not configured, AI features will be disabled.")

if sample and not uploaded:
    df = pd.read_excel('sample_transactions.xlsx')
elif uploaded:
    try:
        df = pd.read_excel(uploaded, sheet_name=0)
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        st.stop()
else:
    st.info("Please upload a transactions .xlsx file or click 'Use sample data'.")
    st.stop()

# Prepare data and mapping
df_prep, mapping = infer_and_prepare_df(df)

st.sidebar.subheader("Column mapping")
date_col = st.sidebar.selectbox("Date column", options=list(df_prep.columns), index=list(df_prep.columns).index(mapping['date_col']))
product_col = st.sidebar.selectbox("Product column", options=list(df_prep.columns), index=list(df_prep.columns).index(mapping['product_col']))
category_col = st.sidebar.selectbox("Category column", options=list(df_prep.columns), index=list(df_prep.columns).index(mapping['category_col']))
totals_col = st.sidebar.selectbox("Total sales column", options=list(df_prep.columns), index=list(df_prep.columns).index(mapping['totals_col']))

# Filters
st.header("Filters & Preview")
df_prep[date_col] = pd.to_datetime(df_prep[date_col], errors="coerce")
min_d = df_prep[date_col].min()
max_d = df_prep[date_col].max()
date_range = st.date_input("Date range", value=(min_d.date() if pd.notna(min_d) else None, max_d.date() if pd.notna(max_d) else None))
if date_range and len(date_range)==2:
    start_dt, end_dt = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_filtered = df_prep[(df_prep[date_col]>=start_dt) & (df_prep[date_col]<=end_dt)]
else:
    df_filtered = df_prep.copy()

st.subheader("Data preview")
st.dataframe(df_filtered.head(20))

# KPIs and aggregations
st.header("Key Metrics & Top Lists")
kpis = compute_key_metrics(df_filtered, totals_col, mapping.get('qty_col','Qty'), date_col=date_col)
c1,c2,c3,c4 = st.columns(4)
c1.metric("Total Sales", f"{kpis['total_sales']:.2f}")
c2.metric("Transactions", f"{kpis['num_transactions']}")
c3.metric("Avg Transaction Value", f"{kpis['avg_transaction_value']:.2f}")
c4.metric("Avg Basket Size", f"{kpis['avg_basket_size']:.2f}")

top_products = aggregate_sales(df_filtered, product_col, totals_col)
top_categories = aggregate_sales(df_filtered, category_col, totals_col)

st.subheader("Top Products")
st.dataframe(top_products.head(10))
st.subheader("Top Categories")
st.dataframe(top_categories.head(10))

# Visualizations using utils
st.header("Visualizations")
from utils import plot_top_products, plot_sales_trend, plot_category_pie
st.plotly_chart(plot_top_products(top_products.head(10), product_col, totals_col), use_container_width=True)
st.plotly_chart(plot_sales_trend(df_filtered, date_col, totals_col), use_container_width=True)
st.plotly_chart(plot_category_pie(top_categories.head(20), category_col, totals_col), use_container_width=True)

# Export
st.download_button("Download processed CSV", df_filtered.to_csv(index=False), file_name="processed_sales.csv", mime="text/csv")

# Groq AI insights
st.header("AI Insights (Groq)")
client = GroqClient()
context = prepare_groq_context_for_summary(kpis, top_products, top_categories, n=10)
if client.is_configured():
    if st.button("Generate AI Insights (Auto)"):
        with st.spinner("Generating AI insights..."):
            summary = client.summarize(context)
            st.subheader("Executive Summary & Recommendations")
            st.write(summary)
    q = st.text_input("Ask a question about the data")
    if q and st.button("Ask AI"):
        with st.spinner("AI is thinking..."):
            ans = client.answer_question(context, q)
            st.write(ans)
else:
    st.info("Groq not configured. Set GROQ_API_KEY in .env or Streamlit Secrets to enable AI features.")\n