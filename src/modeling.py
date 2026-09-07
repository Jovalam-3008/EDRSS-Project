"""Entrenamiento temporal y publicación productiva desde Gold."""

from __future__ import annotations

import json
import math
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from .settings import PROJECT_ROOT, load_project_config
from .database import connect, copy_query_dataframe, query_dataframe


GOVERNANCE_COLUMNS = {
    "operation_sk", "batch_id", "pdate", "riesgo_mora",
    "target_maturity_status", "dataset_role", "source_version",
    "silver_version", "feature_version", "published_at",
}


class QuantileClipper(BaseEstimator, TransformerMixin):
    def __init__(self, lower: float = 0.01, upper: float = 0.99):
        self.lower = lower
        self.upper = upper

    def fit(self, X, y=None):
        values = np.asarray(X, dtype=float)
        self.lower_bounds_ = np.nanquantile(values, self.lower, axis=0)
        self.upper_bounds_ = np.nanquantile(values, self.upper, axis=0)
        return self

    def transform(self, X):
        values = np.asarray(X, dtype=float)
        return np.clip(values, self.lower_bounds_, self.upper_bounds_)


def binary_metrics(y_true, probabilities, threshold: float = 0.5) -> dict[str, float]:
    values = np.asarray(probabilities)
    predictions = (values >= threshold).astype(int)
    return {
        "roc_auc": float(roc_auc_score(y_true, values)),
        "average_precision": float(average_precision_score(y_true, values)),
        "brier": float(brier_score_loss(y_true, values)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
    }


def capacity_metrics(y_true, probabilities, fractions=(0.05, 0.10, 0.20)) -> pd.DataFrame:
    target = np.asarray(y_true)
    scores = np.asarray(probabilities)
    order = np.argsort(-scores)
    prevalence = target.mean()
    total_positive = target.sum()
    rows = []
    for fraction in fractions:
        contacts = max(1, int(math.ceil(len(target) * fraction)))
        selected = order[:contacts]
        positives = int(target[selected].sum())
        precision = positives / contacts
        rows.append({
            "capacity_fraction": float(fraction),
            "contacts": contacts,
            "positives_captured": positives,
            "threshold": float(scores[selected].min()),
            "precision_at_k": float(precision),
            "recall_at_k": float(positives / total_positive),
            "lift_at_k": float(precision / prevalence),
        })
    return pd.DataFrame(rows)


def build_models(random_state: int = 42) -> dict[str, callable]:
    """Tres candidatos con roles distintos: baseline lineal y dos árboles."""
    linear = [
        ("clipper", QuantileClipper()),
        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
        ("scaler", RobustScaler()),
    ]
    tree = [("imputer", SimpleImputer(strategy="median", add_indicator=True))]
    return {
        "Logistic_weighted": lambda: Pipeline(linear + [("model", LogisticRegression(
            max_iter=100, solver="newton-cholesky", class_weight="balanced",
            random_state=random_state,
        ))]),
        "RandomForest": lambda: Pipeline(tree + [("model", RandomForestClassifier(
            n_estimators=140, max_depth=14, min_samples_leaf=30,
            max_features="sqrt", class_weight="balanced_subsample",
            n_jobs=-1, random_state=random_state,
        ))]),
        "HGB_balanced": lambda: Pipeline(tree + [("model", HistGradientBoostingClassifier(
            learning_rate=0.08, max_iter=120, max_leaf_nodes=31,
            min_samples_leaf=40, l2_regularization=0.5,
            class_weight="balanced", early_stopping=False,
            random_state=random_state,
        ))]),
    }


def load_gold_training() -> tuple[pd.DataFrame, list[str]]:
    frame = copy_query_dataframe(
        "select * from gold.ml_training order by pdate, operation_sk",
        parse_dates=["pdate", "published_at"],
    )
    features = [column for column in frame.columns if column not in GOVERNANCE_COLUMNS]
    if len(features) != 58:
        raise RuntimeError(f"Contrato Gold inválido: {len(features)} features; se esperaban 58.")
    return frame, features


def load_gold_scoring(features: list[str]) -> pd.DataFrame:
    columns = ", ".join(["operation_sk", "batch_id", "pdate", *features])
    return copy_query_dataframe(
        f"select {columns} from gold.ml_scoring order by pdate, operation_sk",
        parse_dates=["pdate"],
    )


def _temporal_folds(frame: pd.DataFrame, config: dict):
    for fold in config["temporal_split"]["cv_folds"]:
        train_mask = frame["pdate"].between(fold["train_start"], fold["train_end"])
        valid_mask = frame["pdate"].between(fold["validation_start"], fold["validation_end"])
        yield fold["fold"], frame.index[train_mask], frame.index[valid_mask]


def train_and_evaluate() -> dict:
    config = load_project_config()
    random_state = config["model"]["random_state"]
    fractions = config["model"]["capacity_levels"]

    frame, features = load_gold_training()
    X = frame[features].replace([np.inf, -np.inf], np.nan)
    y = frame["riesgo_mora"].astype(int)
    models = build_models(random_state)

    fold_rows: list[dict] = []
    prediction_rows: list[dict] = []
    started = time.perf_counter()
    for model_name, factory in models.items():
        for fold_number, train_index, valid_index in _temporal_folds(frame, config):
            model = factory()
            fold_started = time.perf_counter()
            model.fit(X.loc[train_index], y.loc[train_index])
            scores = model.predict_proba(X.loc[valid_index])[:, 1]
            metrics = binary_metrics(y.loc[valid_index], scores)
            fold_rows.append({
                "model_name": model_name,
                "fold_number": fold_number,
                "train_rows": len(train_index),
                "validation_rows": len(valid_index),
                "validation_prevalence": float(y.loc[valid_index].mean()),
                "seconds": time.perf_counter() - fold_started,
                **metrics,
            })
            prediction_rows.extend({
                "model_name": model_name,
                "fold_number": fold_number,
                "frame_index": int(index),
                "score": float(score),
            } for index, score in zip(valid_index, scores))

    fold_metrics = pd.DataFrame(fold_rows)
    cv_summary = fold_metrics.groupby("model_name").agg(
        roc_auc_mean=("roc_auc", "mean"),
        roc_auc_std=("roc_auc", "std"),
        roc_auc_worst=("roc_auc", "min"),
        pr_auc_mean=("average_precision", "mean"),
        brier_mean=("brier", "mean"),
        seconds=("seconds", "sum"),
    ).reset_index()

    all_oof = pd.DataFrame(prediction_rows)
    capacity_10 = []
    for model_name, group in all_oof.groupby("model_name"):
        indices = group["frame_index"].to_numpy()
        table = capacity_metrics(y.loc[indices], group["score"], fractions)
        row = table.loc[table["capacity_fraction"].eq(0.10)].iloc[0]
        capacity_10.append({"model_name": model_name, **row.to_dict()})
    cv_summary = cv_summary.merge(pd.DataFrame(capacity_10), on="model_name")

    best_auc = cv_summary["roc_auc_mean"].max()
    tolerance = config["model"]["auc_tolerance"]
    finalists = cv_summary.loc[cv_summary["roc_auc_mean"] >= best_auc - tolerance]
    finalists = finalists.sort_values(
        ["roc_auc_worst", "recall_at_k", "pr_auc_mean", "roc_auc_std"],
        ascending=[False, False, False, True],
    )
    selected_name = finalists.iloc[0]["model_name"]
    selected_oof_raw = all_oof.loc[all_oof["model_name"].eq(selected_name)].copy()
    oof_index = selected_oof_raw["frame_index"].to_numpy()
    selected_oof = frame.loc[oof_index, ["operation_sk", "batch_id", "pdate", "riesgo_mora"]].copy()
    selected_oof["fold_number"] = selected_oof_raw["fold_number"].to_numpy()
    selected_oof["score"] = selected_oof_raw["score"].to_numpy()
    oof_metrics = binary_metrics(selected_oof["riesgo_mora"], selected_oof["score"])
    oof_capacity = capacity_metrics(selected_oof["riesgo_mora"], selected_oof["score"], fractions)
    frozen_threshold = float(oof_capacity.loc[oof_capacity["capacity_fraction"].eq(0.10), "threshold"].iloc[0])

    train_mask = frame["dataset_role"].eq("TRAIN")
    oot_mask = frame["dataset_role"].eq("OOT")
    final_pipeline = models[selected_name]()
    final_pipeline.fit(X.loc[train_mask], y.loc[train_mask])
    oot_scores = final_pipeline.predict_proba(X.loc[oot_mask])[:, 1]
    oot = frame.loc[oot_mask, ["operation_sk", "batch_id", "pdate", "riesgo_mora"]].copy()
    oot["score"] = oot_scores
    oot_metrics = binary_metrics(oot["riesgo_mora"], oot["score"], frozen_threshold)
    oot_capacity = capacity_metrics(oot["riesgo_mora"], oot["score"], fractions)

    scoring = load_gold_scoring(features)
    scoring_X = scoring[features].replace([np.inf, -np.inf], np.nan)
    scoring["score"] = final_pipeline.predict_proba(scoring_X)[:, 1]

    sample_index = X.loc[oot_mask].sample(
        n=min(10_000, int(oot_mask.sum())), random_state=random_state
    ).index
    importance = permutation_importance(
        final_pipeline, X.loc[sample_index], y.loc[sample_index],
        scoring="roc_auc", n_repeats=3, random_state=random_state, n_jobs=1,
    )
    importance_table = pd.DataFrame({
        "feature_name": features,
        "importance_value": importance.importances_mean,
        "importance_std": importance.importances_std,
    }).sort_values("importance_value", ascending=False).reset_index(drop=True)
    importance_table["feature_rank"] = np.arange(1, len(importance_table) + 1)

    return {
        "frame": frame,
        "features": features,
        "fold_metrics": fold_metrics,
        "cv_summary": cv_summary.sort_values("roc_auc_mean", ascending=False),
        "selected_model_name": selected_name,
        "selected_oof": selected_oof,
        "oof_metrics": oof_metrics,
        "oof_capacity": oof_capacity,
        "frozen_threshold": frozen_threshold,
        "oot": oot,
        "oot_metrics": oot_metrics,
        "oot_capacity": oot_capacity,
        "scoring": scoring,
        "importance": importance_table,
        "pipeline": final_pipeline,
        "elapsed_seconds": time.perf_counter() - started,
    }


def _add_priority_fields(frame: pd.DataFrame, threshold: float, scope: str) -> pd.DataFrame:
    result = frame.copy().sort_values("score", ascending=False).reset_index(drop=True)
    result["priority_rank"] = np.arange(1, len(result) + 1)
    fraction = result["priority_rank"] / len(result)
    result["risk_band"] = np.select(
        [fraction <= 0.05, fraction <= 0.10, fraction <= 0.20],
        ["CRITICAL", "HIGH", "MEDIUM"], default="LOW",
    )
    result["predicted_label"] = (result["score"] >= threshold).astype(int)
    result["dataset_role"] = scope
    if "riesgo_mora" not in result:
        result["riesgo_mora"] = np.nan
    return result


def publish_model(result: dict) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    model_run_id = str(uuid.uuid4())
    model_version = f"edrss-v2-{now:%Y%m%dT%H%M%SZ}"
    model_name = result["selected_model_name"]
    batch_id = str(result["frame"]["batch_id"].iloc[0])
    threshold = result["frozen_threshold"]

    output_dir = PROJECT_ROOT / "models"
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / f"{model_name}_{model_version}.joblib"
    joblib.dump(result["pipeline"], artifact_path)

    oof = _add_priority_fields(result["selected_oof"], threshold, "OOF")
    oot = _add_priority_fields(result["oot"], threshold, "OOT")
    scoring = _add_priority_fields(result["scoring"], threshold, "SCORING")
    predictions = pd.concat([oof, oot, scoring], ignore_index=True)

    parameters = {
        "random_state": 42,
        "features": len(result["features"]),
        "selection_rule": "AUC tolerance then worst-fold, recall@10, PR-AUC, stability",
        "capacity_policy": "rank-based",
    }

    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            insert into gold.model_registry
              (model_run_id, model_name, model_version, feature_version,
               training_batch_id, status, threshold, artifact_uri, parameters, notes)
            values (%s, %s, %s, 'features-v2.0.0', %s, 'CANDIDATE', %s, %s, %s, %s)
            """,
            (model_run_id, model_name, model_version, batch_id, threshold,
             str(artifact_path), json.dumps(parameters),
             "EDRSS V2: entrenado solo desde gold.ml_training; política por ranking."),
        )

        selected_fold = result["fold_metrics"].loc[
            result["fold_metrics"]["model_name"].eq(model_name)
        ]
        metric_rows = []
        for row in selected_fold.itertuples():
            for metric in ("roc_auc", "average_precision", "brier", "recall", "precision", "f1"):
                metric_rows.append((
                    model_run_id, "CV_FOLD", int(row.fold_number), None, None,
                    metric, float(getattr(row, metric)),
                ))
        for scope, metrics in (("OOF", result["oof_metrics"]), ("OOT", result["oot_metrics"])):
            for metric, value in metrics.items():
                metric_rows.append((model_run_id, scope, None, None, None, metric, float(value)))
        cursor.executemany(
            """
            insert into gold.model_metrics
              (model_run_id, evaluation_scope, fold_number, period_start,
               period_end, metric_name, metric_value)
            values (%s, %s, %s, %s, %s, %s, %s)
            """,
            metric_rows,
        )

        capacity_rows = []
        for scope, table in (("OOF", result["oof_capacity"]), ("OOT", result["oot_capacity"])):
            for row in table.itertuples():
                capacity_rows.append((
                    model_run_id, scope, float(row.capacity_fraction), int(row.contacts),
                    int(row.positives_captured), float(row.precision_at_k),
                    float(row.recall_at_k), float(row.lift_at_k),
                ))
        cursor.executemany(
            """
            insert into gold.model_capacity_metrics
              (model_run_id, evaluation_scope, capacity_fraction, contacts,
               positives_captured, precision_at_k, recall_at_k, lift_at_k)
            values (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            capacity_rows,
        )

        cursor.executemany(
            """
            insert into gold.model_feature_importance
              (model_run_id, feature_name, importance_type, importance_value,
               importance_std, feature_rank)
            values (%s, %s, 'permutation_oot', %s, %s, %s)
            """,
            [
                (model_run_id, row.feature_name, float(row.importance_value),
                 float(row.importance_std), int(row.feature_rank))
                for row in result["importance"].itertuples()
            ],
        )

        cursor.execute(
            """
            create temporary table prediction_stage (
                operation_sk text, batch_id uuid, pdate date, dataset_role text,
                riesgo_mora smallint, risk_score double precision,
                predicted_label smallint, risk_band text, priority_rank bigint
            ) on commit drop
            """
        )
        with cursor.copy(
            """
            copy prediction_stage
              (operation_sk, batch_id, pdate, dataset_role, riesgo_mora,
               risk_score, predicted_label, risk_band, priority_rank)
            from stdin
            """
        ) as copy:
            for row in predictions.itertuples(index=False):
                target = None if pd.isna(row.riesgo_mora) else int(row.riesgo_mora)
                copy.write_row((
                    row.operation_sk, row.batch_id, row.pdate.date(), row.dataset_role,
                    target, float(row.score), int(row.predicted_label),
                    row.risk_band, int(row.priority_rank),
                ))
        cursor.execute(
            """
            insert into gold.model_predictions
              (model_run_id, operation_sk, batch_id, pdate, dataset_role,
               riesgo_mora, risk_score, predicted_label, risk_band, priority_rank)
            select %s, operation_sk, batch_id, pdate, dataset_role,
                   riesgo_mora, risk_score, predicted_label, risk_band, priority_rank
            from prediction_stage
            """,
            (model_run_id,),
        )
        cursor.execute("update gold.model_registry set status = 'RETIRED' where status = 'ACTIVE'")
        cursor.execute(
            "update gold.model_registry set status = 'ACTIVE' where model_run_id = %s",
            (model_run_id,),
        )

    summary = {
        "model_run_id": model_run_id,
        "model_name": model_name,
        "model_version": model_version,
        "artifact_path": str(artifact_path),
        "predictions_published": str(len(predictions)),
    }
    (output_dir / "latest_model_run.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


def published_model_summary() -> dict[str, pd.DataFrame]:
    return {
        "registry": query_dataframe(
            "select * from gold.model_registry where status = 'ACTIVE'"
        ),
        "metrics": query_dataframe(
            "select * from api.dashboard_model_health where status = 'ACTIVE'"
        ),
        "capacity": query_dataframe(
            "select * from api.dashboard_capacity_story"
        ),
    }
