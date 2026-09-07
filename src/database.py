"""Acceso centralizado a PostgreSQL/Supabase."""

from __future__ import annotations

from contextlib import contextmanager
from io import BytesIO
from pathlib import Path

import pandas as pd
import psycopg

from .settings import PROJECT_ROOT, load_settings, request_database_password


@contextmanager
def connect():
    """Abre una conexión cifrada y confirma o revierte la transacción al salir."""
    settings = load_settings()
    connection = psycopg.connect(
        host=settings.database_host,
        port=settings.database_port,
        dbname=settings.database_name,
        user=settings.database_user,
        password=request_database_password(),
        sslmode="require",
        connect_timeout=20,
        prepare_threshold=None,
    )
    with connection:
        yield connection


def test_connection() -> dict[str, str]:
    """Devuelve evidencia mínima de que la conexión funciona."""
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "select current_database(), current_user, current_timestamp"
        )
        database, user, checked_at = cursor.fetchone()
    return {
        "database": database,
        "user": user,
        "checked_at": checked_at.isoformat(),
    }


def query_dataframe(query: str, params: tuple | None = None) -> pd.DataFrame:
    """Ejecuta una consulta de lectura y devuelve un DataFrame."""
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [column.name for column in cursor.description]
        rows = cursor.fetchall()
    return pd.DataFrame(rows, columns=columns)


def copy_query_dataframe(
    query: str, parse_dates: list[str] | None = None
) -> pd.DataFrame:
    """Descarga consultas grandes mediante COPY para reducir tiempo y memoria."""
    buffer = BytesIO()
    with connect() as connection, connection.cursor() as cursor:
        with cursor.copy(
            f"copy ({query}) to stdout with (format csv, header true)"
        ) as copy:
            while chunk := copy.read():
                buffer.write(chunk)
    buffer.seek(0)
    return pd.read_csv(buffer, parse_dates=parse_dates)


def execute(query: str, params: tuple | None = None) -> None:
    """Ejecuta una sentencia parametrizada dentro de una transacción."""
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(query, params)


def ordered_sql_files(sql_root: Path | None = None) -> list[Path]:
    """Obtiene los scripts en el mismo orden visible en sus nombres."""
    root = sql_root or PROJECT_ROOT / "sql"
    return sorted(root.glob("[0-9][0-9]_*/*.sql"))


def deploy_sql() -> list[str]:
    """Despliega todos los scripts SQL, uno por transacción y en orden."""
    deployed: list[str] = []
    for path in ordered_sql_files():
        statement = path.read_text(encoding="utf-8-sig")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(statement, prepare=False)
        deployed.append(path.relative_to(PROJECT_ROOT).as_posix())
    return deployed


def inventory() -> pd.DataFrame:
    """Lista tablas y vistas de las capas del proyecto."""
    return query_dataframe(
        """
        select table_schema, table_name, table_type
        from information_schema.tables
        where table_schema in ('bronze', 'silver', 'gold', 'api')
        order by table_schema, table_name
        """
    )
