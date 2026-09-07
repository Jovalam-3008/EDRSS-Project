"""Configuración del proyecto sin almacenar secretos."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
_SESSION_PASSWORD: str | None = None


@dataclass(frozen=True)
class Settings:
    project_root: Path
    database_host: str
    database_port: int
    database_name: str
    database_user: str
    dataset_path: Path
    expected_md5: str
    environment: str


def load_project_config() -> dict:
    """Lee las reglas declarativas del proyecto."""
    path = PROJECT_ROOT / "config" / "project.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_settings() -> Settings:
    """Combina configuración versionada con variables locales no sensibles."""
    config = load_project_config()
    relative_dataset = os.getenv(
        "EDRSS_DATASET_PATH", config["data"]["dataset_path"]
    )
    dataset_path = Path(relative_dataset)
    if not dataset_path.is_absolute():
        dataset_path = PROJECT_ROOT / dataset_path

    return Settings(
        project_root=PROJECT_ROOT,
        database_host=os.getenv("SUPABASE_DB_HOST", ""),
        database_port=int(os.getenv("SUPABASE_DB_PORT", "6543")),
        database_name=os.getenv("SUPABASE_DB_NAME", "postgres"),
        database_user=os.getenv("SUPABASE_DB_USER", ""),
        dataset_path=dataset_path,
        expected_md5=os.getenv(
            "EDRSS_EXPECTED_MD5", config["data"]["expected_md5"]
        ),
        environment=os.getenv("EDRSS_ENVIRONMENT", "development"),
    )


def request_database_password(force: bool = False) -> str:
    """Solicita la contraseña de forma oculta y la conserva solo en memoria."""
    global _SESSION_PASSWORD
    if force or not _SESSION_PASSWORD:
        _SESSION_PASSWORD = getpass("Contraseña de Supabase: ")
    if not _SESSION_PASSWORD:
        raise RuntimeError("No se ingresó una contraseña de Supabase.")
    return _SESSION_PASSWORD


def set_database_password(password: str | None) -> None:
    """Guarda o limpia la contraseña únicamente en memoria durante la sesión."""
    global _SESSION_PASSWORD
    _SESSION_PASSWORD = password or None


def has_database_password() -> bool:
    """Indica si la sesión actual ya recibió una contraseña."""
    return bool(_SESSION_PASSWORD)


def md5_file(path: Path, block_size: int = 1024 * 1024) -> str:
    """Calcula la huella del archivo sin cargarlo completo en memoria."""
    digest = hashlib.md5()
    with path.open("rb") as source:
        while block := source.read(block_size):
            digest.update(block)
    return digest.hexdigest()
