"""Hoja 1 — Estado general y decisión principal."""

from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.data import load_view, page_header


page_header("Resumen ejecutivo", "¿Cuál es la situación y cuánto riesgo puede capturar cobranza?")
data = load_view("executive")

if data.empty:
    st.info("Aún no existe un modelo activo. Ejecute los notebooks en orden.")
else:
    row = data.iloc[0]
    cards = st.columns(5)
    cards[0].metric("Operaciones", f"{int(row['total_operations']):,}")
    cards[1].metric("Mora observada", f"{row['delinquency_rate']:.1%}")
    cards[2].metric("ROC-AUC OOT", f"{row['oot_roc_auc']:.3f}")
    cards[3].metric("Captura al 10%", f"{row['recall_at_10']:.1%}")
    cards[4].metric("Lift al 10%", f"{row['lift_at_10']:.2f}x")
    st.subheader("Lectura ejecutiva")
    st.write(
        f"El modelo activo **{row['model_name']}** prioriza la gestión temprana. "
        "La capacidad al 10% permite concentrar el contacto en operaciones con mayor riesgo."
    )
