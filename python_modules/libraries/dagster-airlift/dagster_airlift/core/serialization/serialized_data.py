from collections import defaultdict
from collections.abc import Mapping, Sequence
from functools import cached_property
from typing import AbstractSet, Any, NamedTuple, Optional  # noqa: UP035

from dagster import (
    AssetKey,
    _check as check,
)
from dagster._annotations import PublicAttr, beta
from dagster._record import record
from dagster._serdes import whitelist_for_serdes

from dagster_airlift.constants import (
    DAG_ID_TAG_KEY,
    DAG_MAPPING_METADATA_KEY,
    TASK_ID_TAG_KEY,
    TASK_MAPPING_METADATA_KEY,
)


###################################################################################################
# Serialized data that represents airflow DAGs and tasks.
###################################################################################################
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

    @property
    def metadata_key(self) -> str:
        return TASK_MAPPING_METADATA_KEY

    @property
    def as_dict(self) -> Mapping[str, Any]:
        return {
            "dag_id": self.dag_id,
            "task_id": self.task_id,
        }

    @property
    def identifying_tags(self) -> dict[str, str]:
        return {
            DAG_ID_TAG_KEY: self.dag_id,
            TASK_ID_TAG_KEY: self.task_id,
        }


@whitelist_for_serdes
class DagHandle(NamedTuple):
    dag_id: str

    @property
    def metadata_key(self) -> str:
        return DAG_MAPPING_METADATA_KEY

    @property
    def as_dict(self) -> Mapping[str, Any]:
        return {
            "dag_id": self.dag_id,
        }

    @property
    def identifying_tags(self) -> dict[str, str]:
        return {
            DAG_ID_TAG_KEY: self.dag_id,
        }


@whitelist_for_serdes
class DatasetConsumingDag(NamedTuple):
    dag_id: str
    created_at: str
    updated_at: str


@whitelist_for_serdes
class DatasetProducingTask(NamedTuple):
    dag_id: str
    task_id: str
    created_at: str
    updated_at: str


@whitelist_for_serdes
class Dataset(NamedTuple):
    id: int
    uri: str
    extra: Mapping[str, Any]
    created_at: str
    updated_at: str
    consuming_dags: Sequence[DatasetConsumingDag]
    producing_tasks: Sequence[DatasetProducingTask]

    def is_produced_by_task(self, *, task_id: str, dag_id: str) -> bool:
        return any(
            task.task_id == task_id and task.dag_id == dag_id for task in self.producing_tasks
        )


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
    datasets: Sequence[Dataset]

    @cached_property
    def all_mapped_tasks(self) -> dict[AssetKey, AbstractSet[TaskHandle]]:
        return {item.asset_key: item.mapped_tasks for item in self.key_scoped_task_handles}

    @cached_property
    def all_mapped_dags(self) -> dict[AssetKey, AbstractSet[DagHandle]]:
        return {item.asset_key: item.mapped_dags for item in self.key_scoped_dag_handles}

    @cached_property
    def datasets_by_dag_id(self) -> dict[str, set[str]]:
        """Mapping of dag_id to set of dataset uris it produces, in any task."""
        dataset_map: dict[str, set[str]] = defaultdict(set)
        for dataset in self.datasets:
            for producing_task in dataset.producing_tasks:
                dataset_map[producing_task.dag_id].add(dataset.uri)
        return dataset_map

    @cached_property
    def upstream_datasets_by_uri(self) -> dict[str, set[str]]:
        """Mapping of dataset uri to set of upstream dataset uris."""
        upstream_datasets_map: dict[str, set[str]] = defaultdict(set)
        for dataset in self.datasets:
            for consuming_dag_id in dataset.consuming_dags:
                datasets_produced_by_consuming_dag = self.datasets_by_dag_id.get(
                    consuming_dag_id.dag_id, set()
                )
                for downstream_dataset_uri in datasets_produced_by_consuming_dag:
                    upstream_datasets_map[downstream_dataset_uri].add(dataset.uri)
        return upstream_datasets_map
