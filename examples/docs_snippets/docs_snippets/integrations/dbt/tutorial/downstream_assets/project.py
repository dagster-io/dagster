import os
from pathlib import Path

from dagster_dbt import DbtProject

jaffle_shop_project = DbtProject(
    project_dir=Path(__file__).joinpath("..", "..", "..").resolve(),
)
