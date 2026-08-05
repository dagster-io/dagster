from dagster_snowflake.components.sql_component.component import SnowflakeConnectionComponent

__all__ = [
    "SnowflakeConnectionComponent",
]

# The dbt project component requires the optional `dagster-dbt` dependency
# (`pip install 'dagster-snowflake[dbt]'`). It is only registered when available.
try:
    from dagster_snowflake.components.dbt_project.component import (
        SnowflakeDbtProjectComponent as SnowflakeDbtProjectComponent,
    )

    __all__.append("SnowflakeDbtProjectComponent")
except ImportError:
    pass
