from collections.abc import Mapping
from functools import cached_property
from typing import AbstractSet, Any, NamedTuple, Optional  # noqa: UP035

from dagster import (
    AssetKey,
    _check as check,
)
from dagster._annotations import PublicAttr, beta
from dagster._record import record
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
@record
class TaskInfo:
    webserver_url: str
    dag_id: str
    task_id: str
    metadata: dict[str, Any]

    @property
    def dag_url(self) -> str:
        return f"{self.webserver_url}/dags/{self.dag_id}"

    @cached_property
    def downstream_task_ids(self) -> list[str]:
        return check.is_list(self.metadata["downstream_task_ids"], str)


@beta
@whitelist_for_serdes
@record
class DagInfo:
    """A record containing information about a given airflow dag.

    Users should not instantiate this class directly. It is provided when customizing which DAGs are included
    in the generated definitions using the `dag_selector_fn` argument of :py:func:`build_defs_from_airflow_instance`.

    Args:
        metadata (Dict[str, Any]): The metadata associated with the dag, retrieved by the Airflow REST API:
            https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#operation/get_dags
    """

    webserver_url: str
    dag_id: str
    metadata: PublicAttr[dict[str, Any]]

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
    source_code: Optional[str]
    leaf_asset_keys: set[AssetKey]
    task_infos: Mapping[str, TaskInfo]


@whitelist_for_serdes
@record
class KeyScopedTaskHandles:
    asset_key: AssetKey
    mapped_tasks: AbstractSet[TaskHandle]


@whitelist_for_serdes
@record
class KeyScopedDagHandles:
    asset_key: AssetKey
    mapped_dags: AbstractSet[DagHandle]


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
    key_scoped_task_handles: list[KeyScopedTaskHandles]
    key_scoped_dag_handles: list[KeyScopedDagHandles]
    dag_datas: Mapping[str, SerializedDagData]

    @cached_property
    def all_mapped_tasks(self) -> dict[AssetKey, AbstractSet[TaskHandle]]:
        return {item.asset_key: item.mapped_tasks for item in self.key_scoped_task_handles}

    @cached_property
    def all_mapped_dags(self) -> dict[AssetKey, AbstractSet[DagHandle]]:
        return {item.asset_key: item.mapped_dags for item in self.key_scoped_dag_handles}
