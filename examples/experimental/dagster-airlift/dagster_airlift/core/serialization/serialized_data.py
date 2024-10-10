from functools import cached_property
from typing import AbstractSet, Any, Dict, List, Mapping, NamedTuple, Set, Union

from dagster import (
    AssetKey,
    _check as check,
)
from dagster._core.definitions.metadata.metadata_value import JsonMetadataValue, UrlMetadataValue
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

    @property
    def dagster_metadata(self) -> Mapping[str, Any]:
        return {
            "Task Info (raw)": JsonMetadataValue(self.metadata),
            "Dag ID": self.dag_id,
            "Task ID": self.task_id,
            "Link to DAG": UrlMetadataValue(self.dag_url),
        }


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

    @property
    def dagster_description(self) -> str:
        return f"""
        A materialization corresponds to a successful run of airflow DAG {self.dag_id}.
        """

    @property
    def dagster_metadata(self) -> Mapping[str, Any]:
        return {
            "Dag Info (raw)": JsonMetadataValue(self.metadata),
            "Dag ID": self.dag_id,
            "Link to DAG": UrlMetadataValue(self.url),
        }


@whitelist_for_serdes
class TaskHandle(NamedTuple):
    dag_id: str
    task_id: str


@whitelist_for_serdes
class DagHandle(NamedTuple):
    dag_id: str


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
    mapped_handles: AbstractSet[Union[DagHandle, TaskHandle]]


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
    def all_mapped_handles(self) -> Dict[AssetKey, AbstractSet[Union[DagHandle, TaskHandle]]]:
        return {item.asset_key: item.mapped_handles for item in self.key_scoped_data_items}

    @cached_property
    def info_objects_per_handle(
        self,
    ) -> Mapping[Union[DagHandle, TaskHandle], Union[DagInfo, TaskInfo]]:
        ret = {}
        for dag_id, dag_data in self.dag_datas.items():
            ret[DagHandle(dag_id)] = dag_data.dag_info
            for task_id, task_info in dag_data.task_infos.items():
                ret[TaskHandle(dag_id, task_id)] = task_info
        return ret
