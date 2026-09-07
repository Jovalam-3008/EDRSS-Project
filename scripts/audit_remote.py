"""Auditoría final de Supabase para EDRSS V2."""

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import query_dataframe, test_connection  # noqa: E402
from src.pipeline import latest_successful_batch, layer_counts  # noqa: E402


def scalar(query: str) -> int:
    return int(query_dataframe(query).iloc[0, 0])


if __name__ == "__main__":
    batch_id = latest_successful_batch()
    active = query_dataframe(
        """
        select model_name, model_version, threshold
        from gold.active_model
        """
    )
    dashboard_rows = {
        name: scalar(f"select count(*) from api.{name}")
        for name in [
            "page_executive_summary",
            "page_risk_and_delinquency",
            "page_customer_behavior",
            "page_predictive_model",
            "page_collection_priority",
            "page_data_quality",
        ]
    }
    result = {
        "connection": test_connection(),
        "batch_id": batch_id,
        "layers": layer_counts(batch_id),
        "active_model": active.to_dict(orient="records"),
        "published_predictions": scalar("select count(*) from gold.active_predictions"),
        "dashboard_rows": dashboard_rows,
    }
    print(json.dumps(result, indent=2, default=str))

    assert result["layers"]["bronze"] == result["layers"]["silver"] == result["layers"]["gold"]
    assert result["layers"]["training"] + result["layers"]["scoring"] == result["layers"]["gold"]
    assert len(result["active_model"]) == 1
    assert result["published_predictions"] > 0
    assert all(rows > 0 for rows in dashboard_rows.values())
    print("EDRSS V2 REMOTE AUDIT: PASS")

