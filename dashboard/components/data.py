"""Consultas permitidas para el dashboard: solo vistas API derivadas de Gold."""

from pathlib import Path
import os
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import query_dataframe  # noqa: E402


ALLOWED_VIEWS = {
    "executive": "api.page_executive_summary",
    "risk": "api.page_risk_and_delinquency",
    "behavior": "api.page_customer_behavior",
    "model": "api.page_predictive_model",
    "importance": "api.dashboard_feature_importance",
    "capacity": "api.dashboard_capacity_story",
    "priority": "api.page_collection_priority",
    "quality": "api.page_data_quality",
}

PUBLIC_FILES = {
    "executive": "executive.csv",
    "risk": "risk.csv",
    "behavior": "behavior.csv",
    "model": "model.csv",
    "importance": "importance.csv",
    "capacity": "capacity.csv",
    "quality": "quality.csv",
}


def is_public_mode() -> bool:
    """Identifica la demo pública, que trabaja solo con datos agregados."""
    return os.getenv("EDRSS_PUBLIC_MODE", "0") == "1"


@st.cache_data(ttl=300, show_spinner=False)
def load_view(name: str):
    """Carga una vista aprobada; rechaza nombres SQL recibidos desde la interfaz."""
    if is_public_mode():
        if name not in PUBLIC_FILES:
            raise ValueError(f"Consumible no disponible en la demo pública: {name}")
        return pd.read_csv(PROJECT_ROOT / "data" / "public" / PUBLIC_FILES[name])
    if name not in ALLOWED_VIEWS:
        raise ValueError(f"Consumible no permitido: {name}")
    return query_dataframe(f"select * from {ALLOWED_VIEWS[name]}")


def page_header(title: str, question: str) -> None:
    st.title(title)
    st.caption(question)
