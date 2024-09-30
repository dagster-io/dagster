from functools import cached_property
from typing import AbstractSet, Optional, cast

from dagster import AssetKey, Definitions
from dagster._record import record
from dagster._serdes.serdes import deserialize_value

from dagster_airlift.core.serialization.defs_construction import make_default_dag_asset_key
from dagster_airlift.core.serialization.serialized_data import SerializedAirflowDefinitionsData
from dagster_airlift.core.utils import get_metadata_key


@record
class AirflowDefinitionsData:
    instance_name: str
    resolved_airflow_defs: Definitions

    @cached_property
    def serialized_data(self) -> SerializedAirflowDefinitionsData:
        serialized_data_str = self.resolved_airflow_defs.metadata[
            get_metadata_key(self.instance_name)
        ].value
        return deserialize_value(
            cast(str, serialized_data_str), as_type=SerializedAirflowDefinitionsData
        )

    @property
    def all_dag_ids(self) -> AbstractSet[str]:
        return set(self.serialized_data.dag_datas.keys())

    def asset_key_for_dag(self, dag_id: str) -> AssetKey:
        return make_default_dag_asset_key(self.serialized_data.instance_name, dag_id)

    def task_ids_in_dag(self, dag_id: str) -> AbstractSet[str]:
        return set(self.serialized_data.dag_datas[dag_id].task_handle_data.keys())

    def proxied_state_for_task(self, dag_id: str, task_id: str) -> Optional[bool]:
        return self.serialized_data.dag_datas[dag_id].task_handle_data[task_id].proxied_state

    def asset_keys_in_task(self, dag_id: str, task_id: str) -> AbstractSet[AssetKey]:
        return self.serialized_data.dag_datas[dag_id].task_handle_data[task_id].asset_keys_in_task
