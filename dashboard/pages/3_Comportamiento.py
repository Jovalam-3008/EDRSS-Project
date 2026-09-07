"""Hoja 3 — Diferencias de comportamiento asociadas a la mora."""

from pathlib import Path
import sys

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.data import load_view, page_header


page_header("Comportamiento de la operación", "¿Qué señales distinguen las operaciones con mora?")
data = load_view("behavior")
if data.empty:
    st.info("No hay información madura para comparar.")
else:
    metric = st.selectbox(
        "Indicador",
        [
            "avg_recharge_amount_30d",
            "avg_main_recharges_30d",
            "avg_loan_amount_30d",
            "avg_loans_30d",
            "rate_without_recharge_30d",
        ],
    )
    summary = data.groupby("riesgo_mora", as_index=False)[metric].mean()
    summary["perfil"] = summary["riesgo_mora"].map({0: "Sin mora", 1: "Con mora"})
    figure = px.bar(summary, x="perfil", y=metric, color="perfil", text_auto=".3f")
    st.plotly_chart(figure, use_container_width=True)
