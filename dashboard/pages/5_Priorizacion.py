"""Hoja 5 — Cola operativa de cobranza."""

from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.data import load_view, page_header


page_header("Priorización de cobranza", "¿A quién debe contactar primero el equipo de cobranza?")
data = load_view("priority")
if data.empty:
    st.info("Aún no existen scores del modelo activo.")
else:
    bands = list(data["risk_band"].dropna().unique())
    selected = st.multiselect("Bandas de riesgo", bands, default=bands)
    maximum = int(data["priority_rank"].max())
    contacts = st.slider("Capacidad máxima de contactos", 100, maximum, min(5000, maximum), 100)
    queue = data[data["risk_band"].isin(selected)].nsmallest(contacts, "priority_rank")
    st.metric("Operaciones seleccionadas", f"{len(queue):,}")
    st.dataframe(queue, use_container_width=True, hide_index=True)
    st.download_button(
        "Descargar cola priorizada",
        queue.to_csv(index=False).encode("utf-8"),
        file_name="edrss_cola_priorizada.csv",
        mime="text/csv",
    )
