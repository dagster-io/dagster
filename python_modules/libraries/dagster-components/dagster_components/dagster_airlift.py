import importlib.util

_has_dagster_airlift = importlib.util.find_spec("dagster_airlift") is not None

if _has_dagster_airlift:
    from dagster_components.components.airflow_instance.component import (
        AirflowInstanceComponent as AirflowInstanceComponent,
    )
