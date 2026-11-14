"""
SphereX - Astronomical data analysis for detecting candidate sources
through multi-epoch comparison.
"""

__version__ = "1.0.0"

from .config import (
    PROJECT_DIR,
    RAW_DIR,
    PROCESSED_DIR,
    RESULTS_DIR,
    SCRIPTS_DIR,
    DATA_DIR,
    project_path,
    get_data_path,
    get_result_path,
    get_script_path,
)

__all__ = [
    "PROJECT_DIR",
    "RAW_DIR", 
    "PROCESSED_DIR",
    "RESULTS_DIR",
    "SCRIPTS_DIR",
    "DATA_DIR",
    "project_path",
    "get_data_path",
    "get_result_path",
    "get_script_path",
]
