# start_load_manifest
import os
from pathlib import Path

from dagster_dbt import DbtProject

# This class helps us manage expectations that
# * If using `dagster dev` (or set the environment variable DAGSTER_DBT_PARSE_PROJECT_ON_LOAD) compile the manifest on load.
# * If not expect the manifest.json to already be prepared. This can be done by running this file as a script.
jaffle_shop_project = DbtProject(
    project_dir=Path(__file__).joinpath("..", "..", "..").resolve()
)

# end_load_manifest
