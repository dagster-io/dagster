import importlib.util

if importlib.util.find_spec("dagster_dbt") is not None:
    from dagster_snowflake.components.dbt_project.component import (
        SnowflakeDbtProjectComponent as SnowflakeDbtProjectComponent,
    )
