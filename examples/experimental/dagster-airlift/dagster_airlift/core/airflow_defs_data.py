from functools import cached_property
from typing import AbstractSet, Optional

from dagster import (
    AssetKey,
    Definitions,
    _check as check,
)
from dagster._record import record
from dagster._serdes import deserialize_value

from dagster_airlift.core.serialization.serialized_data import (
    SerializedAirflowDefinitionsData,
    metadata_key,
)


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

    @property
    def all_dag_ids(self) -> AbstractSet[str]:
        return set(self.serialized_data.dag_datas.keys())

    def asset_key_for_dag(self, dag_id: str) -> AssetKey:
        return self.serialized_data.dag_datas[dag_id].spec_data.asset_key

    def task_ids_in_dag(self, dag_id: str) -> AbstractSet[str]:
        return set(self.serialized_data.dag_datas[dag_id].task_handle_data.keys())

    def migration_state_for_task(self, dag_id: str, task_id: str) -> Optional[bool]:
        return self.serialized_data.dag_datas[dag_id].task_handle_data[task_id].migration_state

    def asset_keys_in_task(self, dag_id: str, task_id: str) -> AbstractSet[AssetKey]:
        return self.serialized_data.dag_datas[dag_id].task_handle_data[task_id].asset_keys_in_task

    def topo_order_index(self, asset_key: AssetKey) -> int:
        return self.serialized_data.asset_key_topological_ordering.index(asset_key)
