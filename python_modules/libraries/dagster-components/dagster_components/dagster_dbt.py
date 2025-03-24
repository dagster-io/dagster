import importlib.util

_has_dagster_dbt = importlib.util.find_spec("dagster_dbt") is not None

if _has_dagster_dbt:
    from dagster_components.lib.dbt_project.component import (
        DbtProjectComponent as DbtProjectComponent,
    )
