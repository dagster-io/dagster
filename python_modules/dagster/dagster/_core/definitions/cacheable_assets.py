from typing import AbstractSet, Any, Mapping, NamedTuple, Optional, Sequence

import dagster._check as check
import dagster._seven as seven
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKeyPrefix
from dagster._core.definitions.metadata import MetadataUserInput
from dagster._serdes import whitelist_for_serdes
from dagster._utils import frozendict, frozenlist, make_readonly_value


@whitelist_for_serdes
class AssetsDefinitionCacheableData(
    NamedTuple(
        "_AssetsDefinitionCacheableData",
        [
            ("keys_by_input_name", Optional[Mapping[str, AssetKey]]),
            ("keys_by_output_name", Optional[Mapping[str, AssetKey]]),
            ("internal_asset_deps", Optional[Mapping[str, AbstractSet[AssetKey]]]),
            ("group_name", Optional[str]),
            ("metadata_by_output_name", Optional[Mapping[str, MetadataUserInput]]),
            ("key_prefix", Optional[CoercibleToAssetKeyPrefix]),
            ("can_subset", bool),
            ("extra_metadata", Optional[Mapping[Any, Any]]),
        ],
    )
):
    """Data representing cacheable metadata about assets, which can be used to generate
    AssetsDefinition objects in other processes
    """

    def __new__(
        cls,
        keys_by_input_name: Optional[Mapping[str, AssetKey]] = None,
        keys_by_output_name: Optional[Mapping[str, AssetKey]] = None,
        internal_asset_deps: Optional[Mapping[str, AbstractSet[AssetKey]]] = None,
        group_name: Optional[str] = None,
        metadata_by_output_name: Optional[Mapping[str, MetadataUserInput]] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        can_subset: bool = False,
        extra_metadata: Optional[Mapping[Any, Any]] = None,
    ):

        keys_by_input_name = check.opt_nullable_mapping_param(
            keys_by_input_name, "keys_by_input_name", key_type=str, value_type=AssetKey
        )

        keys_by_output_name = check.opt_nullable_mapping_param(
            keys_by_output_name, "keys_by_output_name", key_type=str, value_type=AssetKey
        )

        internal_asset_deps = check.opt_nullable_mapping_param(
            internal_asset_deps, "internal_asset_deps", key_type=str, value_type=(set, frozenset)
        )

        metadata_by_output_name = check.opt_nullable_mapping_param(
            metadata_by_output_name, "metadata_by_output_name", key_type=str, value_type=dict
        )

        key_prefix = check.opt_inst_param(key_prefix, "key_prefix", (str, list))

        extra_metadata = check.opt_nullable_mapping_param(extra_metadata, "extra_metadata")
        try:
            # check that the value is JSON serializable
            seven.dumps(extra_metadata)
        except TypeError:
            check.failed("Value for `extra_metadata` is not JSON serializable.")

        return super().__new__(
            cls,
            keys_by_input_name=frozendict(keys_by_input_name) if keys_by_input_name else None,
            keys_by_output_name=frozendict(keys_by_output_name) if keys_by_output_name else None,
            internal_asset_deps=frozendict(
                {k: frozenset(v) for k, v in internal_asset_deps.items()}
            )
            if internal_asset_deps
            else None,
            group_name=check.opt_str_param(group_name, "group_name"),
            metadata_by_output_name=make_readonly_value(metadata_by_output_name)
            if metadata_by_output_name
            else None,
            key_prefix=frozenlist(key_prefix) if key_prefix else None,
            can_subset=check.opt_bool_param(can_subset, "can_subset", default=False),
            extra_metadata=make_readonly_value(extra_metadata) if extra_metadata else None,
        )


class CacheableAssetsDefinition:
    def __init__(self, unique_id: str):
        self._unique_id = unique_id

    @property
    def unique_id(self) -> str:
        return self._unique_id

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        """Returns an object representing cacheable information about assets which are not defined
        in Python code.
        """
        raise NotImplementedError()

    def build_definitions(
        self, data: Sequence[AssetsDefinitionCacheableData]
    ) -> Sequence[AssetsDefinition]:
        """For a given set of AssetsDefinitionMetadata, return a list of AssetsDefinitions"""
        raise NotImplementedError()
