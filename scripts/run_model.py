"""Entrena, evalúa y publica el modelo V2 desde los contratos Gold."""

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.modeling import publish_model, train_and_evaluate  # noqa: E402


if __name__ == "__main__":
    result = train_and_evaluate()
    print("Modelo seleccionado:", result["selected_model_name"])
    print("Métricas OOT:", json.dumps(result["oot_metrics"], indent=2))
    print("Capacidad OOT:")
    print(result["oot_capacity"].to_string(index=False))
    publication = publish_model(result)
    print("Publicación:", json.dumps(publication, indent=2))

