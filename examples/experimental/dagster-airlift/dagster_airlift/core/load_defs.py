from dataclasses import dataclass
from typing import Iterator, List, Optional

from dagster import (
    AssetsDefinition,
    AssetSpec,
    Definitions,
    _check as check,
    external_asset_from_spec,
)
from dagster._utils.warnings import suppress_dagster_warnings

from dagster_airlift.constants import AIRFLOW_SOURCE_METADATA_KEY_PREFIX
from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.sensor import (
    DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
    build_airflow_polling_sensor,
)
from dagster_airlift.core.serialization.compute import compute_serialized_data
from dagster_airlift.core.state_backed_defs_loader import StateBackedDefinitionsLoader


def _metadata_key(instance_name: str) -> str:
    return f"{AIRFLOW_SOURCE_METADATA_KEY_PREFIX}/{instance_name}"


@dataclass
class AirflowInstanceDefsLoader(StateBackedDefinitionsLoader[AirflowDefinitionsData]):
    airflow_instance: AirflowInstance
    explicit_defs: Definitions
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS

    @property
    def defs_key(self) -> str:
        return _metadata_key(self.airflow_instance.name)

    def fetch_state(self) -> AirflowDefinitionsData:
        return AirflowDefinitionsData(
            instance_name=self.airflow_instance.name,
            serialized_data=compute_serialized_data(
                airflow_instance=self.airflow_instance, defs=self.explicit_defs
            ),
        )

    def defs_from_state(self, state: AirflowDefinitionsData) -> Definitions:
        return definitions_from_airflow_data(
            state,
            self.explicit_defs,
            self.airflow_instance,
            self.sensor_minimum_interval_seconds,
        )


@suppress_dagster_warnings
def build_defs_from_airflow_instance(
    *,
    airflow_instance: AirflowInstance,
    defs: Optional[Definitions] = None,
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
) -> Definitions:
    defs = defs or Definitions()
    return AirflowInstanceDefsLoader(
        airflow_instance=airflow_instance,
        explicit_defs=defs,
        sensor_minimum_interval_seconds=sensor_minimum_interval_seconds,
    ).build_defs()


def definitions_from_airflow_data(
    airflow_data: AirflowDefinitionsData,
    explicit_defs: Definitions,
    airflow_instance: AirflowInstance,
    sensor_minimum_interval_seconds: int,
) -> Definitions:
    assets_defs = construct_all_assets(explicit_defs=explicit_defs, airflow_data=airflow_data)
    return defs_with_assets_and_sensor(
        explicit_defs,
        assets_defs,
        airflow_instance,
        sensor_minimum_interval_seconds,
        airflow_data=airflow_data,
    )


def defs_with_assets_and_sensor(
    explicit_defs: Definitions,
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
        asset_checks=explicit_defs.asset_checks if explicit_defs else None,
        sensors=[airflow_sensor, *explicit_defs.sensors]
        if explicit_defs and explicit_defs.sensors
        else [airflow_sensor],
        schedules=explicit_defs.schedules if explicit_defs else None,
        jobs=explicit_defs.jobs if explicit_defs else None,
        executor=explicit_defs.executor if explicit_defs else None,
        loggers=explicit_defs.loggers if explicit_defs else None,
        resources=explicit_defs.resources if explicit_defs else None,
    )


def construct_all_assets(
    explicit_defs: Definitions,
    airflow_data: AirflowDefinitionsData,
) -> List[AssetsDefinition]:
    return (
        list(_apply_airflow_data_to_specs(explicit_defs, airflow_data))
        + airflow_data.construct_dag_assets_defs()
    )


def _apply_airflow_data_to_specs(
    explicit_defs: Definitions,
    airflow_data: AirflowDefinitionsData,
) -> Iterator[AssetsDefinition]:
    """Apply asset spec transformations to the asset definitions."""
    for asset in explicit_defs.assets or []:
        asset = check.inst(  # noqa: PLW2901
            asset,
            (AssetSpec, AssetsDefinition),
            "Expected orchestrated defs to all be AssetsDefinitions or AssetSpecs.",
        )
        assets_def = (
            asset if isinstance(asset, AssetsDefinition) else external_asset_from_spec(asset)
        )
        yield assets_def.map_asset_specs(airflow_data.map_airflow_data_to_spec)
