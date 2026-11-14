"""
Central path management for the SphereX project.
Provides dynamic path resolution for all data, results, and script files.
"""

import os
from pathlib import Path
from typing import Union

from dotenv import load_dotenv

# Project root directory (SphereX/)
PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env", override=False)


def _configured_path(variable: str, default: Path) -> Path:
    value = os.getenv(variable)
    if not value:
        return default
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_DIR / path


def _configured_port() -> int:
    value = os.getenv("PORT", "8000")
    try:
        port = int(value)
    except ValueError as error:
        raise ValueError("PORT must be an integer between 1 and 65535.") from error
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be an integer between 1 and 65535.")
    return port


HOST = os.getenv("HOST", "127.0.0.1")
PORT = _configured_port()
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("SPHEREX_CORS_ORIGINS", "*").split(",")
    if origin.strip()
]

# Core directory structure
DATA_DIR = _configured_path("SPHEREX_DATA_DIR", PROJECT_DIR / "data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = _configured_path("SPHEREX_RESULTS_DIR", PROJECT_DIR / "results")
SCRIPTS_DIR = PROJECT_DIR / "scripts"
NOTEBOOKS_DIR = PROJECT_DIR / "notebooks"
PLOTS_DIR = RESULTS_DIR / "plots"
PROCESSED_FILENAMES = frozenset(
    {
        "epoch2_aligned_to_epoch1.fits",
        "epoch2_alignment_footprint.fits",
        "epoch2_flags_aligned.fits",
        "epoch2_minus_epoch1_difference.fits",
        "epoch2_variance_aligned.fits",
    }
)

# Ensure directories exist
for _dir in [DATA_DIR, RAW_DIR, PROCESSED_DIR, RESULTS_DIR, PLOTS_DIR, SCRIPTS_DIR, NOTEBOOKS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)


def project_path(*parts: str) -> Path:
    """Resolve one or more path components relative to the project root."""
    return PROJECT_DIR.joinpath(*parts)


def get_data_path(filename: str, processed: bool = False) -> Path:
    """
    Get the full path for a data file.
    
    Args:
        filename: Name of the data file
        processed: If True, look in processed/; otherwise look in raw/
    
    Returns:
        Full path to the data file
    """
    directory = PROCESSED_DIR if processed else RAW_DIR
    return directory / filename


def resolve_data_path(filename: str) -> Path:
    """Resolve a known raw or processed data filename to its project path."""
    return get_data_path(filename, processed=filename in PROCESSED_FILENAMES)


def get_result_path(filename: str) -> Path:
    """
    Get the full path for a result file (CSV, PNG, etc.).
    
    Args:
        filename: Name of the result file
    
    Returns:
        Full path to the result file
    """
    return RESULTS_DIR / filename


def get_script_path(filename: str) -> Path:
    """
    Get the full path for a script file.
    
    Args:
        filename: Name of the script file
    
    Returns:
        Full path to the script file
    """
    return SCRIPTS_DIR / filename


def migrate_file(source: Union[str, Path], destination: Union[str, Path]) -> None:
    """
    Move a file from source to destination, creating directories if needed.
    
    Args:
        source: Current file path
        destination: Target file path
    """
    import shutil
    
    source = Path(source)
    destination = Path(destination)
    
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
