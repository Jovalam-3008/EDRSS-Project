"""Valida la estructura local sin conectarse a servicios externos."""

from pathlib import Path
import json
import sys

import nbformat

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import ordered_sql_files  # noqa: E402
from src.pipeline import validate_source  # noqa: E402


EXPECTED_NOTEBOOKS = [
    "00_Configuracion_y_conexion.ipynb",
    "01_Ingesta_Bronze.ipynb",
    "02_Limpieza_Silver.ipynb",
    "03_Construccion_Gold.ipynb",
    "04_EDA_y_KPIs_de_negocio.ipynb",
    "05_Modelo_predictivo.ipynb",
    "06_Publicacion_de_scoring.ipynb",
    "07_Validacion_del_dashboard.ipynb",
]


def main() -> None:
    missing = [
        name for name in EXPECTED_NOTEBOOKS
        if not (PROJECT_ROOT / "notebooks" / name).exists()
    ]
    if missing:
        raise RuntimeError(f"Faltan notebooks: {missing}")
    for name in EXPECTED_NOTEBOOKS:
        path = PROJECT_ROOT / "notebooks" / name
        book = nbformat.read(path, as_version=4)
        for cell_number, cell in enumerate(book.cells, start=1):
            if cell.cell_type == "code":
                compile(cell.source, f"{name}:cell-{cell_number}", "exec")
    sql_files = ordered_sql_files()
    if len(sql_files) != 9:
        raise RuntimeError(f"Se esperaban 9 SQL y se encontraron {len(sql_files)}")
    source = validate_source()
    print("EDRSS V2: estructura válida")
    print(json.dumps({
        "sql_files": len(sql_files),
        "notebooks": len(EXPECTED_NOTEBOOKS),
        **source,
    }, indent=2))


if __name__ == "__main__":
    main()
