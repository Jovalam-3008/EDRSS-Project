"""Genera únicamente las figuras analíticas que utiliza el informe Word."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_report_v2 import create_figures  # noqa: E402


if __name__ == "__main__":
    for name, path in create_figures().items():
        print(name, path)

