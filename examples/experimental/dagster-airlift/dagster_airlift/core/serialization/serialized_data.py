from functools import cached_property
from typing import AbstractSet, Any, List, Mapping, Optional, Sequence

from dagster import AssetDep, AssetKey, AssetsDefinition, AssetSpec, external_asset_from_spec
from dagster._record import record
from dagster._serdes import whitelist_for_serdes
from dagster._utils.merger import merge_dicts

from dagster_airlift.constants import AIRFLOW_SOURCE_METADATA_KEY_PREFIX


def metadata_key(instance_name: str) -> str:
    return f"{AIRFLOW_SOURCE_METADATA_KEY_PREFIX}/{instance_name}"


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
    all_asset_keys_in_tasks: AbstractSet[AssetKey]


@whitelist_for_serdes
@record
class KeyScopedDataItem:
    asset_key: AssetKey
    data: "SerializedAssetKeyScopedAirflowData"


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
    instance_name: str
    key_scoped_data_items: List[KeyScopedDataItem]
    dag_datas: Mapping[str, SerializedDagData]
    asset_key_topological_ordering: Sequence[AssetKey]

    @cached_property
    def key_scope_data_map(self) -> Mapping[AssetKey, "SerializedAssetKeyScopedAirflowData"]:
        return {item.asset_key: item.data for item in self.key_scoped_data_items}

    def map_airflow_data_to_spec(self, spec: AssetSpec) -> AssetSpec:
        """If there is airflow data applicable to the asset key, transform the spec and apply the data."""
        existing_key_data = self.key_scope_data_map.get(spec.key)
        return spec if not existing_key_data else existing_key_data.apply_to_spec(spec)

    def construct_dag_assets_defs(self) -> List[AssetsDefinition]:
        return [
            external_asset_from_spec(dag_data.spec_data.to_asset_spec())
            for dag_data in self.dag_datas.values()
        ]


# History:
# - created
@whitelist_for_serdes
@record
class SerializedTaskHandleData:
    """A record containing known data about a given airflow task handle."""

    migration_state: Optional[bool]
    asset_keys_in_task: AbstractSet[AssetKey]


# History:
# - created
@whitelist_for_serdes
@record
class SerializedAssetKeyScopedAirflowData:
    """Additional data retrieved from airflow that once over the serialization boundary, we can combine with the original asset spec."""

    additional_metadata: Mapping[str, Any]
    additional_tags: Mapping[str, str]

    def apply_to_spec(self, spec: AssetSpec) -> AssetSpec:
        return AssetSpec(
            key=spec.key,
            description=spec.description,
            metadata=merge_dicts(spec.metadata, self.additional_metadata),
            tags=merge_dicts(spec.tags, self.additional_tags),
            deps=spec.deps,
        )
