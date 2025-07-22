#!/usr/bin/env python3
"""Sphinx Docstring Validation Script for Dagster.

This script validates Python docstrings by parsing them through the same Sphinx pipeline
used for documentation generation. It helps catch docstring parsing issues early in the
development process before they reach the heavyweight Sphinx build.

Usage:
    python scripts/validate_docstrings.py dagster.asset
    python scripts/validate_docstrings.py dagster._core.definitions.op_definition.OpDefinition

This script now uses the automation.docstring_lint package for the core functionality.
"""

import sys
from pathlib import Path

# Add python modules to path to access automation package
DAGSTER_ROOT = Path(__file__).parent.parent
PYTHON_MODULES_PATH = DAGSTER_ROOT / "python_modules"
sys.path.insert(0, str(PYTHON_MODULES_PATH / "automation"))

from automation.docstring_lint.cli import main

if __name__ == "__main__":
    sys.exit(main())
