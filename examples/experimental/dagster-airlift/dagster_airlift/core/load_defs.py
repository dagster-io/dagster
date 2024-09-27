from dataclasses import dataclass
from typing import Iterator, List, Optional, Sequence

from dagster import (
    AssetsDefinition,
    AssetSpec,
    Definitions,
    _check as check,
    external_asset_from_spec,
)
from dagster._core.definitions.events import AssetMaterialization
from dagster._utils.warnings import suppress_dagster_warnings

from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.airflow_instance import AirflowInstance, DagRun, TaskInstance
from dagster_airlift.core.sensor import (
    DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
    airflow_event_sensor,
    get_asset_events,
)
from dagster_airlift.core.serialization.compute import compute_serialized_data
from dagster_airlift.core.serialization.serialized_data import (
    SerializedAirflowDefinitionsData,
    metadata_key,
)
from dagster_airlift.core.state_backed_defs_loader import StateBackedDefinitionsLoader


@dataclass
class AirflowInstanceDefsLoader(StateBackedDefinitionsLoader[SerializedAirflowDefinitionsData]):
    airflow_instance: AirflowInstance
    explicit_defs: Definitions
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS

    @property
    def defs_key(self) -> str:
        return metadata_key(self.airflow_instance.name)

    def fetch_state(self) -> SerializedAirflowDefinitionsData:
        return compute_serialized_data(
            airflow_instance=self.airflow_instance, defs=self.explicit_defs
        )

    def defs_from_state(self, state: SerializedAirflowDefinitionsData) -> Definitions:
        return definitions_from_airflow_data(state, self.explicit_defs)


@suppress_dagster_warnings
def build_defs_from_airflow_instance(
    *,
    airflow_instance: AirflowInstance,
    defs: Optional[Definitions] = None,
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
) -> Definitions:
    defs = defs or Definitions()
    transformed_defs = AirflowInstanceDefsLoader(
        airflow_instance=airflow_instance,
        explicit_defs=defs,
        sensor_minimum_interval_seconds=sensor_minimum_interval_seconds,
    ).build_defs()
    return defs_with_sensor(transformed_defs, airflow_instance, sensor_minimum_interval_seconds)


def definitions_from_airflow_data(
    serialized_airflow_data: SerializedAirflowDefinitionsData,
    defs: Definitions,
) -> Definitions:
    assets_defs = construct_all_assets(
        definitions=defs,
        airflow_data=serialized_airflow_data,
    )
    return defs_with_assets(defs, assets_defs)


def defs_with_assets(
    defs: Definitions,
    assets_defs: List[AssetsDefinition],
) -> Definitions:
    return Definitions(
        assets=assets_defs,
        asset_checks=defs.asset_checks if defs else None,
        sensors=defs.sensors if defs else None,
        schedules=defs.schedules if defs else None,
        jobs=defs.jobs if defs else None,
        executor=defs.executor if defs else None,
        loggers=defs.loggers if defs else None,
        resources=defs.resources if defs else None,
    )


def defs_with_sensor(
    defs: Definitions,
    airflow_instance: AirflowInstance,
    sensor_minimum_interval_seconds: int,
) -> Definitions:
    airflow_data = AirflowDefinitionsData(
        transformed_defs=defs, instance_name=airflow_instance.name
    )

    @airflow_event_sensor(
        airflow_instance=airflow_instance,
        airflow_data=airflow_data,
        minimum_interval_seconds=sensor_minimum_interval_seconds,
    )
    def _airflow_sensor(
        dag_run: DagRun, task_instances: Sequence[TaskInstance]
    ) -> Sequence[AssetMaterialization]:
        return get_asset_events(
            dag_run=dag_run, task_instances=task_instances, airflow_data=airflow_data
        )

    return Definitions(
        assets=defs.assets if defs else None,
        asset_checks=defs.asset_checks if defs else None,
        sensors=[_airflow_sensor, *defs.sensors] if defs and defs.sensors else [_airflow_sensor],
        schedules=defs.schedules if defs else None,
        jobs=defs.jobs if defs else None,
        executor=defs.executor if defs else None,
        loggers=defs.loggers if defs else None,
        resources=defs.resources if defs else None,
        metadata=defs.metadata if defs else None,
    )


def construct_all_assets(
    definitions: Definitions,
    airflow_data: SerializedAirflowDefinitionsData,
) -> List[AssetsDefinition]:
    return (
        list(_apply_airflow_data_to_specs(definitions, airflow_data))
        + airflow_data.construct_dag_assets_defs()
    )


def _apply_airflow_data_to_specs(
    definitions: Definitions,
    airflow_data: SerializedAirflowDefinitionsData,
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
