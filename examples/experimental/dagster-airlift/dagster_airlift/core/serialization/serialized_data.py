from functools import cached_property
from typing import AbstractSet, Any, Dict, List, Mapping, NamedTuple, Set

from dagster import (
    AssetKey,
    _check as check,
)
from dagster._record import record
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
@record
class TaskInfo:
    webserver_url: str
    dag_id: str
    task_id: str
    metadata: Dict[str, Any]

    @property
    def dag_url(self) -> str:
        return f"{self.webserver_url}/dags/{self.dag_id}"

    @cached_property
    def downstream_task_ids(self) -> List[str]:
        return check.is_list(self.metadata["downstream_task_ids"], str)


@whitelist_for_serdes
@record
class DagInfo:
    webserver_url: str
    dag_id: str
    metadata: Dict[str, Any]

    @property
    def url(self) -> str:
        return f"{self.webserver_url}/dags/{self.dag_id}"

    @property
    def file_token(self) -> str:
        return self.metadata["file_token"]


@whitelist_for_serdes
class TaskHandle(NamedTuple):
    dag_id: str
    task_id: str


###################################################################################################
# Serialized data that scopes to airflow DAGs and tasks.
###################################################################################################
# History:
# - created
@whitelist_for_serdes
@record
class SerializedDagData:
    """A record containing pre-computed data about a given airflow dag."""

    dag_id: str
    dag_info: DagInfo
    source_code: str
    leaf_asset_keys: Set[AssetKey]
    task_infos: Mapping[str, TaskInfo]


@whitelist_for_serdes
@record
class KeyScopedDataItem:
    asset_key: AssetKey
    mapped_tasks: AbstractSet[TaskHandle]


###################################################################################################
# Serializable data that will be cached to avoid repeated calls to the Airflow API, and to avoid
# repeated scans of passed-in Definitions objects.
###################################################################################################
# History:
# - created
# - removed existing_asset_data
# - added key_scope_data_items
# - added instance_name
@whitelist_for_serdes
@record
class SerializedAirflowDefinitionsData:
    instance_name: str
    key_scoped_data_items: List[KeyScopedDataItem]
    dag_datas: Mapping[str, SerializedDagData]

    @cached_property
    def all_mapped_tasks(self) -> Dict[AssetKey, AbstractSet[TaskHandle]]:
        return {item.asset_key: item.mapped_tasks for item in self.key_scoped_data_items}
