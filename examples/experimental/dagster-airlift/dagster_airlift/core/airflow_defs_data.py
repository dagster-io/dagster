from collections import defaultdict
from functools import cached_property
from typing import AbstractSet, Mapping, Optional, Sequence

from dagster import (
    AssetKey,
    AssetSpec,
    Definitions,
    _check as check,
)
from dagster._core.utils import toposort_flatten
from dagster._record import record
from dagster._serdes import deserialize_value

from dagster_airlift.constants import STANDALONE_DAG_ID_METADATA_KEY
from dagster_airlift.core.serialization.serialized_data import (
    SerializedAirflowDefinitionsData,
    metadata_key,
)
from dagster_airlift.core.utils import TaskHandle, is_mapped_asset_spec, task_handles_for_spec


@record
class AirflowDefinitionsData:
    transformed_defs: Definitions
    instance_name: str

    @cached_property
    def serialized_data(self) -> SerializedAirflowDefinitionsData:
        metadata_str = check.str_param(
            self.transformed_defs.metadata[metadata_key(self.instance_name)].value,
            "serialized metadata",
        )
        return deserialize_value(metadata_str, SerializedAirflowDefinitionsData)

    @cached_property
    def asset_specs_per_dag_id(self) -> Mapping[str, AssetSpec]:
        return {
            check.not_none(_get_dag_id(spec.metadata)): spec
            for spec in self.transformed_defs.get_all_asset_specs()
            if _get_dag_id(spec.metadata) is not None
        }

    @cached_property
    def asset_upstreams_graph(self) -> Mapping[AssetKey, AbstractSet[AssetKey]]:
        return {
            spec.key: {dep.asset_key for dep in spec.deps}
            for spec in self.transformed_defs.get_all_asset_specs()
        }

    @cached_property
    def asset_key_topological_ordering(self) -> Sequence[AssetKey]:
        return list(toposort_flatten(self.asset_upstreams_graph))

    @cached_property
    def task_handle_to_asset_keys(self) -> Mapping[TaskHandle, AbstractSet[AssetKey]]:
        task_handles_to_keys = defaultdict(set)
        for spec in self.transformed_defs.get_all_asset_specs():
            if is_mapped_asset_spec(spec):
                for task_handle in task_handles_for_spec(spec):
                    task_handles_to_keys[task_handle].add(spec.key)
        return task_handles_to_keys

    @property
    def all_dag_ids(self) -> AbstractSet[str]:
        return set(self.asset_specs_per_dag_id.keys())

    def asset_key_for_dag(self, dag_id: str) -> AssetKey:
        return self.asset_specs_per_dag_id[dag_id].key

    def task_ids_in_dag(self, dag_id: str) -> AbstractSet[str]:
        return set(self.serialized_data.dag_datas[dag_id].task_handle_data.keys())

    def migration_state_for_task(self, dag_id: str, task_id: str) -> Optional[bool]:
        return self.serialized_data.dag_datas[dag_id].task_handle_data[task_id].migration_state

    def asset_keys_in_task(self, dag_id: str, task_id: str) -> AbstractSet[AssetKey]:
        return self.task_handle_to_asset_keys[TaskHandle(dag_id=dag_id, task_id=task_id)]

    def topo_order_index(self, asset_key: AssetKey) -> int:
        return self.asset_key_topological_ordering.index(asset_key)


def _get_dag_id(metadata: Mapping[str, str]) -> Optional[str]:
    return metadata.get(STANDALONE_DAG_ID_METADATA_KEY)
