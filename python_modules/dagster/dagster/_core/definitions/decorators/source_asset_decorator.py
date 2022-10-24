from typing import TYPE_CHECKING, Mapping, Optional, Sequence, Union, overload

from typing_extensions import Protocol, TypeAlias

from dagster._core.definitions.events import AssetKey, AssetObservation, CoercibleToAssetKeyPrefix
from dagster._core.definitions.logical_version import LogicalVersion
from dagster._core.definitions.metadata import (
    MetadataEntry,
    MetadataUserInput,
    PartitionMetadataEntry,
)
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.source_asset import SourceAsset, SourceAssetObserveFunction
from dagster._core.errors import DagsterInvalidObservationError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.storage.io_manager import IOManagerDefinition

from ..decorators.op_decorator import _Op

if TYPE_CHECKING:
    from dagster._core.execution.context.compute import SourceAssetObserveContext


@overload
def observable_source_asset(observe_fn: SourceAssetObserveFunction) -> SourceAsset:
    ...


@overload
def observable_source_asset(
    *,
    name: Optional[str] = ...,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    metadata: Optional[MetadataUserInput] = None,
    io_manager_key: Optional[str] = None,
    io_manager_def: Optional[IOManagerDefinition] = None,
    description: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    _metadata_entries: Optional[Sequence[Union[MetadataEntry, PartitionMetadataEntry]]] = None,
    group_name: Optional[str] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
) -> "_ObservableSourceAsset":
    ...


def observable_source_asset(
    observe_fn: Optional[SourceAssetObserveFunction] = None,
    *,
    name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    metadata: Optional[MetadataUserInput] = None,
    io_manager_key: Optional[str] = None,
    io_manager_def: Optional[IOManagerDefinition] = None,
    description: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    _metadata_entries: Optional[Sequence[Union[MetadataEntry, PartitionMetadataEntry]]] = None,
    group_name: Optional[str] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
) -> Union[SourceAsset, "_ObservableSourceAsset"]:

    if observe_fn is not None:
        return _ObservableSourceAsset()(observe_fn)

    return _ObservableSourceAsset(
        name,
        key_prefix,
        metadata,
        io_manager_key,
        io_manager_def,
        description,
        partitions_def,
        _metadata_entries,
        group_name,
        resource_defs,
    )


class _ObservableSourceAsset:
    def __init__(
        self,
        name: Optional[str] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        metadata: Optional[MetadataUserInput] = None,
        io_manager_key: Optional[str] = None,
        io_manager_def: Optional[IOManagerDefinition] = None,
        description: Optional[str] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        _metadata_entries: Optional[Sequence[Union[MetadataEntry, PartitionMetadataEntry]]] = None,
        group_name: Optional[str] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    ):
        self.name = name
        if isinstance(key_prefix, str):
            key_prefix = [key_prefix]
        elif key_prefix is None:
            key_prefix = []
        self.key_prefix = key_prefix
        self.metadata = metadata
        self.io_manager_key = io_manager_key
        self.io_manager_def = io_manager_def
        self.description = description
        self.partitions_def = partitions_def
        self._metadata_entries = _metadata_entries
        self.group_name = group_name
        self.resource_defs = resource_defs

    def __call__(self, observe_fn: SourceAssetObserveFunction) -> SourceAsset:
        if observe_fn is not None:
            source_asset_name = self.name or observe_fn.__name__
            source_asset_key = AssetKey([*self.key_prefix, source_asset_name])

            def fn(context: OpExecutionContext) -> None:
                raw_observation = observe_fn(context)
                metadata = _raw_observation_to_metadata(raw_observation)
                context.log_event(
                    AssetObservation(
                        asset_key=source_asset_key,
                        metadata=metadata,
                    )
                )

            op = _Op(
                name="__".join(source_asset_key.path).replace("-", "_"),
                description=self.description,
            )(fn)

        return SourceAsset(
            key=source_asset_key,
            metadata=self.metadata,
            io_manager_key=self.io_manager_key,
            io_manager_def=self.io_manager_def,
            description=self.description,
            partitions_def=self.partitions_def,
            _metadata_entries=self._metadata_entries,
            group_name=self.group_name,
            resource_defs=self.resource_defs,
            observe_fn=observe_fn,
        )


def _raw_observation_to_metadata(raw_observation: object) -> MetadataUserInput:
    if isinstance(raw_observation, dict):
        return raw_observation
    elif isinstance(raw_observation, LogicalVersion):
        return {"logical_version": raw_observation}
    else:
        raise DagsterInvalidObservationError(
            "Source asset observe function must return either a metadata dictionary or a `LogicalVersion` instance."
        )
