"""Ejecuta la ruta de datos completa y muestra sus cantidades finales."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import ingest_bronze, layer_counts, refresh_gold, refresh_silver  # noqa: E402


if __name__ == "__main__":
    ingestion = ingest_bronze()
    batch_id = str(ingestion["batch_id"])
    print("Bronze:", ingestion)
    refresh_silver(batch_id)
    print("Silver: SUCCESS")
    refresh_gold(batch_id)
    print("Gold:", layer_counts(batch_id))

