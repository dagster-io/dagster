from collections import defaultdict
from functools import cached_property
from typing import AbstractSet, Dict, List, Mapping, Set, cast

from dagster import AssetKey, AssetSpec, Definitions
from dagster._record import record

from dagster_airlift.core.airflow_instance import AirflowInstance, DagInfo
from dagster_airlift.core.dag_asset import get_leaf_assets_for_dag
from dagster_airlift.core.serialization.serialized_data import (
    AirflowEntityHandle,
    KeyScopedDataItem,
    SerializedAirflowDefinitionsData,
    SerializedDagData,
    TaskHandle,
    TaskInfo,
)
from dagster_airlift.core.utils import airflow_handles_for_spec, is_mapped_asset_spec, spec_iterator


@record
class AirliftMetadataMappingInfo:
    asset_specs: List[AssetSpec]

    @cached_property
    def mapped_asset_specs(self) -> List[AssetSpec]:
        return [spec for spec in self.asset_specs if is_mapped_asset_spec(spec)]

    @cached_property
    def mapped_task_handles(self) -> AbstractSet[TaskHandle]:
        """All task handles that have at least one mapped asset."""
        return {handle for handle in self.asset_key_map.keys() if isinstance(handle, TaskHandle)}

    @cached_property
    def asset_keys_in_tasks_per_dag(self) -> Mapping[str, Set[AssetKey]]:
        """Mapping of dag_id to set of asset_keys in tasks from that dag. Does not include assets mapped to full dags."""
        asset_keys_per_dag_data = defaultdict(set)
        for task_handle in self.mapped_task_handles:
            asset_keys_per_dag_data[task_handle.dag_id].update(self.asset_key_map[task_handle])
        return asset_keys_per_dag_data

    @cached_property
    def asset_key_map(self) -> Dict[AirflowEntityHandle, Set[AssetKey]]:
        """Mapping of dag_id to task_id to set of asset_keys mapped from that task."""
        asset_key_map: Dict[AirflowEntityHandle, Set[AssetKey]] = defaultdict(set)
        for spec in self.mapped_asset_specs:
            for handle in airflow_handles_for_spec(spec):
                asset_key_map[handle].add(spec.key)
        return asset_key_map

    @cached_property
    def airflow_handle_map(self) -> Dict[AssetKey, Set[AirflowEntityHandle]]:
        handle_map = defaultdict(set)
        for handle, asset_keys in self.asset_key_map.items():
            for asset_key in asset_keys:
                handle_map[asset_key].add(handle)
        return handle_map

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
    def all_mapped_tasks(self) -> Dict[AssetKey, AbstractSet[TaskHandle]]:
        # This can simplify a lot once we handle dag assets on all paths.
        return {
            key: cast(AbstractSet[TaskHandle], handles)
            for key, handles in self.mapping_info.airflow_handle_map.items()
            if isinstance(next(iter(handles)), TaskHandle)
        }


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
            KeyScopedDataItem(asset_key=k, mapped_tasks=v)
            for k, v in fetched_airflow_data.all_mapped_tasks.items()
        ],
        dag_datas={
            dag_id: SerializedDagData(
                dag_id=dag_id,
                dag_info=dag_info,
                source_code=airflow_instance.get_dag_source_code(dag_info.metadata["file_token"]),
                leaf_asset_keys=get_leaf_assets_for_dag(
                    asset_keys_in_dag=mapping_info.asset_keys_in_tasks_per_dag[dag_id],
                    downstreams_asset_dependency_graph=mapping_info.downstream_deps,
                ),
                task_infos=fetched_airflow_data.task_info_map[dag_id],
            )
            for dag_id, dag_info in fetched_airflow_data.dag_infos.items()
        },
    )
