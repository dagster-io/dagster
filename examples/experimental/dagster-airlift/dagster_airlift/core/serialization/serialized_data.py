from typing import AbstractSet, Any, Mapping, Optional, Sequence

from dagster import AssetCheckKey, AssetDep, AssetKey, AssetSpec
from dagster._record import record
from dagster._serdes import whitelist_for_serdes
from dagster._serdes.serdes import (
    FieldSerializer,
    JsonSerializableValue,
    PackableValue,
    SerializableNonScalarKeyMapping,
    UnpackContext,
    WhitelistMap,
    pack_value,
    unpack_value,
)
from dagster._utils.merger import merge_dicts


###################################################################################################
# A generic serializer that can be used for any mapping with non-scalar (but still serializable) keys.
# We should add this to the core framework.
###################################################################################################
class GenericNonScalarKeyMappingSerializer(FieldSerializer):
    """A serializer that can be used for any mapping with non-scalar (but still serializable) keys."""

    def pack(
        self,
        mapping: Mapping[str, "SerializedAssetSpecData"],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> JsonSerializableValue:
        return pack_value(SerializableNonScalarKeyMapping(mapping), whitelist_map, descent_path)

    def unpack(
        self,
        unpacked_value: JsonSerializableValue,
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> PackableValue:
        return unpack_value(unpacked_value, dict, whitelist_map, context)


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
# Serializable data that will be cached to avoid repeated calls to the Airflow API, and to avoid
# repeated scans of passed-in Definitions objects.
###################################################################################################
# History:
# - created
@whitelist_for_serdes(
    field_serializers={
        "existing_asset_data": GenericNonScalarKeyMappingSerializer,
    }
)
@record
class SerializedAirflowDefinitionsData:
    existing_asset_data: Mapping[AssetKey, "SerializedAssetKeyScopedData"]
    dag_datas: Mapping[str, "SerializedDagData"]
    asset_key_topological_ordering: Sequence[AssetKey]


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


# History:
# - created
@whitelist_for_serdes
@record
class SerializedTaskHandleData:
    """A record containing known data about a given airflow task handle."""

    migration_state: Optional[bool]
    asset_keys_in_task: AbstractSet[AssetKey]


###################################################################################################
# Serialized data that scopes to a given asset key.
###################################################################################################
# History:
# - created
@whitelist_for_serdes
@record
class SerializedAssetKeyScopedData:
    """All pre-computed data scoped to a given asset key."""

    existing_key_data: Optional["SerializedAssetKeyScopedAirflowData"]
    asset_graph_data: "SerializedAssetKeyScopedAssetGraphData"


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


# History:
# - created
@whitelist_for_serdes
@record
class SerializedAssetKeyScopedAssetGraphData:
    """A record of asset graph data scoped to a particular asset key."""

    upstreams: AbstractSet[AssetKey]
    downstreams: AbstractSet[AssetKey]
    check_keys: AbstractSet[AssetCheckKey]
