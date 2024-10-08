from collections import defaultdict
from functools import cached_property
from typing import AbstractSet, Mapping, Set

from dagster import AssetKey, Definitions
from dagster._record import record

from dagster_airlift.constants import DAG_MAPPING_METADATA_KEY
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.serialization.compute import AirliftMetadataMappingInfo
from dagster_airlift.core.serialization.serialized_data import TaskHandle


@record
class AirflowDefinitionsData:
    airflow_instance: AirflowInstance
    mapped_defs: Definitions

    @property
    def instance_name(self) -> str:
        return self.airflow_instance.name

    @cached_property
    def mapping_info(self) -> AirliftMetadataMappingInfo:
        return AirliftMetadataMappingInfo(asset_specs=list(self.mapped_defs.get_all_asset_specs()))

    def task_ids_in_dag(self, dag_id: str) -> Set[str]:
        return {
            task_handle.task_id
            for task_handle in self.mapping_info.mapped_task_handles
            if task_handle.dag_id == dag_id
        }

    @property
    def dag_ids_with_mapped_asset_keys(self) -> AbstractSet[str]:
        return {handle.dag_id for handle in self.mapping_info.asset_key_map.keys()}

    @cached_property
    def asset_keys_per_task_handle(self) -> Mapping[TaskHandle, AbstractSet[AssetKey]]:
        return {
            handle: keys
            for handle, keys in self.mapping_info.asset_key_map.items()
            if isinstance(handle, TaskHandle)
        }

    @cached_property
    def asset_keys_per_dag(self) -> Mapping[str, AbstractSet[AssetKey]]:
        dag_id_to_asset_key = defaultdict(set)
        for spec in self.mapped_defs.get_all_asset_specs():
            if DAG_MAPPING_METADATA_KEY in spec.metadata:
                for dag_id in spec.metadata[DAG_MAPPING_METADATA_KEY]:
                    dag_id_to_asset_key[dag_id].add(spec.key)
        return dag_id_to_asset_key

    def asset_keys_in_task(self, dag_id: str, task_id: str) -> AbstractSet[AssetKey]:
        return self.asset_keys_per_task_handle[TaskHandle(dag_id=dag_id, task_id=task_id)]
