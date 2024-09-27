from functools import cached_property
from typing import AbstractSet, Any, Dict, List, Mapping, NamedTuple, Optional, Sequence

from dagster import AssetDep, AssetKey, AssetSpec
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
# Data for reconstructing AssetSpecs from serialized data.
###################################################################################################
# History:
# - created
@whitelist_for_serdes
@record
class SerializedAssetSpecData:
    """Serializable data that can be used to construct a fully qualified AssetSpec."""

    asset_key: AssetKey
    description: Optional[str]
    metadata: Mapping[str, Any]
    tags: Mapping[str, str]
    deps: Sequence["SerializedAssetDepData"]

    def to_asset_spec(self) -> AssetSpec:
        return AssetSpec(
            key=self.asset_key,
            description=self.description,
            metadata=self.metadata,
            tags=self.tags,
            deps=[AssetDep(asset=dep.asset_key) for dep in self.deps] if self.deps else [],
        )


# History:
# - created
@whitelist_for_serdes
@record
class SerializedAssetDepData:
    # A dumbed down version of AssetDep that can be serialized easily to and from a dictionary.
    asset_key: AssetKey

    @staticmethod
    def from_asset_dep(asset_dep: AssetDep) -> "SerializedAssetDepData":
        return SerializedAssetDepData(asset_key=asset_dep.asset_key)


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
    spec_data: SerializedAssetSpecData
    task_handle_data: Mapping[str, "SerializedTaskHandleData"]


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
