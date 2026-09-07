"""Hoja 4 — Desempeño, estabilidad y explicación del modelo."""

from pathlib import Path
import sys

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.data import load_view, page_header


page_header("Modelo predictivo", "¿Qué tan confiable, estable y explicable es el scoring?")
metrics = load_view("model")
importance = load_view("importance")
capacity = load_view("capacity")

tab_metrics, tab_capacity, tab_features = st.tabs(
    ["Desempeño", "Capacidad", "Variables importantes"]
)
with tab_metrics:
    if metrics.empty:
        st.info("Aún no hay métricas de un modelo activo.")
    else:
        chart = metrics[metrics["metric_name"].isin(["roc_auc", "average_precision"])]
        st.plotly_chart(
            px.bar(chart, x="evaluation_scope", y="metric_value", color="metric_name", barmode="group"),
            use_container_width=True,
        )
with tab_capacity:
    if capacity.empty:
        st.info("Aún no hay métricas de capacidad.")
    else:
        st.plotly_chart(
            px.line(capacity, x="capacity_fraction", y="recall_at_k", color="evaluation_scope", markers=True),
            use_container_width=True,
        )
with tab_features:
    if importance.empty:
        st.info("Aún no hay importancia de variables.")
    else:
        top = importance.sort_values("feature_rank").head(15)
        st.plotly_chart(
            px.bar(top, x="importance_value", y="feature_name", orientation="h"),
            use_container_width=True,
        )
