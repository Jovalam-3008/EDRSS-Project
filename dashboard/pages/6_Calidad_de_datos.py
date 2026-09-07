"""Hoja técnica — Evidencia de calidad y trazabilidad."""

from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.data import load_view, page_header


page_header("Calidad de datos", "¿Los consumibles cumplen los controles definidos?")
data = load_view("quality")
if data.empty:
    st.info("Aún no existen controles ejecutados.")
else:
    counts = data["status"].value_counts()
    columns = st.columns(3)
    for column, status in zip(columns, ["PASS", "WARN", "FAIL"]):
        column.metric(status, int(counts.get(status, 0)))
    st.dataframe(
        data.sort_values("checked_at", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
