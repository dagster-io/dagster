from collections import defaultdict
from collections.abc import Iterable
from functools import cached_property
from typing import TYPE_CHECKING, AbstractSet, Callable, Optional  # noqa: UP035

from dagster import AssetKey, AssetSpec
from dagster._record import record

from dagster_airlift.core.airflow_instance import AirflowInstance, DagInfo
from dagster_airlift.core.dag_asset import get_leaf_assets_for_dag
from dagster_airlift.core.serialization.serialized_data import (
    DagHandle,
    KeyScopedDagHandles,
    KeyScopedTaskHandles,
    SerializedAirflowDefinitionsData,
    SerializedDagData,
    TaskHandle,
    TaskInfo,
)
from dagster_airlift.core.utils import (
    dag_handles_for_spec,
    is_dag_mapped_asset_spec,
    is_task_mapped_asset_spec,
    spec_iterator,
    task_handles_for_spec,
)

if TYPE_CHECKING:
    from dagster_airlift.core.airflow_defs_data import MappedAsset


DEFAULT_MAX_NUM_DAGS_SOURCE_CODE_RETRIEVAL = 50
DagSelectorFn = Callable[[DagInfo], bool]


@record
class AirliftMetadataMappingInfo:
    asset_specs: Iterable[AssetSpec]

    @cached_property
    def mapped_task_asset_specs(self) -> list[AssetSpec]:
        return [spec for spec in self.asset_specs if is_task_mapped_asset_spec(spec)]

    @cached_property
    def mapped_dag_asset_specs(self) -> list[AssetSpec]:
        return [spec for spec in self.asset_specs if is_dag_mapped_asset_spec(spec)]

    @cached_property
    def dag_ids(self) -> set[str]:
        return set(self.all_mapped_asset_keys_by_dag_id.keys())

    @cached_property
    def task_id_map(self) -> dict[str, set[str]]:
        """Mapping of dag_id to set of task_ids in that dag. This only contains task ids mapped to assets in this object."""
        task_id_map_data = {
            dag_id: set(ta_map.keys())
            for dag_id, ta_map in self.asset_keys_by_mapped_task_id.items()
        }
        return defaultdict(set, task_id_map_data)

    @cached_property
    def all_mapped_asset_keys_by_dag_id(self) -> dict[str, set[AssetKey]]:
        """Mapping of dag_id to set of asset_keys which are materialized by that dag.

        If assets within the dag are mapped to individual tasks, all of those assets will be included in this set.
        If the dag itself is mapped to a set of assets, those assets will be included in this set.
        """
        asset_keys_in_dag_by_id = defaultdict(set)
        for dag_id, task_to_asset_map in self.asset_keys_by_mapped_task_id.items():
            for asset_keys in task_to_asset_map.values():
                asset_keys_in_dag_by_id[dag_id].update(asset_keys)
        for dag_id, asset_keys in self.asset_keys_by_mapped_dag_id.items():
            asset_keys_in_dag_by_id[dag_id].update(asset_keys)
        return defaultdict(set, asset_keys_in_dag_by_id)

    @cached_property
    def asset_keys_by_mapped_task_id(self) -> dict[str, dict[str, set[AssetKey]]]:
        """Mapping of dag_id to task_id to set of asset_keys mapped from that task."""
        asset_key_map: dict[str, dict[str, set[AssetKey]]] = defaultdict(lambda: defaultdict(set))
        for spec in self.asset_specs:
            if is_task_mapped_asset_spec(spec):
                for task_handle in task_handles_for_spec(spec):
                    asset_key_map[task_handle.dag_id][task_handle.task_id].add(spec.key)
        return asset_key_map

    @cached_property
    def asset_keys_by_mapped_dag_id(self) -> dict[str, set[AssetKey]]:
        """Mapping of dag_id to set of asset_keys mapped from that dag."""
        asset_key_map: dict[str, set[AssetKey]] = defaultdict(set)
        for spec in self.asset_specs:
            if is_dag_mapped_asset_spec(spec):
                for dag_handle in dag_handles_for_spec(spec):
                    asset_key_map[dag_handle.dag_id].add(spec.key)
        return asset_key_map

    @cached_property
    def task_handle_map(self) -> dict[AssetKey, set[TaskHandle]]:
        task_handle_map = defaultdict(set)
        for dag_id, asset_key_by_task_id in self.asset_keys_by_mapped_task_id.items():
            for task_id, asset_keys in asset_key_by_task_id.items():
                for asset_key in asset_keys:
                    task_handle_map[asset_key].add(TaskHandle(dag_id=dag_id, task_id=task_id))
        return task_handle_map

    @cached_property
    def downstream_deps(self) -> dict[AssetKey, set[AssetKey]]:
        downstreams = defaultdict(set)
        for spec in self.asset_specs:
            for dep in spec.deps:
                downstreams[dep.asset_key].add(spec.key)
        return downstreams


def build_airlift_metadata_mapping_info(
    mapped_assets: Iterable["MappedAsset"],
) -> AirliftMetadataMappingInfo:
    asset_specs = list(spec_iterator(mapped_assets))
    return AirliftMetadataMappingInfo(asset_specs=asset_specs)


@record
class FetchedAirflowData:
    dag_infos: dict[str, DagInfo]
    task_info_map: dict[str, dict[str, TaskInfo]]
    mapping_info: AirliftMetadataMappingInfo

    @cached_property
    def all_mapped_tasks(self) -> dict[AssetKey, AbstractSet[TaskHandle]]:
        return {
            spec.key: task_handles_for_spec(spec)
            for spec in self.mapping_info.mapped_task_asset_specs
        }

    @cached_property
    def all_mapped_dags(self) -> dict[AssetKey, AbstractSet[DagHandle]]:
        return {
            spec.key: dag_handles_for_spec(spec)
            for spec in self.mapping_info.mapped_dag_asset_specs
        }


def fetch_all_airflow_data(
    airflow_instance: AirflowInstance,
    mapping_info: AirliftMetadataMappingInfo,
    dag_selector_fn: Optional[DagSelectorFn],
    automapping_enabled: bool,
) -> FetchedAirflowData:
    dag_infos = {
        dag.dag_id: dag
        for dag in airflow_instance.list_dags()
        if dag_selector_fn is None or dag_selector_fn(dag)
    }
    # To limit the number of API calls, only fetch task infos for the dags that we absolutely have to.
    # Airflow has no batch API for fetching task infos, so we have to fetch them one dag
    # at a time.
    task_info_map = defaultdict(dict)
    for dag_id in dag_infos.keys():
        # Explicitly don't fetch task information for dags that have no mapped tasks,
        # unless automapping is enabled.
        if len(mapping_info.task_id_map[dag_id]) == 0 and not automapping_enabled:
            continue
        task_info_map[dag_id] = {
            task_info.task_id: task_info
            for task_info in airflow_instance.get_task_infos(dag_id=dag_id)
        }

    return FetchedAirflowData(
        dag_infos=dag_infos,
        task_info_map=task_info_map,
        mapping_info=mapping_info,
    )


def infer_code_retrieval_enabled(
    source_code_retrieval_enabled: Optional[bool], fetched_airflow_data: FetchedAirflowData
) -> bool:
    if source_code_retrieval_enabled is None:
        return len(fetched_airflow_data.dag_infos) < DEFAULT_MAX_NUM_DAGS_SOURCE_CODE_RETRIEVAL
    return source_code_retrieval_enabled


def compute_serialized_data(
    airflow_instance: AirflowInstance,
    mapped_assets: Iterable["MappedAsset"],
    dag_selector_fn: Optional[DagSelectorFn],
    automapping_enabled: bool,
    source_code_retrieval_enabled: Optional[bool],
) -> "SerializedAirflowDefinitionsData":
    mapping_info = build_airlift_metadata_mapping_info(mapped_assets)
    fetched_airflow_data = fetch_all_airflow_data(
        airflow_instance, mapping_info, dag_selector_fn, automapping_enabled=automapping_enabled
    )
    source_code_retrieval_enabled = infer_code_retrieval_enabled(
        source_code_retrieval_enabled, fetched_airflow_data
    )
    return SerializedAirflowDefinitionsData(
        instance_name=airflow_instance.name,
        key_scoped_task_handles=[
            KeyScopedTaskHandles(asset_key=k, mapped_tasks=v)
            for k, v in fetched_airflow_data.all_mapped_tasks.items()
        ],
        key_scoped_dag_handles=[
            KeyScopedDagHandles(asset_key=k, mapped_dags=v)
            for k, v in fetched_airflow_data.all_mapped_dags.items()
        ],
        dag_datas={
            dag_id: SerializedDagData(
                dag_id=dag_id,
                dag_info=dag_info,
                source_code=airflow_instance.get_dag_source_code(dag_info.metadata["file_token"])
                if source_code_retrieval_enabled
                else None,
                leaf_asset_keys=get_leaf_assets_for_dag(
                    asset_keys_in_dag=mapping_info.all_mapped_asset_keys_by_dag_id[dag_id],
                    downstreams_asset_dependency_graph=mapping_info.downstream_deps,
                ),
                task_infos=fetched_airflow_data.task_info_map[dag_id],
            )
            for dag_id, dag_info in fetched_airflow_data.dag_infos.items()
        },
    )
