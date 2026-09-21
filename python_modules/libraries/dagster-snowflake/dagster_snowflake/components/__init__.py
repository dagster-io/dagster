import importlib.util

from dagster_snowflake.components.sql_component.component import SnowflakeConnectionComponent

__all__ = [
    "SnowflakeConnectionComponent",
]

if importlib.util.find_spec("dagster_dbt") is not None:
    from dagster_snowflake.components.dbt_project.component import (
        SnowflakeDbtProjectComponent as SnowflakeDbtProjectComponent,
    )

    __all__.append("SnowflakeDbtProjectComponent")
