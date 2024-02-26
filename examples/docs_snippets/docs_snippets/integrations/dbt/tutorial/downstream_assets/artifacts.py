import os
from pathlib import Path

from dagster_dbt import DbtArtifacts

dbt_artifacts = DbtArtifacts(
    project_dir=Path(__file__).joinpath("..", "..", "..").resolve()
)

if __name__ == "__main__":
    # Run this file as a script as part of deployment process to prepare manifest and handle package data
    dbt_artifacts.prepare()
