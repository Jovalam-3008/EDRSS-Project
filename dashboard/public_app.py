"""Entrada pública de EDRSS V2 con consumibles agregados y sin credenciales."""

import os
from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ["EDRSS_PUBLIC_MODE"] = "1"

st.set_page_config(
    page_title="EDRSS V2 · Demo pública",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {background: #111827;}
    [data-testid="stSidebar"] * {color: #f8fafc;}
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px;
        box-shadow: 0 3px 12px rgba(15, 23, 42, 0.05);
    }
    h1, h2, h3 {color: #0f172a;}
    </style>
    """,
    unsafe_allow_html=True,
)

pages = [
    st.Page("pages/1_Resumen_ejecutivo.py", title="Resumen ejecutivo", icon="🏠"),
    st.Page("pages/2_Riesgo_y_mora.py", title="Riesgo y mora", icon="📈"),
    st.Page("pages/3_Comportamiento.py", title="Comportamiento", icon="👥"),
    st.Page("pages/4_Modelo_predictivo.py", title="Modelo predictivo", icon="🧠"),
    st.Page("pages_public/5_Capacidad_operativa.py", title="Capacidad de cobranza", icon="🎯"),
    st.Page("pages/6_Calidad_de_datos.py", title="Calidad de datos", icon="✅"),
]

navigation = st.navigation(pages)
st.sidebar.caption("EDRSS V2 · Demo pública con datos agregados")
st.sidebar.info(
    "La versión pública no contiene la base original, credenciales ni operaciones individuales."
)
navigation.run()
