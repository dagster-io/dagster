from dagster import AssetSpec, Definitions
from dagster_airlift.core import (
    AirflowDefinitionsData,
    AirflowInstance,
    BasicAuthBackend,
    build_airflow_polling_sensor_defs,
    get_resolved_airflow_defs,
    maps_to_dag,
)

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url="http://localhost:8080", username="admin", password="admin"
    ),
    name="airflow_instance_one",
)


def get_resolved_defs() -> Definitions:
    """Get resolved definitions with additional metadata for a particular dag."""
    defs = get_resolved_airflow_defs(airflow_instance=airflow_instance)

    def _add_metadata(spec: AssetSpec) -> AssetSpec:
        if maps_to_dag(spec, "my_dag"):
            return spec._replace(metadata={"team": "my_team", **spec.metadata})
        return spec

    return defs.map_asset_specs(_add_metadata)  # type: ignore


defs_data = AirflowDefinitionsData(
    resolved_airflow_defs=get_resolved_defs(),
    airflow_instance=airflow_instance,
)

defs = Definitions.merge(
    defs_data.resolved_airflow_defs,
    build_airflow_polling_sensor_defs(defs_data),
)
