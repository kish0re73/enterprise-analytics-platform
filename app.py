import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analytics"))
from analytics_engine import (load_fact_sales, rfm_segmentation, forecast_revenue,
                               churn_prediction, anomaly_detection, kmeans_segmentation,
                               demand_forecast, kpi_suite, forecast_accuracy_backtest,
                               generate_business_insights)

DB_URL = os.environ.get("BI_DB_URL", "postgresql://postgres:postgres@localhost:5432/bi_warehouse")


@st.cache_data(ttl=3600)
def get_sales():
    return load_fact_sales()


@st.cache_data(ttl=3600)
def get_rfm(_sales):
    return rfm_segmentation(_sales)


@st.cache_data(ttl=3600)
def get_forecast(_sales, periods=3):
    return forecast_revenue(_sales, periods)


@st.cache_data(ttl=3600)
def get_churn(_sales):
    return churn_prediction(_sales)


@st.cache_data(ttl=3600)
def get_anomalies(_sales):
    return anomaly_detection(_sales)


@st.cache_data(ttl=3600)
def get_kmeans(_sales):
    return kmeans_segmentation(_sales)


@st.cache_data(ttl=3600)
def get_demand_forecast(_sales, top_n=8, periods=3):
    return demand_forecast(_sales, top_n, periods)


@st.cache_data(ttl=3600)
def get_kpi_suite(_sales):
    return kpi_suite(_sales)


@st.cache_data(ttl=3600)
def get_forecast_accuracy(_sales):
    return forecast_accuracy_backtest(_sales)


@st.cache_data(ttl=3600)
def get_ai_insights(_sales, _rfm):
    return generate_business_insights(_sales, _rfm)
