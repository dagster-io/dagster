from dataclasses import dataclass
from typing import Iterator, Optional

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
    get_asset_events,
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
        )


@suppress_dagster_warnings
def build_defs_from_airflow_instance(
    *,
    airflow_instance: AirflowInstance,
    defs: Optional[Definitions] = None,
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
) -> Definitions:
    defs_loader = AirflowInstanceDefsLoader(
        airflow_instance=airflow_instance,
        explicit_defs=defs or Definitions(),
        sensor_minimum_interval_seconds=sensor_minimum_interval_seconds,
    )
    transformed_defs = defs_loader.build_defs()
    airflow_data = defs_loader.fetch_state()
    sensor_defs = build_airflow_polling_sensor_defs(
        airflow_instance=airflow_instance,
        airflow_data=airflow_data,
        event_translation_fn=lambda dag_run, task_instances: get_asset_events(
            dag_run=dag_run, task_instances=task_instances, airflow_data=airflow_data
        ),
        minimum_interval_seconds=sensor_minimum_interval_seconds,
    )
    return Definitions.merge(transformed_defs, sensor_defs)


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
    return Definitions(
        assets=list(_apply_airflow_data_to_specs(explicit_defs, airflow_data)),
        asset_checks=explicit_defs.asset_checks,
        sensors=explicit_defs.sensors,
        schedules=explicit_defs.schedules,
        jobs=explicit_defs.jobs,
        executor=explicit_defs.executor,
        loggers=explicit_defs.loggers,
        resources=explicit_defs.resources,
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
