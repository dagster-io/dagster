from typing import AbstractSet, Mapping, Optional, Union, overload

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKeyPrefix
from dagster._core.definitions.metadata import (
    MetadataUserInput,
)
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.source_asset import SourceAsset, SourceAssetObserveFunction


@overload
def observable_source_asset(observe_fn: SourceAssetObserveFunction) -> SourceAsset: ...


@overload
def observable_source_asset(
    *,
    name: Optional[str] = ...,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    metadata: Optional[MetadataUserInput] = None,
    io_manager_key: Optional[str] = None,
    io_manager_def: Optional[object] = None,
    description: Optional[str] = None,
    group_name: Optional[str] = None,
    required_resource_keys: Optional[AbstractSet[str]] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    auto_observe_interval_minutes: Optional[float] = None,
) -> "_ObservableSourceAsset": ...


@experimental
def observable_source_asset(
    observe_fn: Optional[SourceAssetObserveFunction] = None,
    *,
    name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    metadata: Optional[MetadataUserInput] = None,
    io_manager_key: Optional[str] = None,
    io_manager_def: Optional[object] = None,
    description: Optional[str] = None,
    group_name: Optional[str] = None,
    required_resource_keys: Optional[AbstractSet[str]] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    auto_observe_interval_minutes: Optional[float] = None,
) -> Union[SourceAsset, "_ObservableSourceAsset"]:
    """Create a `SourceAsset` with an associated observation function.

    The observation function of a source asset is wrapped inside of an op and can be executed as
    part of a job. Each execution generates an `AssetObservation` event associated with the source
    asset. The source asset observation function should return a metadata dictionary that will be
    attached to the `AssetObservation`.

    Args:
        name (Optional[str]): The name of the source asset.  If not provided, defaults to the name of the
            decorated function. The asset's name must be a valid name in dagster (ie only contains
            letters, numbers, and _) and may not contain python reserved keywords.
        key_prefix (Optional[Union[str, Sequence[str]]]): If provided, the source asset's key is the
            concatenation of the key_prefix and the asset's name, which defaults to the name of
            the decorated function. Each item in key_prefix must be a valid name in dagster (ie only
            contains letters, numbers, and _) and may not contain python reserved keywords.
        metadata (Mapping[str, RawMetadataValue]): Metadata associated with the asset.
        io_manager_key (Optional[str]): The key for the IOManager that will be used to load the contents of
            the source asset when it's used as an input to other assets inside a job.
        io_manager_def (Optional[IOManagerDefinition]): (Experimental) The definition of the IOManager that will be used to load the contents of
            the source asset when it's used as an input to other assets inside a job.
        description (Optional[str]): The description of the asset.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. If not provided,
            the name "default" is used.
        required_resource_keys (Optional[Set[str]]): Set of resource keys required by the observe op.
        resource_defs (Optional[Mapping[str, ResourceDefinition]]): (Experimental) resource
            definitions that may be required by the :py:class:`dagster.IOManagerDefinition` provided in
            the `io_manager_def` argument.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the asset.
        auto_observe_interval_minutes (Optional[float]): While the asset daemon is turned on, a run
            of the observation function for this asset will be launched at this interval.
        observe_fn (Optional[SourceAssetObserveFunction]) Observation function for the source asset.
    """
    if observe_fn is not None:
        return _ObservableSourceAsset()(observe_fn)

    return _ObservableSourceAsset(
        name,
        key_prefix,
        metadata,
        io_manager_key,
        io_manager_def,
        description,
        group_name,
        required_resource_keys,
        resource_defs,
        partitions_def,
        auto_observe_interval_minutes,
    )


class _ObservableSourceAsset:
    def __init__(
        self,
        name: Optional[str] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        metadata: Optional[MetadataUserInput] = None,
        io_manager_key: Optional[str] = None,
        io_manager_def: Optional[object] = None,
        description: Optional[str] = None,
        group_name: Optional[str] = None,
        required_resource_keys: Optional[AbstractSet[str]] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        auto_observe_interval_minutes: Optional[float] = None,
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
        self.group_name = group_name
        self.required_resource_keys = required_resource_keys
        self.resource_defs = resource_defs
        self.partitions_def = partitions_def
        self.auto_observe_interval_minutes = auto_observe_interval_minutes

    def __call__(self, observe_fn: SourceAssetObserveFunction) -> SourceAsset:
        source_asset_name = self.name or observe_fn.__name__
        source_asset_key = AssetKey([*self.key_prefix, source_asset_name])

        arg_resource_keys = {arg.name for arg in get_resource_args(observe_fn)}
        decorator_resource_keys = set(self.required_resource_keys or [])
        check.param_invariant(
            len(decorator_resource_keys) == 0 or len(arg_resource_keys) == 0,
            "Cannot specify resource requirements in both @op decorator and as arguments to the"
            " decorated function",
        )
        resolved_resource_keys = decorator_resource_keys.union(arg_resource_keys)

        return SourceAsset(
            key=source_asset_key,
            metadata=self.metadata,
            io_manager_key=self.io_manager_key,
            io_manager_def=self.io_manager_def,
            description=self.description,
            group_name=self.group_name,
            _required_resource_keys=resolved_resource_keys,
            resource_defs=self.resource_defs,
            observe_fn=observe_fn,
            partitions_def=self.partitions_def,
            auto_observe_interval_minutes=self.auto_observe_interval_minutes,
        )
