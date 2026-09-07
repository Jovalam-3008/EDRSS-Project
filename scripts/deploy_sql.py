"""Despliega los SQL de EDRSS V2 en el orden de sus carpetas y nombres."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import deploy_sql, test_connection  # noqa: E402


if __name__ == "__main__":
    print("Conexión:", test_connection())
    for sql_file in deploy_sql():
        print("OK", sql_file)

