from typing import Iterator, List, Optional

from dagster import (
    AssetsDefinition,
    AssetSpec,
    Definitions,
    _check as check,
    external_asset_from_spec,
)
from dagster._core.definitions.definitions_loader import DefinitionsLoadContext, DefinitionsLoadType
from dagster._serdes.serdes import deserialize_value, serialize_value
from dagster._utils.warnings import suppress_dagster_warnings

from dagster_airlift.constants import DAG_ID_METADATA_KEY, TASK_ID_METADATA_KEY
from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.airflow_instance import AirflowInstance, TaskInfo
from dagster_airlift.core.sensor import (
    DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
    build_airflow_polling_sensor,
)
from dagster_airlift.core.serialization.compute import _metadata_key, compute_serialized_data


def get_or_compute_airflow_data(
    *, airflow_instance: AirflowInstance, defs: Definitions
) -> AirflowDefinitionsData:
    context = DefinitionsLoadContext.get()
    metadata_key = _metadata_key(airflow_instance.name)
    if (
        context.load_type == DefinitionsLoadType.RECONSTRUCTION
        and metadata_key in context.reconstruction_metadata
    ):
        airflow_definition_data = deserialize_value(
            context.reconstruction_metadata[metadata_key], as_type=AirflowDefinitionsData
        )
        assert isinstance(airflow_definition_data, AirflowDefinitionsData)
        return airflow_definition_data
    else:
        serialized_data = compute_serialized_data(airflow_instance=airflow_instance, defs=defs)
        return AirflowDefinitionsData(
            instance_name=airflow_instance.name, serialized_data=serialized_data
        )


@suppress_dagster_warnings
def build_defs_from_airflow_instance(
    *,
    airflow_instance: AirflowInstance,
    defs: Optional[Definitions] = None,
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
) -> Definitions:
    defs = defs or Definitions()
    airflow_data = get_or_compute_airflow_data(airflow_instance=airflow_instance, defs=defs)
    return definitions_from_airflow_data(
        airflow_data, defs, airflow_instance, sensor_minimum_interval_seconds
    ).with_reconstruction_metadata(
        {_metadata_key(airflow_data.instance_name): serialize_value(airflow_data)}
    )


def definitions_from_airflow_data(
    airflow_data: AirflowDefinitionsData,
    defs: Definitions,
    airflow_instance: AirflowInstance,
    sensor_minimum_interval_seconds: int,
) -> Definitions:
    assets_defs = construct_all_assets(
        definitions=defs,
        airflow_data=airflow_data,
    )
    return defs_with_assets_and_sensor(
        defs,
        assets_defs,
        airflow_instance,
        sensor_minimum_interval_seconds,
        airflow_data=airflow_data,
    )


def defs_with_assets_and_sensor(
    defs: Definitions,
    assets_defs: List[AssetsDefinition],
    airflow_instance: AirflowInstance,
    sensor_minimum_interval_seconds: int,
    airflow_data: AirflowDefinitionsData,
) -> Definitions:
    airflow_sensor = build_airflow_polling_sensor(
        airflow_instance=airflow_instance,
        minimum_interval_seconds=sensor_minimum_interval_seconds,
        airflow_data=airflow_data,
    )
    return Definitions(
        assets=assets_defs,
        asset_checks=defs.asset_checks if defs else None,
        sensors=[airflow_sensor, *defs.sensors] if defs and defs.sensors else [airflow_sensor],
        schedules=defs.schedules if defs else None,
        jobs=defs.jobs if defs else None,
        executor=defs.executor if defs else None,
        loggers=defs.loggers if defs else None,
        resources=defs.resources if defs else None,
    )


def construct_all_assets(
    definitions: Definitions,
    airflow_data: AirflowDefinitionsData,
) -> List[AssetsDefinition]:
    return (
        list(_apply_airflow_data_to_specs(definitions, airflow_data))
        + airflow_data.construct_dag_assets_defs()
    )


def _apply_airflow_data_to_specs(
    definitions: Definitions,
    airflow_data: AirflowDefinitionsData,
) -> Iterator[AssetsDefinition]:
    """Apply asset spec transformations to the asset definitions."""
    for asset in definitions.assets or []:
        asset = check.inst(  # noqa: PLW2901
            asset,
            (AssetSpec, AssetsDefinition),
            "Expected orchestrated defs to all be AssetsDefinitions or AssetSpecs.",
        )
        assets_def = (
            asset if isinstance(asset, AssetsDefinition) else external_asset_from_spec(asset)
        )
        yield assets_def.map_asset_specs(airflow_data.map_airflow_data_to_spec)


def get_task_info_for_spec(
    airflow_instance: AirflowInstance, spec: AssetSpec
) -> Optional[TaskInfo]:
    if TASK_ID_METADATA_KEY not in spec.metadata or DAG_ID_METADATA_KEY not in spec.metadata:
        return None
    return airflow_instance.get_task_info(
        dag_id=spec.metadata[DAG_ID_METADATA_KEY], task_id=spec.metadata[TASK_ID_METADATA_KEY]
    )
