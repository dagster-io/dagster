from collections import defaultdict
from functools import cached_property
from typing import AbstractSet, Dict, List, Set

from dagster import AssetKey, AssetSpec, Definitions
from dagster._record import record

from dagster_airlift.core.airflow_instance import AirflowInstance, DagInfo
from dagster_airlift.core.dag_asset import get_leaf_assets_for_dag
from dagster_airlift.core.serialization.serialized_data import (
    KeyScopedDataItem,
    SerializedAirflowDefinitionsData,
    SerializedDagData,
    TaskHandle,
    TaskInfo,
)
from dagster_airlift.core.utils import is_mapped_asset_spec, spec_iterator, task_handles_for_spec


@record
class AirliftMetadataMappingInfo:
    asset_specs: List[AssetSpec]

    @cached_property
    def mapped_asset_specs(self) -> List[AssetSpec]:
        return [spec for spec in self.asset_specs if is_mapped_asset_spec(spec)]

    @cached_property
    def dag_ids(self) -> Set[str]:
        return set(self.task_id_map.keys())

    @cached_property
    def task_id_map(self) -> Dict[str, Set[str]]:
        """Mapping of dag_id to set of task_ids in that dag. This only contains task ids mapped to assets in this object."""
        task_id_map_data = {
            dag_id: set(ta_map.keys()) for dag_id, ta_map in self.asset_key_map.items()
        }
        return defaultdict(set, task_id_map_data)

    @cached_property
    def asset_keys_per_dag_id(self) -> Dict[str, Set[AssetKey]]:
        """Mapping of dag_id to set of asset_keys in that dag. Does not include standlone dag assets."""
        asset_keys_per_dag_data = {
            dag_id: {
                asset_key for asset_keys in task_to_asset_map.values() for asset_key in asset_keys
            }
            for dag_id, task_to_asset_map in self.asset_key_map.items()
        }
        return defaultdict(set, asset_keys_per_dag_data)

    @cached_property
    def asset_key_map(self) -> Dict[str, Dict[str, Set[AssetKey]]]:
        """Mapping of dag_id to task_id to set of asset_keys mapped from that task."""
        asset_key_map: Dict[str, Dict[str, Set[AssetKey]]] = defaultdict(lambda: defaultdict(set))
        for spec in self.asset_specs:
            if is_mapped_asset_spec(spec):
                for task_handle in task_handles_for_spec(spec):
                    asset_key_map[task_handle.dag_id][task_handle.task_id].add(spec.key)
        return asset_key_map

    @cached_property
    def task_handle_map(self) -> Dict[AssetKey, Set[TaskHandle]]:
        task_handle_map = defaultdict(set)
        for dag_id, asset_key_by_task_id in self.asset_key_map.items():
            for task_id, asset_keys in asset_key_by_task_id.items():
                for asset_key in asset_keys:
                    task_handle_map[asset_key].add(TaskHandle(dag_id=dag_id, task_id=task_id))
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
    def all_mapped_tasks(self) -> Dict[AssetKey, AbstractSet[TaskHandle]]:
        return {
            spec.key: task_handles_for_spec(spec) for spec in self.mapping_info.mapped_asset_specs
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
                    asset_keys_in_dag=mapping_info.asset_keys_per_dag_id[dag_id],
                    downstreams_asset_dependency_graph=mapping_info.downstream_deps,
                ),
                task_infos=fetched_airflow_data.task_info_map[dag_id],
            )
            for dag_id, dag_info in fetched_airflow_data.dag_infos.items()
        },
    )
