from typing import List, Sequence

from dagster import AssetMaterialization, Definitions
from dagster_airlift.core import (
    AirflowDefinitionsData,
    AirflowInstance,
    BasicAuthBackend,
    DagRun,
    TaskInstance,
    build_airflow_polling_sensor_defs,
    get_resolved_airflow_defs,
)

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url="http://localhost:8080", username="admin", password="admin"
    ),
    name="airflow_instance_one",
)


def get_resolved_defs() -> Definitions:
    """Get resolved definitions with additional metadata for a particular dag."""
    return get_resolved_airflow_defs(airflow_instance=airflow_instance)


defs_data = AirflowDefinitionsData(
    resolved_airflow_defs=get_resolved_defs(),
    airflow_instance=airflow_instance,
)


def alter_materializations(
    dag_run: DagRun, task_instances: Sequence[TaskInstance]
) -> List[AssetMaterialization]:
    def _transform_materialization(materialization: AssetMaterialization) -> AssetMaterialization:
        if defs_data.asset_key_for_dag("my_dag_id") == materialization.asset_key:
            return materialization._replace(
                metadata={"team": "my_team", **materialization.metadata}
            )
        return materialization

    return [
        _transform_materialization(mat)
        for mat in defs_data.default_event_translation_fn(dag_run, task_instances)
    ]


defs = Definitions.merge(
    defs_data.resolved_airflow_defs,
    build_airflow_polling_sensor_defs(defs_data, event_translation_fn=alter_materializations),
)
