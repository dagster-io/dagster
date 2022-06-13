from typing import Dict, Iterator, Mapping, NamedTuple, Optional, Sequence, Union, cast

import dagster._check as check
from dagster.core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster.core.definitions.metadata import (
    MetadataEntry,
    MetadataMapping,
    MetadataUserInput,
    PartitionMetadataEntry,
    normalize_metadata,
)
from dagster.core.definitions.partition import PartitionsDefinition
from dagster.core.definitions.resource_definition import ResourceDefinition
from dagster.core.definitions.resource_requirement import (
    ResourceAddable,
    ResourceRequirement,
    SourceAssetIOManagerRequirement,
    get_resource_key_conflicts,
)
from dagster.core.definitions.utils import DEFAULT_GROUP_NAME, validate_group_name
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvalidInvocationError
from dagster.core.storage.io_manager import IOManagerDefinition
from dagster.utils import merge_dicts


class SourceAsset(
    NamedTuple(
        "_SourceAsset",
        [
            ("key", AssetKey),
            ("metadata_entries", Sequence[Union[MetadataEntry, PartitionMetadataEntry]]),
            ("io_manager_key", Optional[str]),
            ("description", Optional[str]),
            ("partitions_def", Optional[PartitionsDefinition]),
            ("group_name", str),
            ("resource_defs", Dict[str, ResourceDefinition]),
        ],
    ),
    ResourceAddable,
):
    """A SourceAsset represents an asset that will be loaded by (but not updated by) Dagster.

    Attributes:
        key (Union[AssetKey, Sequence[str], str]): The key of the asset.
        metadata_entries (List[MetadataEntry]): Metadata associated with the asset.
        io_manager_key (Optional[str]): The key for the IOManager that will be used to load the contents of
            the asset when it's used as an input to other assets inside a job.
        io_manager_def (Optional[IOManagerDefinition]): The definition of the IOManager that will be used to load the contents of
            the asset when it's used as an input to other assets inside a job.
        description (Optional[str]): The description of the asset.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the asset.
    """

    def __new__(
        cls,
        key: CoercibleToAssetKey,
        metadata: Optional[MetadataUserInput] = None,
        io_manager_key: Optional[str] = None,
        io_manager_def: Optional[IOManagerDefinition] = None,
        description: Optional[str] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        _metadata_entries: Optional[Sequence[Union[MetadataEntry, PartitionMetadataEntry]]] = None,
        group_name: Optional[str] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        # Add additional fields to with_resources and with_group below
    ):

        key = AssetKey.from_coerceable(key)
        metadata = check.opt_dict_param(metadata, "metadata", key_type=str)
        metadata_entries = _metadata_entries or normalize_metadata(metadata, [], allow_invalid=True)
        resource_defs = dict(check.opt_mapping_param(resource_defs, "resource_defs"))
        io_manager_def = check.opt_inst_param(io_manager_def, "io_manager_def", IOManagerDefinition)
        if io_manager_def:
            if not io_manager_key:
                source_asset_path = "__".join(key.path)
                io_manager_key = f"{source_asset_path}__io_manager"

            if io_manager_key in resource_defs and resource_defs[io_manager_key] != io_manager_def:
                raise DagsterInvalidDefinitionError(
                    f"Provided conflicting definitions for io manager key '{io_manager_key}'. Please provide only one definition per key."
                )

            resource_defs[io_manager_key] = io_manager_def

        return super().__new__(
            cls,
            key=key,
            metadata_entries=metadata_entries,
            io_manager_key=check.opt_str_param(io_manager_key, "io_manager_key"),
            description=check.opt_str_param(description, "description"),
            partitions_def=check.opt_inst_param(
                partitions_def, "partitions_def", PartitionsDefinition
            ),
            group_name=validate_group_name(group_name),
            resource_defs=resource_defs,
        )

    @property
    def metadata(self) -> MetadataMapping:
        # PartitionMetadataEntry (unstable API) case is unhandled
        return {entry.label: entry.entry_data for entry in self.metadata_entries}  # type: ignore

    def get_io_manager_key(self) -> str:
        return self.io_manager_key or "io_manager"

    @property
    def io_manager_def(self) -> Optional[IOManagerDefinition]:
        io_manager_key = self.get_io_manager_key()
        return cast(
            Optional[IOManagerDefinition],
            self.resource_defs.get(io_manager_key) if io_manager_key else None,
        )

    def with_resources(self, resource_defs) -> "SourceAsset":
        from dagster.core.execution.resources_init import get_transitive_required_resource_keys

        overlapping_keys = get_resource_key_conflicts(self.resource_defs, resource_defs)
        if overlapping_keys:
            raise DagsterInvalidInvocationError(
                f"SourceAsset with key {self.key} has conflicting resource "
                "definitions with provided resources for the following keys: "
                f"{sorted(list(overlapping_keys))}. Either remove the existing "
                "resources from the asset or change the resource keys so that "
                "they don't overlap."
            )

        merged_resource_defs = merge_dicts(resource_defs, self.resource_defs)

        io_manager_def = merged_resource_defs.get(self.get_io_manager_key())
        if not io_manager_def and self.get_io_manager_key() != "io_manager":
            raise DagsterInvalidDefinitionError(
                f"SourceAsset with asset key {self.key} requires IO manager with key '{self.get_io_manager_key()}', but none was provided."
            )
        relevant_keys = get_transitive_required_resource_keys(
            {self.get_io_manager_key()}, merged_resource_defs
        )

        relevant_resource_defs = {
            key: resource_def
            for key, resource_def in merged_resource_defs.items()
            if key in relevant_keys
        }

        io_manager_key = (
            self.get_io_manager_key() if self.get_io_manager_key() != "io_manager" else None
        )
        return SourceAsset(
            key=self.key,
            io_manager_key=io_manager_key,
            description=self.description,
            partitions_def=self.partitions_def,
            _metadata_entries=self.metadata_entries,
            resource_defs=relevant_resource_defs,
            group_name=self.group_name,
        )

    def with_group_name(self, group_name: str) -> "SourceAsset":
        if self.group_name != DEFAULT_GROUP_NAME:
            raise DagsterInvalidDefinitionError(
                f"A group name has already been provided to source asset {self.key.to_user_string()}"
            )

        return SourceAsset(
            key=self.key,
            _metadata_entries=self.metadata_entries,
            io_manager_key=self.io_manager_key,
            io_manager_def=self.io_manager_def,
            description=self.description,
            partitions_def=self.partitions_def,
            group_name=group_name,
            resource_defs=self.resource_defs,
        )

    def get_resource_requirements(self) -> Iterator[ResourceRequirement]:
        SourceAssetIOManagerRequirement(
            key=self.get_io_manager_key(), asset_key=self.key.to_string()
        )
        for source_key, resource_def in self.resource_defs.items():
            yield from resource_def.get_resource_requirements(outer_context=source_key)
