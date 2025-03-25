from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from typing import Any, Callable, Optional, Union

from dagster import (
    AssetsDefinition,
    AssetSpec,
    Definitions,
    _check as check,
)
from dagster._annotations import beta
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._core.definitions.external_asset import external_asset_from_spec
from dagster._core.definitions.sensor_definition import DefaultSensorStatus

from dagster_airlift.core.airflow_defs_data import MappedAsset
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.sensor.event_translation import (
    DagsterEventTransformerFn,
    default_event_transformer,
)
from dagster_airlift.core.sensor.sensor_builder import (
    DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
    build_airflow_polling_sensor,
)
from dagster_airlift.core.serialization.compute import DagSelectorFn, compute_serialized_data
from dagster_airlift.core.serialization.defs_construction import (
    construct_dag_assets_defs,
    get_airflow_data_to_spec_mapper,
)
from dagster_airlift.core.serialization.serialized_data import (
    DagInfo,
    SerializedAirflowDefinitionsData,
)
from dagster_airlift.core.utils import get_metadata_key, spec_iterator


@dataclass
class AirflowInstanceDefsLoader(StateBackedDefinitionsLoader[SerializedAirflowDefinitionsData]):
    airflow_instance: AirflowInstance
    mapped_assets: Sequence[MappedAsset]
    source_code_retrieval_enabled: Optional[bool]
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS
    dag_selector_fn: Optional[DagSelectorFn] = None

    @property
    def defs_key(self) -> str:
        return get_metadata_key(self.airflow_instance.name)

    def fetch_state(self) -> SerializedAirflowDefinitionsData:
        return compute_serialized_data(
            airflow_instance=self.airflow_instance,
            mapped_assets=self.mapped_assets,
            dag_selector_fn=self.dag_selector_fn,
            automapping_enabled=False,
            source_code_retrieval_enabled=self.source_code_retrieval_enabled,
        )

    def defs_from_state(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, serialized_airflow_data: SerializedAirflowDefinitionsData
    ) -> Definitions:
        return Definitions(
            assets=[
                *_apply_airflow_data_to_specs(self.mapped_assets, serialized_airflow_data),
                *construct_dag_assets_defs(serialized_airflow_data),
            ]
        )


@beta
def build_defs_from_airflow_instance(
    *,
    airflow_instance: AirflowInstance,
    defs: Optional[Definitions] = None,
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
    event_transformer_fn: DagsterEventTransformerFn = default_event_transformer,
    dag_selector_fn: Optional[Callable[[DagInfo], bool]] = None,
    source_code_retrieval_enabled: Optional[bool] = None,
    default_sensor_status: Optional[DefaultSensorStatus] = None,
) -> Definitions:
    """Builds a :py:class:`dagster.Definitions` object from an Airflow instance.

    For every DAG in the Airflow instance, this function will create a Dagster asset for the DAG
    with an asset key instance_name/dag/dag_id. It will also create a sensor that polls the Airflow
    instance for DAG runs and emits Dagster events for each successful run.

    An optional `defs` argument can be provided, where the user can pass in a :py:class:`dagster.Definitions`
    object containing assets which are mapped to Airflow DAGs and tasks. These assets will be enriched with
    metadata from the Airflow instance, and placed upstream of the automatically generated DAG assets.

    An optional `event_transformer_fn` can be provided, which allows the user to modify the Dagster events
    produced by the sensor. The function takes the Dagster events produced by the sensor and returns a sequence
    of Dagster events.

    An optional `dag_selector_fn` can be provided, which allows the user to filter which DAGs assets are created for.
    The function takes a :py:class:`dagster_airlift.core.serialization.serialized_data.DagInfo` object and returns a
    boolean indicating whether the DAG should be included.

    Args:
        airflow_instance (AirflowInstance): The Airflow instance to build assets and the sensor from.
        defs: Optional[Definitions]: A :py:class:`dagster.Definitions` object containing assets that are
            mapped to Airflow DAGs and tasks.
        sensor_minimum_interval_seconds (int): The minimum interval in seconds between sensor runs.
        event_transformer_fn (DagsterEventTransformerFn): A function that allows for modifying the Dagster events
            produced by the sensor.
        dag_selector_fn (Optional[Callable[[DagInfo], bool]]): A function that allows for filtering which DAGs assets are created for.
        source_code_retrieval_enabled (Optional[bool]): Whether to retrieve source code for the Airflow DAGs. By default, source code is retrieved when the number of DAGs is under 50 for performance reasons. This setting overrides the default behavior.
        default_sensor_status (Optional[DefaultSensorStatus]): The default status for the sensor. By default, the sensor will be enabled.

    Returns:
        Definitions: A :py:class:`dagster.Definitions` object containing the assets and sensor.

    Examples:
        Building a :py:class:`dagster.Definitions` object from an Airflow instance.

        .. code-block:: python

            from dagster_airlift.core import (
                AirflowInstance,
                AirflowBasicAuthBackend,
                build_defs_from_airflow_instance,
            )

            from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME

            airflow_instance = AirflowInstance(
                auth_backend=AirflowBasicAuthBackend(
                    webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
                ),
                name=AIRFLOW_INSTANCE_NAME,
            )


            defs = build_defs_from_airflow_instance(airflow_instance=airflow_instance)

        Providing task-mapped assets to the function.

        .. code-block:: python

            from dagster import Definitions
            from dagster_airlift.core import (
                AirflowInstance,
                AirflowBasicAuthBackend,
                assets_with_task_mappings,
                build_defs_from_airflow_instance,
            )
            ...


            defs = build_defs_from_airflow_instance(
                airflow_instance=airflow_instance, # same as above
                defs=Definitions(
                    assets=assets_with_task_mappings(
                        dag_id="rebuild_iris_models",
                        task_mappings={
                            "my_task": [AssetSpec("my_first_asset"), AssetSpec("my_second_asset")],
                        },
                    ),
                ),
            )

        Providing a custom event transformer function.

        .. code-block:: python

            from typing import Sequence
            from dagster import Definitions, SensorEvaluationContext
            from dagster_airlift.core import (
                AirflowInstance,
                AirflowBasicAuthBackend,
                AssetEvent,
                assets_with_task_mappings,
                build_defs_from_airflow_instance,
                AirflowDefinitionsData,
            )
            ...

            def add_tags_to_events(
                context: SensorEvaluationContext,
                defs_data: AirflowDefinitionsData,
                events: Sequence[AssetEvent]
            ) -> Sequence[AssetEvent]:
                altered_events = []
                for event in events:
                    altered_events.append(event._replace(tags={"my_tag": "my_value"}))
                return altered_events

            defs = build_defs_from_airflow_instance(
                airflow_instance=airflow_instance, # same as above
                event_transformer_fn=add_tags_to_events,
            )

        Filtering which DAGs assets are created for.

        .. code-block:: python

            from dagster import Definitions
            from dagster_airlift.core import (
                AirflowInstance,
                AirflowBasicAuthBackend,
                AssetEvent,
                assets_with_task_mappings,
                build_defs_from_airflow_instance,
                DagInfo,
            )
            ...

            def only_include_dag(dag_info: DagInfo) -> bool:
                return dag_info.dag_id == "my_dag_id"

            defs = build_defs_from_airflow_instance(
                airflow_instance=airflow_instance, # same as above
                dag_selector_fn=only_include_dag,
            )

    """
    defs = defs or Definitions()
    mapped_assets = _type_narrow_defs_assets(defs)
    serialized_airflow_data = AirflowInstanceDefsLoader(
        airflow_instance=airflow_instance,
        mapped_assets=mapped_assets,
        dag_selector_fn=dag_selector_fn,
        source_code_retrieval_enabled=source_code_retrieval_enabled,
    ).get_or_fetch_state()
    mapped_and_constructed_assets = [
        *_apply_airflow_data_to_specs(mapped_assets, serialized_airflow_data),
        *construct_dag_assets_defs(serialized_airflow_data),
    ]
    defs_with_airflow_assets = replace_assets_in_defs(
        defs=defs, assets=mapped_and_constructed_assets
    )

    return Definitions.merge(
        defs_with_airflow_assets,
        Definitions(
            sensors=[
                build_airflow_polling_sensor(
                    mapped_assets=mapped_and_constructed_assets,
                    airflow_instance=airflow_instance,
                    minimum_interval_seconds=sensor_minimum_interval_seconds,
                    event_transformer_fn=event_transformer_fn,
                    default_sensor_status=default_sensor_status,
                )
            ]
        ),
    )


def _type_check_asset(asset: Any) -> MappedAsset:
    return check.inst(
        asset,
        (AssetSpec, AssetsDefinition),
        "Expected passed assets to all be AssetsDefinitions or AssetSpecs.",
    )


def _type_narrow_defs_assets(defs: Definitions) -> Sequence[MappedAsset]:
    return [_type_check_asset(asset) for asset in defs.assets or []]


def _apply_airflow_data_to_specs(
    assets: Sequence[MappedAsset],
    serialized_data: SerializedAirflowDefinitionsData,
) -> Iterator[AssetsDefinition]:
    """Apply asset spec transformations to the asset definitions."""
    for asset in assets:
        narrowed_asset = _type_check_asset(asset)
        assets_def = (
            narrowed_asset
            if isinstance(narrowed_asset, AssetsDefinition)
            else external_asset_from_spec(narrowed_asset)
        )
        yield assets_def.map_asset_specs(get_airflow_data_to_spec_mapper(serialized_data))


def replace_assets_in_defs(
    defs: Definitions, assets: Iterable[Union[AssetSpec, AssetsDefinition]]
) -> Definitions:
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


def enrich_airflow_mapped_assets(
    mapped_assets: Sequence[MappedAsset],
    airflow_instance: AirflowInstance,
    source_code_retrieval_enabled: Optional[bool],
) -> Sequence[AssetsDefinition]:
    """Enrich Airflow-mapped assets with metadata from the provided :py:class:`AirflowInstance`."""
    serialized_data = AirflowInstanceDefsLoader(
        airflow_instance=airflow_instance,
        mapped_assets=mapped_assets,
        source_code_retrieval_enabled=source_code_retrieval_enabled,
    ).get_or_fetch_state()
    return list(_apply_airflow_data_to_specs(mapped_assets, serialized_data))


@beta
def load_airflow_dag_asset_specs(
    airflow_instance: AirflowInstance,
    mapped_assets: Optional[Sequence[MappedAsset]] = None,
    dag_selector_fn: Optional[Callable[[DagInfo], bool]] = None,
    source_code_retrieval_enabled: Optional[bool] = None,
) -> Sequence[AssetSpec]:
    """Load asset specs for Airflow DAGs from the provided :py:class:`AirflowInstance`, and link upstreams from mapped assets."""
    serialized_data = AirflowInstanceDefsLoader(
        airflow_instance=airflow_instance,
        mapped_assets=mapped_assets or [],
        dag_selector_fn=dag_selector_fn,
        source_code_retrieval_enabled=source_code_retrieval_enabled,
    ).get_or_fetch_state()
    return list(spec_iterator(construct_dag_assets_defs(serialized_data)))
