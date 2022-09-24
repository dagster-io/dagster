from typing import AbstractSet, Dict, List, Mapping, NamedTuple, Optional, FrozenSet

import dagster._check as check
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataUserInput
from dagster._serdes import whitelist_for_serdes
from dagster._utils import frozendict


@whitelist_for_serdes
class AssetsDefinitionMetadata(
    NamedTuple(
        "_PipelineSnapshot",
        [
            ("input_keys", FrozenSet[AssetKey]),
            ("output_keys", FrozenSet[AssetKey]),
            ("asset_deps", Optional[Mapping[AssetKey, FrozenSet[AssetKey]]]),
            ("group_names_by_key", Optional[Mapping[AssetKey, str]]),
            ("metadata_by_key", Optional[Mapping[AssetKey, MetadataUserInput]]),
        ],
    )
):
    """Data representing cacheable metadata about assets, which can be used to generate
    AssetsDefinition objects in other processes
    """

    def __new__(
        cls,
        input_keys: AbstractSet[AssetKey],
        output_keys: AbstractSet[AssetKey],
        asset_deps: Optional[Dict[AssetKey, AbstractSet[AssetKey]]] = None,
        group_names_by_key: Optional[Dict[AssetKey, str]] = None,
        metadata_by_key: Optional[Dict[AssetKey, MetadataUserInput]] = None,
    ):
        asset_deps = check.opt_nullable_dict_param(
            asset_deps, "asset_deps", key_type=AssetKey, value_type=set
        )
        group_names_by_key = check.opt_nullable_dict_param(
            group_names_by_key, "group_names_by_key", key_type=AssetKey, value_type=str
        )
        metadata_by_key = check.opt_nullable_dict_param(
            metadata_by_key,
            "metadata_by_key",
            key_type=AssetKey,
            value_type=MetadataUserInput,
        )
        return super().__new__(
            cls,
            input_keys=frozenset(check.set_param(input_keys, "input_keys", of_type=AssetKey)),
            output_keys=frozenset(check.set_param(output_keys, "output_keys", of_type=AssetKey)),
            asset_deps=frozendict({k: frozenset(v) for k, v in asset_deps.items()})
            if asset_deps
            else None,
            group_names_by_key=frozendict(group_names_by_key) if group_names_by_key else None,
            metadata_by_key=frozendict(metadata_by_key) if metadata_by_key else None,
        )


class LazyAssetsDefinition:
    def __init__(self, unique_id: str):
        self._unique_id = unique_id

    @property
    def unique_id(self) -> str:
        return self._unique_id

    def get_metadata(self) -> AssetsDefinitionMetadata:
        """Returns an object representing cacheable information about assets which are not defined
        in Python code.
        """
        raise NotImplementedError()

    def get_assets(self, metadata: AssetsDefinitionMetadata) -> List[AssetsDefinition]:
        """For a given set of AssetsDefinitionMetadata, return a list of AssetsDefinitions"""
        raise NotImplementedError()
