import dagster as dg
from dagster_dbt import DbtCliResource
from dagster_duckdb import DuckDBResource

from project_dbt.defs.assets.dbt import project

dbt_resource = DbtCliResource(
    project_dir=project.project_dir,
)

database_resource = DuckDBResource(
    database=dg.EnvVar("DUCKDB_DATABASE"),
)


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "database": database_resource,
            "dbt": dbt_resource,
        },
    )
