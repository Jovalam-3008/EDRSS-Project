"""Hoja 2 — Evolución y concentración de la mora."""

from pathlib import Path
import sys

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.data import load_view, page_header


page_header("Riesgo y mora", "¿Cómo evoluciona la mora y en qué periodo se concentra?")
data = load_view("risk")
if data.empty:
    st.info("No hay información Gold disponible.")
else:
    data["pdate"] = data["pdate"].astype(str)
    roles = sorted(data["dataset_role"].dropna().unique())
    selected = st.multiselect("Rol temporal", roles, default=roles)
    filtered = data[data["dataset_role"].isin(selected)]
    figure = px.line(
        filtered,
        x="pdate",
        y="delinquency_rate",
        color="dataset_role",
        markers=True,
        labels={"pdate": "Fecha", "delinquency_rate": "Tasa de mora"},
    )
    figure.update_yaxes(tickformat=".0%")
    st.plotly_chart(figure, use_container_width=True)
