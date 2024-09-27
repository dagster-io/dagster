from functools import cached_property
from typing import AbstractSet, Any, Dict, List, Mapping, NamedTuple, Optional, Set

from dagster import AssetKey
from dagster._record import record
from dagster._serdes import whitelist_for_serdes

from dagster_airlift.core.utils import convert_to_valid_dagster_name


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


@whitelist_for_serdes
@record
class DagInfo:
    webserver_url: str
    dag_id: str
    metadata: Dict[str, Any]

    @property
    def url(self) -> str:
        return f"{self.webserver_url}/dags/{self.dag_id}"

    @cached_property
    def dagster_safe_dag_id(self) -> str:
        """Name based on the dag_id that is safe to use in dagster."""
        return convert_to_valid_dagster_name(self.dag_id)

    @property
    def dag_asset_key(self) -> AssetKey:
        # Conventional asset key representing a successful run of an airfow dag.
        return AssetKey(["airflow_instance", "dag", self.dagster_safe_dag_id])

    @property
    def file_token(self) -> str:
        return self.metadata["file_token"]


@whitelist_for_serdes
class TaskHandle(NamedTuple):
    dag_id: str
    task_id: str


@whitelist_for_serdes
@record
class MappedAirflowTaskData:
    task_info: TaskInfo
    task_handle: TaskHandle
    migrated: Optional[bool]


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
    task_handle_data: Mapping[str, "SerializedTaskHandleData"]
    dag_info: DagInfo
    source_code: str
    leaf_asset_keys: Set[AssetKey]


@whitelist_for_serdes
@record
class KeyScopedDataItem:
    asset_key: AssetKey
    mapped_tasks: List[MappedAirflowTaskData]


###################################################################################################
# Serializable data that will be cached to avoid repeated calls to the Airflow API, and to avoid
# repeated scans of passed-in Definitions objects.
###################################################################################################
# History:
# - created
# - removed existing_asset_data
# - added key_scope_data_items
@whitelist_for_serdes
@record
class SerializedAirflowDefinitionsData:
    key_scoped_data_items: List[KeyScopedDataItem]
    dag_datas: Mapping[str, SerializedDagData]

    @cached_property
    def all_mapped_tasks(self) -> Dict[AssetKey, List[MappedAirflowTaskData]]:
        return {item.asset_key: item.mapped_tasks for item in self.key_scoped_data_items}


# History:
# - created
@whitelist_for_serdes
@record
class SerializedTaskHandleData:
    """A record containing known data about a given airflow task handle."""

    migration_state: Optional[bool]
    asset_keys_in_task: AbstractSet[AssetKey]
