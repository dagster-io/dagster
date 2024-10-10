from collections import defaultdict
from functools import cached_property
from typing import AbstractSet, Dict, List, Sequence, Set, Union

from dagster import AssetKey, AssetSpec, Definitions
from dagster._record import record

from dagster_airlift.core.airflow_instance import AirflowInstance, DagInfo
from dagster_airlift.core.dag_asset import get_leaf_assets_for_dag
from dagster_airlift.core.serialization.serialized_data import (
    DagHandle,
    KeyScopedDataItem,
    SerializedAirflowDefinitionsData,
    SerializedDagData,
    TaskHandle,
    TaskInfo,
)
from dagster_airlift.core.utils import handles_for_spec, is_mapped_asset_spec, spec_iterator


@record
class AirliftMetadataMappingInfo:
    asset_specs: List[AssetSpec]

    @cached_property
    def mapped_asset_specs(self) -> List[AssetSpec]:
        return [spec for spec in self.asset_specs if is_mapped_asset_spec(spec)]

    @cached_property
    def dag_ids(self) -> Set[str]:
        return {handle.dag_id for handle in self.all_mapped_handles}

    @cached_property
    def task_id_map(self) -> Dict[str, Set[str]]:
        """Mapping of dag_id to set of task_ids in that dag. This only contains task ids mapped to assets in this object."""
        task_id_map = defaultdict(set)
        for handle in self.task_handles:
            task_id_map[handle.dag_id].add(handle.task_id)
        return task_id_map

    @cached_property
    def task_handles(self) -> Set[TaskHandle]:
        return {handle for handle in self.all_mapped_handles if isinstance(handle, TaskHandle)}

    @cached_property
    def asset_keys_per_dag_id(self) -> Dict[str, Set[AssetKey]]:
        """Mapping of dag_id to set of asset_keys in that dag. Does not include standlone dag assets."""
        mapped_keys_per_dag_id = defaultdict(set)
        for handle, asset_keys in self.handle_to_asset_keys.items():
            if isinstance(handle, DagHandle):
                mapped_keys_per_dag_id[handle.dag_id].update(asset_keys)
            if isinstance(handle, TaskHandle):
                mapped_keys_per_dag_id[handle.dag_id].update(asset_keys)
        return mapped_keys_per_dag_id

    @cached_property
    def handle_to_asset_keys(self) -> Dict[Union[DagHandle, TaskHandle], Set[AssetKey]]:
        """Mapping of dag_id to task_id to set of asset_keys mapped from that task."""
        asset_key_map: Dict[Union[DagHandle, TaskHandle], Set[AssetKey]] = defaultdict(set)
        for spec in self.asset_specs:
            if is_mapped_asset_spec(spec):
                for handle in handles_for_spec(spec):
                    asset_key_map[handle].add(spec.key)
        return asset_key_map

    @cached_property
    def all_mapped_handles(self) -> Sequence[Union[DagHandle, TaskHandle]]:
        return list(self.handle_to_asset_keys.keys())

    @cached_property
    def asset_key_to_handles(self) -> Dict[AssetKey, Set[TaskHandle]]:
        task_handle_map = defaultdict(set)
        for handle, asset_keys in self.handle_to_asset_keys.items():
            for asset_key in asset_keys:
                task_handle_map[asset_key].add(handle)
        return task_handle_map

    @cached_property
    def downstream_deps(self) -> Dict[AssetKey, Set[AssetKey]]:
        downstreams = defaultdict(set)
        for spec in self.asset_specs:
            for dep in spec.deps:
                downstreams[dep.asset_key].add(spec.key)
        return downstreams


def build_airlift_metadata_mapping_info(defs: Definitions) -> AirliftMetadataMappingInfo:
    asset_specs = list(spec_iterator(defs.assets))
    return AirliftMetadataMappingInfo(asset_specs=asset_specs)


@record
class FetchedAirflowData:
    dag_infos: Dict[str, DagInfo]
    task_info_map: Dict[str, Dict[str, TaskInfo]]
    mapping_info: AirliftMetadataMappingInfo

    @cached_property
    def all_mapped_handles(self) -> Dict[AssetKey, AbstractSet[Union[DagHandle, TaskHandle]]]:
        return {spec.key: handles_for_spec(spec) for spec in self.mapping_info.mapped_asset_specs}


def fetch_all_airflow_data(
    airflow_instance: AirflowInstance, mapping_info: AirliftMetadataMappingInfo
) -> FetchedAirflowData:
    dag_infos = {dag.dag_id: dag for dag in airflow_instance.list_dags()}
    task_info_map = defaultdict(dict)
    for dag_id in dag_infos:
        task_info_map[dag_id] = {
            task_info.task_id: task_info
            for task_info in airflow_instance.get_task_infos(dag_id=dag_id)
        }

    return FetchedAirflowData(
        dag_infos=dag_infos,
        task_info_map=task_info_map,
        mapping_info=mapping_info,
    )


def compute_serialized_data(
    airflow_instance: AirflowInstance, defs: Definitions
) -> "SerializedAirflowDefinitionsData":
    mapping_info = build_airlift_metadata_mapping_info(defs)
    fetched_airflow_data = fetch_all_airflow_data(airflow_instance, mapping_info)
    return SerializedAirflowDefinitionsData(
        instance_name=airflow_instance.name,
        key_scoped_data_items=[
            KeyScopedDataItem(asset_key=k, mapped_handles=v)
            for k, v in fetched_airflow_data.all_mapped_handles.items()
        ],
        dag_datas={
            dag_id: SerializedDagData(
                dag_id=dag_id,
                dag_info=dag_info,
                source_code=airflow_instance.get_dag_source_code(dag_info.metadata["file_token"]),
                leaf_asset_keys=get_leaf_assets_for_dag(
                    asset_keys_in_dag=mapping_info.asset_keys_per_dag_id[dag_id],
                    downstreams_asset_dependency_graph=mapping_info.downstream_deps,
                ),
                task_infos=fetched_airflow_data.task_info_map[dag_id],
            )
            for dag_id, dag_info in fetched_airflow_data.dag_infos.items()
        },
    )
