"""
Backward-compatibility module.
Redirects to spherex.config for all path management.
"""

# Import everything from spherex.config for backward compatibility
from spherex.config import PROJECT_DIR, project_path

__all__ = ["PROJECT_DIR", "project_path"]
