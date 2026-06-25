"""
Project Paths
"""

from pathlib import Path


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]

BACKEND_DIR = (
    PROJECT_ROOT / "backend"
)

DATASETS_DIR = (
    PROJECT_ROOT / "datasets"
)

MODELS_DIR = (
    PROJECT_ROOT / "models"
)

REPORTS_DIR = (
    PROJECT_ROOT / "reports"
)

LOGS_DIR = (
    PROJECT_ROOT / "logs"
)