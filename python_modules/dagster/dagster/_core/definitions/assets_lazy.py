from typing import AbstractSet, Dict, List, Mapping, NamedTuple, Optional

import dagster._check as check
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataUserInput
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
class AssetsDefinitionMetadata(
    NamedTuple(
        "_PipelineSnapshot",
        [
            ("input_keys", AbstractSet[AssetKey]),
            ("output_keys", AbstractSet[AssetKey]),
            ("asset_deps", Optional[Mapping[AssetKey, AbstractSet[AssetKey]]]),
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
        return super().__new__(
            cls,
            input_keys=check.set_param(input_keys, "input_keys", of_type=AssetKey),
            output_keys=check.set_param(output_keys, "output_keys", of_type=AssetKey),
            asset_deps=check.opt_nullable_dict_param(
                asset_deps, "asset_deps", key_type=AssetKey, value_type=set
            ),
            group_names_by_key=check.opt_nullable_dict_param(
                group_names_by_key, "group_names_by_key", key_type=AssetKey, value_type=str
            ),
            metadata_by_key=check.opt_nullable_dict_param(
                metadata_by_key, "metadata_by_key", key_type=AssetKey, value_type=MetadataUserInput
            ),
        )


class LazyAssetsDefinition:
    def __init__(self, unique_id: str):
        self._unique_id = unique_id

    @property
    def unique_id(self) -> str:
        return self._unique_id

    def get_definitions(self, instance) -> List[AssetsDefinition]:
        from dagster import DagsterInstance
        from dagster._core.storage.runs.sql_run_storage import SnapshotType

        # attempt to get cached metadata
        if instance is None:
            instance = DagsterInstance.get()
        # pylint: disable=protected-access
        metadata = instance.run_storage._get_snapshot(self._unique_id)

        # no record exists yet
        if metadata is None:
            metadata = self.generate_metadata()
            # cache this generated metadata
            # pylint: disable=protected-access
            instance.run_storage._add_snapshot(
                snapshot_id=self.unique_id,
                snapshot_obj=metadata,
                snapshot_type=SnapshotType.PIPELINE,
            )
        return self.generate_assets(metadata)

    def generate_metadata(self) -> AssetsDefinitionMetadata:
        """Returns an object representing cacheable information about assets which are not defined
        in Python code.
        """
        raise NotImplementedError()

    def generate_assets(self, metadata: AssetsDefinitionMetadata) -> List[AssetsDefinition]:
        """For a given set of AssetsDefinitionMetadata, return a list of AssetsDefinitions"""
        raise NotImplementedError()
