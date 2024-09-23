from collections import defaultdict
from typing import Dict, Optional, Set

from dagster import AssetKey, AssetSpec, Definitions
from dagster._core.utils import toposort_flatten

from dagster_airlift.constants import (
    AIRFLOW_SOURCE_METADATA_KEY_PREFIX,
    DAG_ID_METADATA_KEY,
    TASK_ID_METADATA_KEY,
)
from dagster_airlift.core.airflow_instance import AirflowInstance, TaskInfo
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


def compute_serialized_data(
    airflow_instance: AirflowInstance, defs: Definitions
) -> "SerializedAirflowDefinitionsData":
    migration_state = airflow_instance.get_migration_state()
    dag_infos = {dag.dag_id: dag for dag in airflow_instance.list_dags()}

    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]] = defaultdict(set)
    per_asset_key_airflow_data: Dict[AssetKey, SerializedAssetKeyScopedAirflowData] = {}
    upstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]] = defaultdict(set)
    all_asset_keys_per_dag_id: Dict[str, Set[AssetKey]] = defaultdict(set)
    keys_per_task_handle: Dict[str, Dict[str, Set[AssetKey]]] = defaultdict(
        lambda: defaultdict(set)
    )
    all_asset_keys = set()
    migration_state_per_task_handle: Dict[str, Dict[str, Optional[bool]]] = defaultdict(dict)
    task_ids_per_dag_id = defaultdict(set)
    for spec in spec_iterator(defs.assets):
        all_asset_keys.add(spec.key)
        task_info = _get_task_info_for_spec(airflow_instance, spec)
        if task_info is None:
            continue
        task_ids_per_dag_id[task_info.dag_id].add(task_info.task_id)
        keys_per_task_handle[task_info.dag_id][task_info.task_id].add(spec.key)
        # We technically overwrite the results here, but it's a lookup from an in-memory dictionary of small size.
        migration_state_for_task = migration_state.get_migration_state_for_task(
            dag_id=task_info.dag_id, task_id=task_info.task_id
        )
        migration_state_per_task_handle[task_info.dag_id][task_info.task_id] = (
            migration_state_for_task
        )
        per_asset_key_airflow_data[spec.key] = get_airflow_data_for_task_mapped_spec(
            task_info=task_info,
            migration_state=migration_state_for_task,
        )
        for dep in spec.deps:
            upstreams_asset_dependency_graph[spec.key].add(dep.asset_key)
            downstreams_asset_dependency_graph[dep.asset_key].add(spec.key)
        all_asset_keys_per_dag_id[task_info.dag_id].add(spec.key)
    check_keys_per_asset_key = defaultdict(set)
    for checks_def in defs.asset_checks or []:
        for check_key in checks_def.check_keys:
            check_keys_per_asset_key[check_key.asset_key].add(check_key)

    dag_datas = {}
    for dag_id, dag_info in dag_infos.items():
        leaf_asset_keys = get_leaf_assets_for_dag(
            asset_keys_in_dag=all_asset_keys_per_dag_id[dag_id],
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
        for task_id in task_ids_per_dag_id[dag_id]:
            task_handle_data[task_id] = SerializedTaskHandleData(
                migration_state=migration_state_per_task_handle[dag_id].get(task_id),
                asset_keys_in_task=keys_per_task_handle[dag_id][task_id],
            )
        dag_datas[dag_id] = SerializedDagData(
            dag_id=dag_id,
            spec_data=dag_spec,
            task_handle_data=task_handle_data,
            all_asset_keys_in_tasks=all_asset_keys_per_dag_id[dag_id],
        )
    existing_asset_data = {}
    for asset_key in all_asset_keys:
        existing_asset_data[asset_key] = SerializedAssetKeyScopedData(
            existing_key_data=per_asset_key_airflow_data.get(asset_key),
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
