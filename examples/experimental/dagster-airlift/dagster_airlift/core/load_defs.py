from dataclasses import dataclass
from typing import Iterable, Iterator, Optional

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
    build_airflow_polling_sensor_defs,
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

    def defs_from_state(self, airflow_data: AirflowDefinitionsData) -> Definitions:
        return Definitions.merge(
            enrich_explicit_defs_with_airflow_metadata(self.explicit_defs, airflow_data),
            airflow_data.construct_dag_assets_defs(),
            build_airflow_polling_sensor_defs(
                airflow_instance=self.airflow_instance,
                minimum_interval_seconds=self.sensor_minimum_interval_seconds,
                airflow_data=airflow_data,
            ),
        )


@suppress_dagster_warnings
def build_defs_from_airflow_instance(
    *,
    airflow_instance: AirflowInstance,
    defs: Optional[Definitions] = None,
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
) -> Definitions:
    return AirflowInstanceDefsLoader(
        airflow_instance=airflow_instance,
        explicit_defs=defs or Definitions(),
        sensor_minimum_interval_seconds=sensor_minimum_interval_seconds,
    ).build_defs()


class FullAutomappedDagsLoader(StateBackedDefinitionsLoader[AirflowDefinitionsData]):
    def __init__(
        self,
        airflow_instance: AirflowInstance,
        sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
    ):
        self.airflow_instance = airflow_instance
        self.sensor_minimum_interval_seconds = sensor_minimum_interval_seconds

    @property
    def defs_key(self) -> str:
        return _metadata_key(self.airflow_instance.name) + "/full_automapped_dags"

    def fetch_state(self) -> AirflowDefinitionsData:
        return AirflowDefinitionsData(
            instance_name=self.airflow_instance.name,
            serialized_data=compute_serialized_data(
                airflow_instance=self.airflow_instance, defs=Definitions()
            ),
        )

    def defs_from_state(self, airflow_data: AirflowDefinitionsData) -> Definitions:
        return Definitions.merge(
            airflow_data.construct_automapped_dag_assets_defs(),
            build_airflow_polling_sensor_defs(
                airflow_instance=self.airflow_instance,
                minimum_interval_seconds=self.sensor_minimum_interval_seconds,
                airflow_data=airflow_data,
            ),
        )


def build_full_automapped_dags_from_airflow_instance(
    *,
    airflow_instance: AirflowInstance,
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
) -> Definitions:
    return FullAutomappedDagsLoader(
        airflow_instance=airflow_instance,
        sensor_minimum_interval_seconds=sensor_minimum_interval_seconds,
    ).build_defs()


def enrich_explicit_defs_with_airflow_metadata(
    explicit_defs: Definitions, airflow_data: AirflowDefinitionsData
) -> Definitions:
    return replace_assets_in_defs(
        explicit_defs,
        (
            assets_def.map_asset_specs(airflow_data.map_airflow_data_to_spec)
            for assets_def in assets_def_of_defs(explicit_defs)
        ),
    )


def replace_assets_in_defs(defs: Definitions, assets: Iterable[AssetsDefinition]) -> Definitions:
    return Definitions(
        assets=list(assets),
        asset_checks=defs.asset_checks,
        sensors=defs.sensors,
        schedules=defs.schedules,
        jobs=defs.jobs,
        executor=defs.executor,
        loggers=defs.loggers,
        resources=defs.resources,
    )


def assets_def_of_defs(defs: Definitions) -> Iterator[AssetsDefinition]:
    for asset in defs.assets or []:
        asset = check.inst(  # noqa: PLW2901
            asset,
            (AssetSpec, AssetsDefinition),
            "Expected passed assets to all be AssetsDefinitions or AssetSpecs.",
        )
        yield asset if isinstance(asset, AssetsDefinition) else external_asset_from_spec(asset)
