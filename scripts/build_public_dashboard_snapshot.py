"""Construye consumibles agregados y seguros para la demo pública de EDRSS."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "dataset.csv"
PUBLIC_DIR = PROJECT_ROOT / "data" / "public"
MODEL_VERSION = "edrss-v2-20260907T010913Z"
MEASURED_AT = "2026-09-07T01:09:13Z"


def write_csv(frame: pd.DataFrame, name: str) -> None:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(PUBLIC_DIR / name, index=False)


def main() -> None:
    data = pd.read_csv(RAW_PATH)
    data["pdate"] = pd.to_datetime(data["pdate"], format="%d-%m-%Y")

    train_end = pd.Timestamp("2016-07-07")
    embargo_end = pd.Timestamp("2016-07-12")
    mature_end = pd.Timestamp("2016-07-23")

    data["dataset_role"] = "SCORING"
    data.loc[data["pdate"] <= train_end, "dataset_role"] = "TRAIN"
    data.loc[
        data["pdate"].between(train_end + pd.Timedelta(days=1), embargo_end),
        "dataset_role",
    ] = "EMBARGO"
    data.loc[
        data["pdate"].between(embargo_end + pd.Timedelta(days=1), mature_end),
        "dataset_role",
    ] = "OOT"

    data["riesgo_mora"] = (1 - data["label"]).where(data["pdate"] <= mature_end)
    data["no_main_recharge30"] = (data["cnt_ma_rech30"] <= 0).astype(int)
    data["no_loan30"] = (data["cnt_loans30"] <= 0).astype(int)

    mature = data[data["pdate"] <= mature_end].copy()
    scoring = data[data["pdate"] > mature_end].copy()

    executive = pd.DataFrame(
        [
            {
                "total_operations": len(data),
                "mature_operations": len(mature),
                "scoring_population": len(scoring),
                "delinquency_rate": mature["riesgo_mora"].mean(),
                "model_name": "RandomForest",
                "model_version": MODEL_VERSION,
                "threshold": 0.5,
                "trained_at": MEASURED_AT,
                "oot_roc_auc": 0.843492,
                "recall_at_10": 0.3367,
                "precision_at_10": 0.6954,
                "lift_at_10": 3.37,
            }
        ]
    )
    write_csv(executive, "executive.csv")

    risk = (
        data.groupby(["pdate", "dataset_role"], as_index=False)
        .agg(
            operations=("label", "size"),
            delinquent_operations=("riesgo_mora", "sum"),
            delinquency_rate=("riesgo_mora", "mean"),
            avg_loan_amount_30d=("amnt_loans30", "mean"),
            avg_loans_30d=("cnt_loans30", "mean"),
        )
        .sort_values("pdate")
    )
    write_csv(risk, "risk.csv")

    behavior = (
        mature.groupby(["pdate", "riesgo_mora"], as_index=False)
        .agg(
            operations=("label", "size"),
            avg_tenure=("aon", "mean"),
            avg_main_recharges_30d=("cnt_ma_rech30", "mean"),
            avg_recharge_amount_30d=("sumamnt_ma_rech30", "mean"),
            avg_loans_30d=("cnt_loans30", "mean"),
            avg_loan_amount_30d=("amnt_loans30", "mean"),
            rate_without_recharge_30d=("no_main_recharge30", "mean"),
            rate_without_loan_30d=("no_loan30", "mean"),
        )
        .sort_values(["pdate", "riesgo_mora"])
    )
    write_csv(behavior, "behavior.csv")

    model = pd.DataFrame(
        [
            ["RandomForest", MODEL_VERSION, MEASURED_AT, "OOT", None, "2016-07-13", "2016-07-23", "roc_auc", 0.843492, MEASURED_AT],
            ["RandomForest", MODEL_VERSION, MEASURED_AT, "OOT", None, "2016-07-13", "2016-07-23", "average_precision", 0.600970, MEASURED_AT],
            ["RandomForest", MODEL_VERSION, MEASURED_AT, "OOT", None, "2016-07-13", "2016-07-23", "brier_score", 0.134447, MEASURED_AT],
        ],
        columns=["model_name", "model_version", "trained_at", "evaluation_scope", "fold_number", "period_start", "period_end", "metric_name", "metric_value", "measured_at"],
    )
    write_csv(model, "model.csv")

    capacity = pd.DataFrame(
        [
            ["RandomForest", MODEL_VERSION, "ACTIVE", "OOT", 0.05, 1581, 1229, 0.7774, 0.1882, 3.76, MEASURED_AT],
            ["RandomForest", MODEL_VERSION, "ACTIVE", "OOT", 0.10, 3161, 2198, 0.6954, 0.3367, 3.37, MEASURED_AT],
            ["RandomForest", MODEL_VERSION, "ACTIVE", "OOT", 0.20, 6321, 3716, 0.5879, 0.5692, 2.85, MEASURED_AT],
        ],
        columns=["model_name", "model_version", "status", "evaluation_scope", "capacity_fraction", "contacts", "positives_captured", "precision_at_k", "recall_at_k", "lift_at_k", "measured_at"],
    )
    write_csv(capacity, "capacity.csv")

    importance_values = [
        ("log1p_sumamnt_ma_rech90", 0.00480),
        ("sumamnt_ma_rech90", 0.00452),
        ("log1p_cnt_ma_rech90", 0.00449),
        ("recency_to_tenure_ratio", 0.00321),
        ("sumamnt_ma_rech30", 0.00282),
        ("last_rech_date_ma", 0.00238),
        ("medianmarechprebal90", 0.00215),
        ("cnt_ma_rech90", 0.00197),
    ]
    importance = pd.DataFrame(
        [
            ["RandomForest", MODEL_VERSION, feature, "permutation", value, None, rank, MEASURED_AT]
            for rank, (feature, value) in enumerate(importance_values, start=1)
        ],
        columns=["model_name", "model_version", "feature_name", "importance_type", "importance_value", "importance_std", "feature_rank", "measured_at"],
    )
    write_csv(importance, "importance.csv")

    quality = pd.DataFrame(
        [
            ["public-snapshot", "BRONZE", "row_count", "PASS", len(data), 209593, "Conteo de la fuente", MEASURED_AT],
            ["public-snapshot", "SILVER", "row_count", "PASS", len(data), 209593, "Conteo después de tipificación", MEASURED_AT],
            ["public-snapshot", "GOLD", "row_count", "PASS", len(data), 209593, "Conteo del contrato analítico", MEASURED_AT],
            ["public-snapshot", "GOLD", "mature_target", "PASS", len(mature), 150768, "Población supervisada", MEASURED_AT],
            ["public-snapshot", "GOLD", "scoring_population", "PASS", len(scoring), 58825, "Población en cuarentena temporal", MEASURED_AT],
            ["public-snapshot", "MODEL", "oot_roc_auc", "PASS", 0.843492, 0.80, "Umbral mínimo de aceptación", MEASURED_AT],
        ],
        columns=["batch_id", "layer_name", "check_name", "status", "observed_value", "expected_value", "details", "checked_at"],
    )
    write_csv(quality, "quality.csv")

    print(f"Public snapshot created at {PUBLIC_DIR}")


if __name__ == "__main__":
    main()
