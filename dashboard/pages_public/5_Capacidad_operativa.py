"""Historia pública de capacidad sin exponer la cola operativa."""

from pathlib import Path
import sys

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.data import load_view, page_header


page_header(
    "Capacidad de cobranza",
    "¿Cuánto riesgo puede capturar el equipo según su capacidad de contacto?",
)
capacity = load_view("capacity").sort_values("capacity_fraction")
executive = load_view("executive").iloc[0]

selected_capacity = st.select_slider(
    "Capacidad de contacto",
    options=capacity["capacity_fraction"].tolist(),
    value=0.10,
    format_func=lambda value: f"{value:.0%}",
)
row = capacity.loc[capacity["capacity_fraction"] == selected_capacity].iloc[0]

cards = st.columns(5)
cards[0].metric("Operaciones para scoring", f"{int(executive['scoring_population']):,}")
cards[1].metric("Contactos evaluados", f"{int(row['contacts']):,}")
cards[2].metric("Mora capturada", f"{row['recall_at_k']:.1%}")
cards[3].metric("Precisión", f"{row['precision_at_k']:.1%}")
cards[4].metric("Lift", f"{row['lift_at_k']:.2f}x")

chart_data = capacity.melt(
    id_vars=["capacity_fraction"],
    value_vars=["recall_at_k", "precision_at_k"],
    var_name="Indicador",
    value_name="Valor",
)
chart_data["Indicador"] = chart_data["Indicador"].map(
    {"recall_at_k": "Riesgo capturado", "precision_at_k": "Precisión"}
)
figure = px.line(
    chart_data,
    x="capacity_fraction",
    y="Valor",
    color="Indicador",
    markers=True,
    labels={"capacity_fraction": "Capacidad de contacto"},
)
figure.update_xaxes(tickformat=".0%")
figure.update_yaxes(tickformat=".0%")
st.plotly_chart(figure, use_container_width=True)

st.info(
    "Esta página publica únicamente métricas agregadas. La cola detallada permanece en el entorno privado."
)
