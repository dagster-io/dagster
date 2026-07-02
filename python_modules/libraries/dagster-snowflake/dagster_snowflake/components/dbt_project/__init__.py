try:
    from dagster_snowflake.components.dbt_project.component import (
        SnowflakeDbtProjectComponent as SnowflakeDbtProjectComponent,
    )
except ImportError:
    pass
