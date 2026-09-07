"""Punto de entrada del tablero multipágina EDRSS V2."""

from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import test_connection  # noqa: E402
from src.settings import (  # noqa: E402
    has_database_password,
    set_database_password,
)

st.set_page_config(
    page_title="EDRSS V2",
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
    st.Page("pages/5_Priorizacion.py", title="Priorización", icon="🎯"),
    st.Page("pages/6_Calidad_de_datos.py", title="Calidad de datos", icon="✅"),
]

navigation = st.navigation(pages)
st.sidebar.caption("Early Delinquency Risk Scoring System · V2")

if not has_database_password():
    st.sidebar.subheader("Conexión a Supabase")
    with st.sidebar.form("supabase_connection", clear_on_submit=True):
        password = st.text_input(
            "Contraseña",
            type="password",
            help="La contraseña permanece solo en memoria durante esta sesión.",
        )
        connect_button = st.form_submit_button("Conectar", use_container_width=True)

    if connect_button:
        if not password:
            st.sidebar.warning("Ingrese la contraseña para continuar.")
        else:
            set_database_password(password)
            try:
                test_connection()
            except Exception:
                set_database_password(None)
                st.sidebar.error("Supabase rechazó la conexión. Verifique la contraseña.")
            else:
                st.rerun()

    st.info("Ingrese la contraseña de Supabase en el panel lateral para cargar el dashboard.")
    st.stop()

navigation.run()
