from typing import Any, Mapping, Optional, Sequence

from dagster import AssetDep, AssetKey, AssetSpec
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


# We serialize dictionaries as json, and json doesn't know how to serialize AssetKeys. So we wrap the mapping
# to be able to serialize this dictionary with "non scalar" keys.
class CacheableSpecMappingSerializer(FieldSerializer):
    def pack(
        self,
        mapping: Mapping[str, "AssetSpecData"],
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


class GenericAssetKeyMappingSerializer(FieldSerializer):
    """Can be used for any mapping with AssetKey keys."""

    def pack(
        self,
        data: Mapping[str, Any],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> JsonSerializableValue:
        return pack_value(SerializableNonScalarKeyMapping(data), whitelist_map, descent_path)

    def unpack(
        self,
        unpacked_value: JsonSerializableValue,
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> PackableValue:
        return unpack_value(unpacked_value, dict, whitelist_map, context)


@whitelist_for_serdes
@record
class AssetSpecData:
    """Serializable data that can be used to construct a fully qualified AssetSpec."""

    asset_key: AssetKey
    description: Optional[str]
    metadata: Mapping[str, Any]
    tags: Mapping[str, str]
    deps: Sequence["CacheableAssetDep"]

    def to_asset_spec(self) -> AssetSpec:
        return AssetSpec(
            key=self.asset_key,
            description=self.description,
            metadata=self.metadata,
            tags=self.tags,
            deps=[AssetDep(asset=dep.asset_key) for dep in self.deps] if self.deps else [],
        )


@whitelist_for_serdes
@record
class ExistingAssetKeyAirflowData:
    """Additional data retrieved from airflow that once over the serialization boundary, we can combine with the original asset spec."""

    asset_key: AssetKey
    additional_metadata: Mapping[str, Any]
    additional_tags: Mapping[str, str]

    def apply_to_spec(self, spec: AssetSpec) -> AssetSpec:
        return AssetSpec(
            key=self.asset_key,
            description=spec.description,
            metadata=merge_dicts(spec.metadata, self.additional_metadata),
            tags=merge_dicts(spec.tags, self.additional_tags),
            deps=spec.deps,
        )


@whitelist_for_serdes
@record
class CacheableAssetDep:
    # A dumbed down version of AssetDep that can be serialized easily to and from a dictionary.
    asset_key: AssetKey

    @staticmethod
    def from_asset_dep(asset_dep: AssetDep) -> "CacheableAssetDep":
        return CacheableAssetDep(asset_key=asset_dep.asset_key)
