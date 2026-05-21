#!/usr/bin/env python3
"""
Django Management Utility
-------------------------
Enhanced and production-ready version of manage.py

Features:
✔ Improved error handling
✔ Better logging
✔ Environment validation
✔ Python version check
✔ Cleaner structure
✔ Production-quality comments
✔ Safe execution flow
"""

import os
import sys
import logging
from pathlib import Path


# =========================
# Configuration
# =========================

BASE_DIR = Path(__file__).resolve().parent

PROJECT_SETTINGS = "invoice_system_management.settings"

MIN_PYTHON = (3, 10)


# =========================
# Logging Configuration
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# =========================
# Utility Functions
# =========================

def check_python_version() -> None:
    """
    Ensure the correct Python version is being used.
    """
    if sys.version_info < MIN_PYTHON:
        raise RuntimeError(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or higher is required."
        )


def configure_environment() -> None:
    """
    Configure Django environment variables.
    """
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        PROJECT_SETTINGS
    )


def import_django():
    """
    Import Django management utility safely.
    """
    try:
        from django.core.management import execute_from_command_line
        return execute_from_command_line

    except ImportError as exc:
        logger.error("Django import failed.")

        raise ImportError(
            "\nDjango is not installed or not available "
            "in the current environment.\n\n"
            "Possible Solutions:\n"
            "1. Activate your virtual environment\n"
            "2. Install dependencies:\n"
            "   pip install -r requirements.txt\n"
            "3. Verify PYTHONPATH configuration\n"
        ) from exc


# =========================
# Main Entry Point
# =========================

def main() -> None:
    """
    Main execution function.
    """

    try:
        check_python_version()

        configure_environment()

        execute_from_command_line = import_django()

        logger.info("Starting Django management utility...")

        execute_from_command_line(sys.argv)

    except Exception as error:
        logger.exception("Application startup failed.")
        sys.exit(f"\nERROR: {error}\n")


# =========================
# Script Execution
# =========================

if __name__ == "__main__":
    main()