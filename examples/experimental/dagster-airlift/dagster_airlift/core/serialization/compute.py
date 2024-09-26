from collections import defaultdict
from functools import cached_property
from typing import Dict, List, Optional, Set

from dagster import (
    AssetKey,
    AssetSpec,
    Definitions,
    _check as check,
)
from dagster._record import record

from dagster_airlift.constants import TASK_MAPPING_METADATA_KEY
from dagster_airlift.core.airflow_instance import AirflowInstance, DagInfo, TaskInfo
from dagster_airlift.core.dag_asset import dag_asset_spec_data, get_leaf_assets_for_dag
from dagster_airlift.core.serialization.serialized_data import (
    KeyScopedDataItem,
    MappedAirflowTaskData,
    SerializedAirflowDefinitionsData,
    SerializedDagData,
    SerializedTaskHandleData,
    TaskHandle,
)
from dagster_airlift.core.utils import spec_iterator
from dagster_airlift.migration_state import AirflowMigrationState


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
        """Mapping of dag_id to set of task_ids in that dag."""
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
        for spec in self.mapped_asset_specs:
            for dep in spec.deps:
                downstreams[dep.asset_key].add(spec.key)
        return downstreams


def is_mapped_asset_spec(spec: AssetSpec) -> bool:
    return TASK_MAPPING_METADATA_KEY in spec.metadata


def task_handles_for_spec(spec: AssetSpec) -> Set[TaskHandle]:
    check.param_invariant(is_mapped_asset_spec(spec), "spec", "Must be mappped spec")
    task_handles = []
    for task_handle_dict in spec.metadata[TASK_MAPPING_METADATA_KEY]:
        task_handles.append(
            TaskHandle(dag_id=task_handle_dict["dag_id"], task_id=task_handle_dict["task_id"])
        )
    return set(task_handles)


def build_airlift_metadata_mapping_info(defs: Definitions) -> AirliftMetadataMappingInfo:
    asset_specs = list(spec_iterator(defs.assets))
    return AirliftMetadataMappingInfo(asset_specs=asset_specs)


@record
class FetchedAirflowData:
    dag_infos: Dict[str, DagInfo]
    task_info_map: Dict[str, Dict[str, TaskInfo]]
    migration_state: AirflowMigrationState
    mapping_info: AirliftMetadataMappingInfo

    @cached_property
    def migration_state_map(self) -> Dict[str, Dict[str, Optional[bool]]]:
        migration_state_map: Dict[str, Dict[str, Optional[bool]]] = defaultdict(dict)
        for spec in self.mapping_info.mapped_asset_specs:
            for task_handle in task_handles_for_spec(spec):
                dag_id, task_id = task_handle
                migration_state_map[task_handle.dag_id][task_handle.task_id] = None
                migration_state_for_task = self.migration_state.get_migration_state_for_task(
                    dag_id=dag_id, task_id=task_id
                )
                migration_state_map[dag_id][task_id] = migration_state_for_task
        return migration_state_map

    @cached_property
    def all_mapped_tasks(self) -> Dict[AssetKey, List[MappedAirflowTaskData]]:
        return {
            spec.key: [
                MappedAirflowTaskData(
                    task_handle=task_handle,
                    task_info=self.task_info_map[task_handle.dag_id][task_handle.task_id],
                    migrated=self.migration_state_map[task_handle.dag_id][task_handle.task_id],
                )
                for task_handle in task_handles_for_spec(spec)
            ]
            for spec in self.mapping_info.mapped_asset_specs
        }


def fetch_all_airflow_data(
    airflow_instance: AirflowInstance, mapping_info: AirliftMetadataMappingInfo
) -> FetchedAirflowData:
    dag_infos = {dag.dag_id: dag for dag in airflow_instance.list_dags()}
    task_info_map = defaultdict(dict)
    for dag_id in mapping_info.dag_ids:
        task_info_map[dag_id] = {
            task_info.task_id: task_info
            for task_info in airflow_instance.get_task_infos(dag_id=dag_id)
        }

    migration_state = airflow_instance.get_migration_state()

    return FetchedAirflowData(
        dag_infos=dag_infos,
        task_info_map=task_info_map,
        migration_state=migration_state,
        mapping_info=mapping_info,
    )


def compute_serialized_data(
    airflow_instance: AirflowInstance, defs: Definitions
) -> "SerializedAirflowDefinitionsData":
    mapping_info = build_airlift_metadata_mapping_info(defs)

    fetched_airflow_data = fetch_all_airflow_data(airflow_instance, mapping_info)

    dag_datas = {}
    for dag_id, dag_info in fetched_airflow_data.dag_infos.items():
        leaf_asset_keys = get_leaf_assets_for_dag(
            asset_keys_in_dag=mapping_info.asset_keys_per_dag_id[dag_id],
            downstreams_asset_dependency_graph=mapping_info.downstream_deps,
        )
        dag_spec = dag_asset_spec_data(
            airflow_instance=airflow_instance,
            asset_keys_for_leaf_tasks=leaf_asset_keys,
            dag_info=dag_info,
        )
        task_handle_data = {}
        for task_id in mapping_info.task_id_map[dag_id]:
            task_handle_data[task_id] = SerializedTaskHandleData(
                migration_state=fetched_airflow_data.migration_state_map[dag_id].get(task_id),
                asset_keys_in_task=mapping_info.asset_key_map[dag_id][task_id],
            )
        dag_datas[dag_id] = SerializedDagData(
            dag_id=dag_id,
            spec_data=dag_spec,
            task_handle_data=task_handle_data,
        )

    return SerializedAirflowDefinitionsData(
        key_scoped_data_items=[
            KeyScopedDataItem(asset_key=k, mapped_tasks=v)
            for k, v in fetched_airflow_data.all_mapped_tasks.items()
        ],
        dag_datas=dag_datas,
    )
