# ruff: noqa: I001
# start_load_project
from pathlib import Path

from dagster_dbt import DbtProject

jaffle_shop_project = DbtProject(
    project_dir=Path(__file__).joinpath("..", "..", "..").resolve(),
    packaged_project_dir=Path(__file__).joinpath("..", "..", "dbt-project").resolve(),
)
# If `dagster dev` is used, the dbt project will be prepared to create the manifest at run time.
# Otherwise, we expect a manifest to be present in the project's target directory.
jaffle_shop_project.prepare_if_dev()

# end_load_project
