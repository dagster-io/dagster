"""dbt project configuration for Dagster integration."""

import os
from pathlib import Path

from dagster_dbt import DbtProject

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Path to dbt project relative to this file
dbt_project_dir = PROJECT_ROOT / "dbt_project"

# DuckDB database path - used by both Dagster and dbt
DUCKDB_PATH = str(PROJECT_ROOT / "data_quality.duckdb")

# Set environment variable for dbt to use
os.environ["DBT_DUCKDB_PATH"] = DUCKDB_PATH

dbt_project = DbtProject(
    project_dir=dbt_project_dir,
    packaged_project_dir=dbt_project_dir,
)

# Prepare the dbt project during development
dbt_project.prepare_if_dev()
