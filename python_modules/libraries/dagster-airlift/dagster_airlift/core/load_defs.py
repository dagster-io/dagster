from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Optional, Union, cast

from dagster import AssetsDefinition, AssetSpec, Definitions
from dagster._annotations import beta
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets.definition.asset_spec import map_asset_specs
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._core.definitions.external_asset import external_asset_from_spec
from dagster._core.definitions.sensor_definition import DefaultSensorStatus

from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.filter import AirflowFilter
from dagster_airlift.core.job_builder import construct_dag_jobs
from dagster_airlift.core.monitoring_job.builder import build_airflow_monitoring_defs
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
from dagster_airlift.core.utils import (
    MappedAsset,
    dag_handles_for_spec,
    get_metadata_key,
    is_dag_mapped_asset_spec,
    is_task_mapped_asset_spec,
    spec_iterator,
    task_handles_for_spec,
    type_narrow_defs_assets,
)


@dataclass
class AirflowInstanceDefsLoader(StateBackedDefinitionsLoader[SerializedAirflowDefinitionsData]):
    airflow_instance: AirflowInstance
    retrieval_filter: AirflowFilter
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
            retrieval_filter=self.retrieval_filter,
        )

    def defs_from_state(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, serialized_airflow_data: SerializedAirflowDefinitionsData
    ) -> Definitions:
        raise Exception(
            "We use get_or_fetch_state() to build definitions, and leave it up to the callsite how it is used."
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
    retrieval_filter: Optional[AirflowFilter] = None,
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
    mapped_assets = type_narrow_defs_assets(defs)
    serialized_airflow_data = AirflowInstanceDefsLoader(
        airflow_instance=airflow_instance,
        mapped_assets=mapped_assets,
        dag_selector_fn=dag_selector_fn,
        source_code_retrieval_enabled=source_code_retrieval_enabled,
        retrieval_filter=retrieval_filter or AirflowFilter(),
    ).get_or_fetch_state()
    assets_to_apply_airflow_data = [
        *mapped_assets,
        *construct_dataset_specs(serialized_airflow_data),
    ]
    mapped_and_constructed_assets = [
        *_apply_airflow_data_to_specs(assets_to_apply_airflow_data, serialized_airflow_data),
        *construct_dag_assets_defs(serialized_airflow_data),
    ]
    fully_resolved_assets_definitions = [
        external_asset_from_spec(asset)
        if isinstance(asset, AssetSpec)
        else cast("AssetsDefinition", asset)
        for asset in mapped_and_constructed_assets
    ]
    defs_with_airflow_assets = replace_assets_in_defs(
        defs=defs, assets=fully_resolved_assets_definitions
    )

    return Definitions.merge_unbound_defs(
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


def _apply_airflow_data_to_specs(
    assets: Sequence[MappedAsset],
    serialized_data: SerializedAirflowDefinitionsData,
) -> Sequence[MappedAsset]:
    """Apply asset spec transformations to the assets."""
    return cast(
        "Sequence[MappedAsset]",
        map_asset_specs(
            func=get_airflow_data_to_spec_mapper(serialized_data),
            iterable=assets,
        ),
    )


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
    retrieval_filter: Optional[AirflowFilter] = None,
) -> Sequence[MappedAsset]:
    """Enrich Airflow-mapped assets with metadata from the provided :py:class:`AirflowInstance`."""
    serialized_data = AirflowInstanceDefsLoader(
        airflow_instance=airflow_instance,
        mapped_assets=mapped_assets,
        source_code_retrieval_enabled=source_code_retrieval_enabled,
        retrieval_filter=retrieval_filter or AirflowFilter(),
    ).get_or_fetch_state()
    return list(_apply_airflow_data_to_specs(mapped_assets, serialized_data))


@beta
def load_airflow_dag_asset_specs(
    airflow_instance: AirflowInstance,
    mapped_assets: Optional[Sequence[MappedAsset]] = None,
    dag_selector_fn: Optional[Callable[[DagInfo], bool]] = None,
    source_code_retrieval_enabled: Optional[bool] = None,
    retrieval_filter: Optional[AirflowFilter] = None,
) -> Sequence[AssetSpec]:
    """Load asset specs for Airflow DAGs from the provided :py:class:`AirflowInstance`, and link upstreams from mapped assets."""
    serialized_data = AirflowInstanceDefsLoader(
        airflow_instance=airflow_instance,
        mapped_assets=mapped_assets or [],
        dag_selector_fn=dag_selector_fn,
        source_code_retrieval_enabled=source_code_retrieval_enabled,
        retrieval_filter=retrieval_filter or AirflowFilter(),
    ).get_or_fetch_state()
    return list(spec_iterator(construct_dag_assets_defs(serialized_data)))


def uri_to_asset_key(uri: str) -> AssetKey:
    last_path_segment = uri.split("/")[-1]
    with_ext_removed = last_path_segment.split(".")[0]
    return AssetKey(with_ext_removed)


def construct_dataset_specs(
    serialized_data: SerializedAirflowDefinitionsData,
) -> Sequence[AssetSpec]:
    """Construct dataset definitions from the serialized Airflow data."""
    from dagster_airlift.core.multiple_tasks import assets_with_multiple_task_mappings

    return cast(
        "Sequence[AssetSpec]",
        [
            assets_with_multiple_task_mappings(
                task_handles=[
                    {"dag_id": t.dag_id, "task_id": t.task_id} for t in dataset.producing_tasks
                ],
                assets=[
                    AssetSpec(
                        key=uri_to_asset_key(dataset.uri),
                        metadata=dataset.extra,
                        deps=[
                            uri_to_asset_key(upstream_uri)
                            for upstream_uri in serialized_data.upstream_datasets_by_uri.get(
                                dataset.uri, set()
                            )
                        ],
                    )
                ],
            )[0]
            for dataset in serialized_data.datasets
        ],
    )


def _get_dag_to_spec_mapping(
    mapped_assets: Sequence[Union[AssetSpec, AssetsDefinition]],
) -> Mapping[str, Sequence[AssetSpec]]:
    res = defaultdict(list)
    for spec in spec_iterator(mapped_assets):
        if is_task_mapped_asset_spec(spec):
            for task_handle in task_handles_for_spec(spec):
                res[task_handle.dag_id].append(spec)
        elif is_dag_mapped_asset_spec(spec):
            for dag_handle in dag_handles_for_spec(spec):
                res[dag_handle.dag_id].append(spec)
    return res


def build_job_based_airflow_defs(
    *,
    airflow_instance: AirflowInstance,
    retrieval_filter: Optional[AirflowFilter] = None,
    mapped_defs: Optional[Definitions] = None,
    source_code_retrieval_enabled: Optional[bool] = None,
) -> Definitions:
    mapped_defs = mapped_defs or Definitions()
    retrieval_filter = retrieval_filter or AirflowFilter()
    mapped_assets = type_narrow_defs_assets(mapped_defs)
    serialized_airflow_data = AirflowInstanceDefsLoader(
        airflow_instance=airflow_instance,
        mapped_assets=mapped_assets,
        dag_selector_fn=None,
        source_code_retrieval_enabled=source_code_retrieval_enabled,
        retrieval_filter=retrieval_filter,
    ).get_or_fetch_state()
    assets_with_airflow_data = _apply_airflow_data_to_specs(
        [
            *mapped_assets,
            *construct_dataset_specs(serialized_airflow_data),
        ],
        serialized_airflow_data,
    )
    dag_to_spec_mapping = _get_dag_to_spec_mapping(assets_with_airflow_data)
    jobs = construct_dag_jobs(
        serialized_data=serialized_airflow_data,
        mapped_specs=dag_to_spec_mapping,
    )
    return Definitions.merge(
        replace_assets_in_defs(defs=mapped_defs, assets=assets_with_airflow_data),
        Definitions(jobs=jobs),
        build_airflow_monitoring_defs(airflow_instance=airflow_instance),
    )
