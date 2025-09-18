# highlight-start
# These lines can be removed
from pathlib import Path

from dagster_dbt import DbtCliResource, DbtProject

import dagster as dg

dbt_project_directory = Path(__file__).absolute().parent / "dbt"
dbt_project = DbtProject(project_dir=dbt_project_directory)

dbt_resource = DbtCliResource(project_dir=dbt_project)


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "dbt": dbt_resource,
        }
    )


# highlight-end
