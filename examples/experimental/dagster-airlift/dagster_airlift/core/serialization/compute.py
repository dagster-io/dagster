from collections import defaultdict
from functools import cached_property
from typing import Dict, List, NamedTuple, Optional, Set

from dagster import (
    AssetKey,
    AssetSpec,
    Definitions,
    _check as check,
)
from dagster._core.utils import toposort_flatten
from dagster._record import record

from dagster_airlift.constants import (
    AIRFLOW_SOURCE_METADATA_KEY_PREFIX,
    DAG_ID_METADATA_KEY,
    TASK_ID_METADATA_KEY,
)
from dagster_airlift.core.airflow_instance import AirflowInstance, DagInfo, TaskInfo
from dagster_airlift.core.dag_asset import dag_asset_spec_data, get_leaf_assets_for_dag
from dagster_airlift.core.serialization.serialized_data import (
    SerializedAirflowDefinitionsData,
    SerializedAssetKeyScopedAirflowData,
    SerializedAssetKeyScopedAssetGraphData,
    SerializedAssetKeyScopedData,
    SerializedDagData,
    SerializedTaskHandleData,
)
from dagster_airlift.core.task_asset import get_airflow_data_for_task_mapped_spec
from dagster_airlift.core.utils import spec_iterator
from dagster_airlift.migration_state import AirflowMigrationState


class TaskHandle(NamedTuple):
    dag_id: str
    task_id: str


@record
class TaskSpecMappingInfo:
    asset_specs: List[AssetSpec]

    @cached_property
    def mapped_asset_specs(self) -> List[AssetSpec]:
        return [spec for spec in self.asset_specs if is_mapped_asset_spec(spec)]

    @cached_property
    def asset_keys(self) -> Set[AssetKey]:
        return {spec.key for spec in self.asset_specs}

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
                dag_id, task_id = task_handle_for_spec(spec)
                asset_key_map[dag_id][task_id].add(spec.key)
        return asset_key_map

    @cached_property
    def task_handle_map(self) -> Dict[AssetKey, TaskHandle]:
        task_handle_map = {}
        for dag_id, asset_key_by_task_id in self.asset_key_map.items():
            for task_id, asset_keys in asset_key_by_task_id.items():
                for asset_key in asset_keys:
                    task_handle_map[asset_key] = TaskHandle(dag_id=dag_id, task_id=task_id)
        return task_handle_map


def is_mapped_asset_spec(spec: AssetSpec) -> bool:
    return DAG_ID_METADATA_KEY in spec.metadata and TASK_ID_METADATA_KEY in spec.metadata


def task_handle_for_spec(spec: AssetSpec) -> TaskHandle:
    check.param_invariant(is_mapped_asset_spec(spec), "spec", "Must be mappped spec")
    return TaskHandle(
        dag_id=spec.metadata[DAG_ID_METADATA_KEY], task_id=spec.metadata[TASK_ID_METADATA_KEY]
    )


def build_task_spec_mapping_info(defs: Definitions) -> TaskSpecMappingInfo:
    asset_specs = list(spec_iterator(defs.assets))
    return TaskSpecMappingInfo(asset_specs=asset_specs)


@record
class FetchedAirflowData:
    dag_infos: Dict[str, DagInfo]
    task_info_map: Dict[str, Dict[str, TaskInfo]]
    migration_state: AirflowMigrationState
    spec_mapping_info: TaskSpecMappingInfo

    @cached_property
    def migration_state_map(self) -> Dict[str, Dict[str, Optional[bool]]]:
        migration_state_map: Dict[str, Dict[str, Optional[bool]]] = defaultdict(dict)
        for spec in self.spec_mapping_info.mapped_asset_specs:
            dag_id, task_id = task_handle_for_spec(spec)
            migration_state_for_task = self.migration_state.get_migration_state_for_task(
                dag_id=dag_id, task_id=task_id
            )
            migration_state_map[dag_id][task_id] = migration_state_for_task
        return migration_state_map

    @cached_property
    def airflow_data_by_key(self) -> Dict[AssetKey, SerializedAssetKeyScopedAirflowData]:
        airflow_data_by_key = {}
        for spec in self.spec_mapping_info.mapped_asset_specs:
            dag_id, task_id = task_handle_for_spec(spec)
            airflow_data_by_key[spec.key] = get_airflow_data_for_task_mapped_spec(
                task_info=self.task_info_map[dag_id][task_id],
                migration_state=self.migration_state_map[dag_id][task_id],
            )

        return airflow_data_by_key


def fetch_all_airflow_data(
    airflow_instance: AirflowInstance, mapping_info: TaskSpecMappingInfo
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
        spec_mapping_info=mapping_info,
    )


def compute_serialized_data(
    airflow_instance: AirflowInstance, defs: Definitions
) -> "SerializedAirflowDefinitionsData":
    task_spec_mapping_info = build_task_spec_mapping_info(defs)

    fetched_airflow_data = fetch_all_airflow_data(airflow_instance, task_spec_mapping_info)

    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]] = defaultdict(set)
    upstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]] = defaultdict(set)
    for spec in task_spec_mapping_info.mapped_asset_specs:
        for dep in spec.deps:
            upstreams_asset_dependency_graph[spec.key].add(dep.asset_key)
            downstreams_asset_dependency_graph[dep.asset_key].add(spec.key)

    check_keys_per_asset_key = defaultdict(set)
    for checks_def in defs.asset_checks or []:
        for check_key in checks_def.check_keys:
            check_keys_per_asset_key[check_key.asset_key].add(check_key)

    all_asset_keys = task_spec_mapping_info.asset_keys

    dag_datas = {}
    for dag_id, dag_info in fetched_airflow_data.dag_infos.items():
        leaf_asset_keys = get_leaf_assets_for_dag(
            asset_keys_in_dag=task_spec_mapping_info.asset_keys_per_dag_id[dag_id],
            downstreams_asset_dependency_graph=downstreams_asset_dependency_graph,
        )
        dag_spec = dag_asset_spec_data(
            airflow_instance=airflow_instance,
            asset_keys_for_leaf_tasks=leaf_asset_keys,
            dag_info=dag_info,
        )
        all_asset_keys.add(dag_spec.asset_key)
        # Add dag asset to the upstream/downstream graphs.
        upstreams_asset_dependency_graph[dag_spec.asset_key] = set(leaf_asset_keys)
        for leaf_asset_key in leaf_asset_keys:
            downstreams_asset_dependency_graph[leaf_asset_key].add(dag_spec.asset_key)
        task_handle_data = {}
        for task_id in task_spec_mapping_info.task_id_map[dag_id]:
            task_handle_data[task_id] = SerializedTaskHandleData(
                migration_state=fetched_airflow_data.migration_state_map[dag_id].get(task_id),
                asset_keys_in_task=task_spec_mapping_info.asset_key_map[dag_id][task_id],
            )
        dag_datas[dag_id] = SerializedDagData(
            dag_id=dag_id,
            spec_data=dag_spec,
            task_handle_data=task_handle_data,
            all_asset_keys_in_tasks=task_spec_mapping_info.asset_keys_per_dag_id[dag_id],
        )
    existing_asset_data = {}
    for asset_key in all_asset_keys:
        existing_asset_data[asset_key] = SerializedAssetKeyScopedData(
            existing_key_data=fetched_airflow_data.airflow_data_by_key.get(asset_key),
            asset_graph_data=SerializedAssetKeyScopedAssetGraphData(
                upstreams=upstreams_asset_dependency_graph[asset_key],
                downstreams=downstreams_asset_dependency_graph[asset_key],
                check_keys=check_keys_per_asset_key[asset_key],
            ),
        )
    topology_order = toposort_flatten(upstreams_asset_dependency_graph)
    return SerializedAirflowDefinitionsData(
        existing_asset_data=existing_asset_data,
        dag_datas=dag_datas,
        asset_key_topological_ordering=topology_order,
    )


def _get_task_info_for_spec(
    airflow_instance: AirflowInstance, spec: AssetSpec
) -> Optional[TaskInfo]:
    if TASK_ID_METADATA_KEY not in spec.metadata or DAG_ID_METADATA_KEY not in spec.metadata:
        return None
    return airflow_instance.get_task_info(
        dag_id=spec.metadata[DAG_ID_METADATA_KEY], task_id=spec.metadata[TASK_ID_METADATA_KEY]
    )


def _metadata_key(instance_name: str) -> str:
    return f"{AIRFLOW_SOURCE_METADATA_KEY_PREFIX}/{instance_name}"
