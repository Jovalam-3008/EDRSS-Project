"""Ingesta y promoción secuencial Bronze → Silver → Gold."""

from __future__ import annotations

import csv
import uuid
from pathlib import Path

from psycopg import sql

from .database import connect
from .settings import load_settings, md5_file


SOURCE_COLUMNS = [
    "label", "aon", "daily_decr30", "daily_decr90", "rental30", "rental90",
    "last_rech_date_ma", "last_rech_date_da", "last_rech_amt_ma",
    "cnt_ma_rech30", "fr_ma_rech30", "sumamnt_ma_rech30",
    "medianamnt_ma_rech30", "medianmarechprebal30", "cnt_ma_rech90",
    "fr_ma_rech90", "sumamnt_ma_rech90", "medianamnt_ma_rech90",
    "medianmarechprebal90", "cnt_da_rech30", "fr_da_rech30",
    "cnt_da_rech90", "fr_da_rech90", "cnt_loans30", "amnt_loans30",
    "maxamnt_loans30", "medianamnt_loans30", "cnt_loans90",
    "amnt_loans90", "maxamnt_loans90", "medianamnt_loans90",
    "payback30", "payback90", "pcircle", "pdate",
]


def validate_source(path: Path | None = None) -> dict[str, object]:
    """Comprueba existencia, columnas y huella antes de cargar."""
    settings = load_settings()
    source = Path(path or settings.dataset_path).resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    with source.open("r", encoding="utf-8-sig", newline="") as file:
        header = next(csv.reader(file))
    if header != SOURCE_COLUMNS:
        raise ValueError("El orden o nombre de las columnas no cumple el contrato.")
    file_hash = md5_file(source)
    if settings.expected_md5 and file_hash != settings.expected_md5:
        raise ValueError("La huella MD5 no coincide con la fuente aprobada.")
    return {"path": str(source), "columns": len(header), "md5": file_hash}


def latest_successful_batch() -> str | None:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            select batch_id::text
            from bronze.ingestion_batch
            where status = 'SUCCESS'
            order by completed_at desc nulls last
            limit 1
            """
        )
        row = cursor.fetchone()
    return row[0] if row else None


def ingest_bronze(path: Path | None = None) -> dict[str, object]:
    """Carga el CSV como texto; si la misma fuente ya existe, reutiliza su lote."""
    settings = load_settings()
    source = Path(path or settings.dataset_path).resolve()
    source_info = validate_source(source)
    file_hash = str(source_info["md5"])

    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            select batch_id::text, loaded_row_count
            from bronze.ingestion_batch
            where source_file_hash = %s and status = 'SUCCESS'
            order by completed_at desc limit 1
            """,
            (file_hash,),
        )
        existing = cursor.fetchone()
    if existing:
        return {"batch_id": existing[0], "rows": existing[1], "status": "REUSED"}

    batch_id = str(uuid.uuid4())
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            insert into bronze.ingestion_batch
                (batch_id, source_file_name, source_file_hash, status)
            values (%s, %s, %s, 'RUNNING')
            """,
            (batch_id, source.name, file_hash),
        )

    try:
        with connect() as connection, connection.cursor() as cursor:
            definitions = sql.SQL(", ").join(
                sql.SQL("{} text").format(sql.Identifier(column))
                for column in SOURCE_COLUMNS
            )
            cursor.execute(
                sql.SQL(
                    "create temporary table stage_source ("
                    "source_row_number bigint generated always as identity, {}) "
                    "on commit drop"
                ).format(definitions)
            )
            columns = sql.SQL(", ").join(map(sql.Identifier, SOURCE_COLUMNS))
            copy_command = sql.SQL(
                "copy stage_source ({}) from stdin with (format csv, header true)"
            ).format(columns)
            with source.open("r", encoding="utf-8-sig", newline="") as file:
                with cursor.copy(copy_command) as copy:
                    while chunk := file.read(1024 * 1024):
                        copy.write(chunk)
            cursor.execute(
                sql.SQL(
                    "insert into bronze.telecom_raw "
                    "(batch_id, source_row_number, source_file_name, source_file_hash, {}) "
                    "select %s, source_row_number, %s, %s, {} from stage_source"
                ).format(columns, columns),
                (batch_id, source.name, file_hash),
            )
            loaded_rows = cursor.rowcount
            cursor.execute(
                """
                update bronze.ingestion_batch
                set source_row_count = %s, loaded_row_count = %s,
                    rejected_row_count = 0, status = 'SUCCESS',
                    completed_at = current_timestamp
                where batch_id = %s
                """,
                (loaded_rows, loaded_rows, batch_id),
            )
    except Exception as error:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                update bronze.ingestion_batch
                set status = 'FAILED', completed_at = current_timestamp,
                    error_message = %s
                where batch_id = %s
                """,
                (str(error)[:2000], batch_id),
            )
        raise
    return {"batch_id": batch_id, "rows": loaded_rows, "status": "SUCCESS"}


def refresh_silver(batch_id: str | None = None) -> str:
    """Ejecuta limpieza y, después, creación de features Silver."""
    selected = batch_id or latest_successful_batch()
    if not selected:
        raise RuntimeError("No existe un lote Bronze exitoso.")
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("set local statement_timeout = '10min'")
        cursor.execute("call silver.refresh_telecom_operations(%s)", (selected,))
        cursor.execute("call silver.refresh_behavior_features(%s)", (selected,))
    return selected


def refresh_gold(batch_id: str | None = None) -> str:
    """Publica contratos de ML y KPIs a partir de Silver."""
    selected = batch_id or latest_successful_batch()
    if not selected:
        raise RuntimeError("No existe un lote Bronze exitoso.")
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("set local statement_timeout = '10min'")
        cursor.execute("call gold.refresh_ml_features(%s)", (selected,))
        cursor.execute("call gold.refresh_executive_kpis(%s)", (selected,))
    return selected


def layer_counts(batch_id: str | None = None) -> dict[str, int]:
    """Compara cantidades para una validación rápida del pipeline."""
    selected = batch_id or latest_successful_batch()
    if not selected:
        return {}
    statements = {
        "bronze": "select count(*) from bronze.telecom_raw where batch_id = %s",
        "silver": "select count(*) from silver.telecom_operations where batch_id = %s",
        "gold": "select count(*) from gold.ml_features where batch_id = %s",
        "training": "select count(*) from gold.ml_training where batch_id = %s",
        "scoring": "select count(*) from gold.ml_scoring where batch_id = %s",
    }
    counts: dict[str, int] = {}
    with connect() as connection, connection.cursor() as cursor:
        for name, statement in statements.items():
            cursor.execute(statement, (selected,))
            counts[name] = cursor.fetchone()[0]
    return counts
