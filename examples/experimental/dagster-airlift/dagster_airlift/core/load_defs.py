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

from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.sensor import (
    DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
    build_airflow_polling_sensor_defs,
    get_asset_events,
)
from dagster_airlift.core.serialization.compute import compute_serialized_data
from dagster_airlift.core.serialization.defs_construction import (
    construct_automapped_dag_assets_defs,
    construct_dag_assets_defs,
    get_airflow_data_to_spec_mapper,
)
from dagster_airlift.core.serialization.serialized_data import SerializedAirflowDefinitionsData
from dagster_airlift.core.state_backed_defs_loader import StateBackedDefinitionsLoader
from dagster_airlift.core.utils import get_metadata_key


@dataclass
class AirflowInstanceDefsLoader(StateBackedDefinitionsLoader[SerializedAirflowDefinitionsData]):
    airflow_instance: AirflowInstance
    explicit_defs: Definitions
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS

    @property
    def defs_key(self) -> str:
        return get_metadata_key(self.airflow_instance.name)

    def fetch_state(self) -> SerializedAirflowDefinitionsData:
        return compute_serialized_data(
            airflow_instance=self.airflow_instance, defs=self.explicit_defs
        )

    def defs_from_state(
        self, serialized_airflow_data: SerializedAirflowDefinitionsData
    ) -> Definitions:
        return Definitions.merge(
            enrich_explicit_defs_with_airflow_metadata(self.explicit_defs, serialized_airflow_data),
            construct_dag_assets_defs(serialized_airflow_data),
        )


@suppress_dagster_warnings
def build_defs_from_airflow_instance(
    *,
    airflow_instance: AirflowInstance,
    defs: Optional[Definitions] = None,
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
) -> Definitions:
    resolved_defs = AirflowInstanceDefsLoader(
        airflow_instance=airflow_instance,
        explicit_defs=defs or Definitions(),
        sensor_minimum_interval_seconds=sensor_minimum_interval_seconds,
    ).build_defs()
    return Definitions.merge(
        resolved_defs,
        build_airflow_polling_sensor_defs(
            airflow_data=AirflowDefinitionsData(
                airflow_instance=airflow_instance, resolved_airflow_defs=resolved_defs
            ),
            event_translation_fn=get_asset_events,
            minimum_interval_seconds=sensor_minimum_interval_seconds,
        ),
    )


class FullAutomappedDagsLoader(StateBackedDefinitionsLoader[SerializedAirflowDefinitionsData]):
    def __init__(
        self,
        airflow_instance: AirflowInstance,
        sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
    ):
        self.airflow_instance = airflow_instance
        self.sensor_minimum_interval_seconds = sensor_minimum_interval_seconds

    @property
    def defs_key(self) -> str:
        return get_metadata_key(self.airflow_instance.name) + "/full_automapped_dags"

    def fetch_state(self) -> SerializedAirflowDefinitionsData:
        return compute_serialized_data(airflow_instance=self.airflow_instance, defs=Definitions())

    def defs_from_state(
        self, serialized_airflow_data: SerializedAirflowDefinitionsData
    ) -> Definitions:
        return construct_automapped_dag_assets_defs(serialized_airflow_data)


def build_full_automapped_dags_from_airflow_instance(
    *,
    airflow_instance: AirflowInstance,
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
) -> Definitions:
    defs = FullAutomappedDagsLoader(
        airflow_instance=airflow_instance,
        sensor_minimum_interval_seconds=sensor_minimum_interval_seconds,
    ).build_defs()
    return Definitions.merge(
        defs,
        build_airflow_polling_sensor_defs(
            minimum_interval_seconds=sensor_minimum_interval_seconds,
            airflow_data=AirflowDefinitionsData(
                resolved_airflow_defs=defs, airflow_instance=airflow_instance
            ),
            event_translation_fn=get_asset_events,
        ),
    )


def enrich_explicit_defs_with_airflow_metadata(
    explicit_defs: Definitions, serialized_data: SerializedAirflowDefinitionsData
) -> Definitions:
    return Definitions(
        assets=list(_apply_airflow_data_to_specs(explicit_defs, serialized_data)),
        asset_checks=explicit_defs.asset_checks,
        sensors=explicit_defs.sensors,
        schedules=explicit_defs.schedules,
        jobs=explicit_defs.jobs,
        executor=explicit_defs.executor,
        loggers=explicit_defs.loggers,
        resources=explicit_defs.resources,
        metadata=explicit_defs.metadata,
    )


def _apply_airflow_data_to_specs(
    explicit_defs: Definitions,
    serialized_data: SerializedAirflowDefinitionsData,
) -> Iterator[AssetsDefinition]:
    """Apply asset spec transformations to the asset definitions."""
    for asset in explicit_defs.assets or []:
        asset = check.inst(  # noqa: PLW2901
            asset,
            (AssetSpec, AssetsDefinition),
            "Expected passed assets to all be AssetsDefinitions or AssetSpecs.",
        )
        assets_def = (
            asset if isinstance(asset, AssetsDefinition) else external_asset_from_spec(asset)
        )
        yield assets_def.map_asset_specs(get_airflow_data_to_spec_mapper(serialized_data))


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
