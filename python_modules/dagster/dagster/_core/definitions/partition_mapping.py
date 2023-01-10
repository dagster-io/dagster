import collections.abc
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Collection, Mapping, NamedTuple, Optional, Union, cast

import dagster._check as check
from dagster._annotations import experimental, public
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionKey,
    MultiPartitionsDefinition,
)
from dagster._core.definitions.partition import (
    PartitionsDefinition,
    PartitionsSubset,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._serdes import whitelist_for_serdes
from dagster._utils.cached_method import cached_method


class PartitionMapping(ABC):
    """Defines a correspondence between the partitions in an asset and the partitions in an asset
    that it depends on.

    Overriding PartitionMapping outside of Dagster is not supported. The abstract methods of this
    class may change at any time.
    """

    @public
    @abstractmethod
    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: Optional[PartitionKeyRange],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        """Returns the range of partition keys in the upstream asset that include data necessary
        to compute the contents of the given partition key range in the downstream asset.

        Args:
            downstream_partition_key_range (PartitionKeyRange): The range of partition keys in the
                downstream asset.
            downstream_partitions_def (PartitionsDefinition): The partitions definition for the
                downstream asset.
            upstream_partitions_def (PartitionsDefinition): The partitions definition for the
                upstream asset.
        """

    @public
    @abstractmethod
    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        """Returns the range of partition keys in the downstream asset that use the data in the given
        partition key range of the upstream asset.

        Args:
            upstream_partition_key_range (PartitionKeyRange): The range of partition keys in the
                upstream asset.
            downstream_partitions_def (PartitionsDefinition): The partitions definition for the
                downstream asset.
            upstream_partitions_def (PartitionsDefinition): The partitions definition for the
                upstream asset.
        """

    @public
    def get_upstream_partitions_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionsSubset:
        """
        Returns the subset of partition keys in the upstream asset that include data necessary
        to compute the contents of the given partition key subset in the downstream asset.

        Args:
            downstream_partitions_subset (Optional[PartitionsSubset]):
                The subset of partition keys in the downstream asset.
            upstream_partitions_def (PartitionsDefinition): The partitions definition for the
                upstream asset.
        """
        upstream_key_ranges = []
        if downstream_partitions_subset is None:
            upstream_key_ranges.append(
                self.get_upstream_partitions_for_partition_range(
                    None, None, upstream_partitions_def
                )
            )
        else:
            for key_range in downstream_partitions_subset.get_partition_key_ranges():
                upstream_key_ranges.append(
                    self.get_upstream_partitions_for_partition_range(
                        key_range,
                        downstream_partitions_subset.partitions_def,
                        upstream_partitions_def,
                    )
                )

        return upstream_partitions_def.empty_subset().with_partition_keys(
            pk
            for upstream_key_range in upstream_key_ranges
            for pk in upstream_partitions_def.get_partition_keys_in_range(upstream_key_range)
        )

    @public
    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: PartitionsDefinition,
    ) -> PartitionsSubset:
        """
        Returns the subset of partition keys in the downstream asset that use the data in the given
        partition key subset of the upstream asset.

        Args:
            upstream_partitions_subset (Union[PartitionKeyRange, PartitionsSubset]): The
                subset of partition keys in the upstream asset.
            downstream_partitions_def (PartitionsDefinition): The partitions definition for the
                downstream asset.
        """
        downstream_key_ranges = []
        for key_range in upstream_partitions_subset.get_partition_key_ranges():
            downstream_key_ranges.append(
                self.get_downstream_partitions_for_partition_range(
                    key_range,
                    downstream_partitions_def,
                    upstream_partitions_subset.partitions_def,
                )
            )

        return downstream_partitions_def.empty_subset().with_partition_keys(
            pk
            for upstream_key_range in downstream_key_ranges
            for pk in downstream_partitions_def.get_partition_keys_in_range(upstream_key_range)
        )


@whitelist_for_serdes
class IdentityPartitionMapping(PartitionMapping, NamedTuple("_IdentityPartitionMapping", [])):
    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: Optional[PartitionKeyRange],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        if downstream_partitions_def is None or downstream_partition_key_range is None:
            check.failed("downstream asset is not partitioned")

        return downstream_partition_key_range

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        return upstream_partition_key_range


@whitelist_for_serdes
class AllPartitionMapping(PartitionMapping, NamedTuple("_AllPartitionMapping", [])):
    def get_upstream_partitions_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionsSubset:
        first = upstream_partitions_def.get_first_partition_key()
        last = upstream_partitions_def.get_last_partition_key()

        empty_subset = upstream_partitions_def.empty_subset()
        if first is not None and last is not None:
            return empty_subset.with_partition_key_range(PartitionKeyRange(first, last))
        else:
            return empty_subset

    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: Optional[PartitionKeyRange],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        raise NotImplementedError()

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        raise NotImplementedError()


@whitelist_for_serdes
class LastPartitionMapping(PartitionMapping, NamedTuple("_LastPartitionMapping", [])):
    def get_upstream_partitions_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionsSubset:
        last = upstream_partitions_def.get_last_partition_key()

        empty_subset = upstream_partitions_def.empty_subset()
        if last is not None:
            return empty_subset.with_partition_keys([last])
        else:
            return empty_subset

    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: Optional[PartitionKeyRange],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        raise NotImplementedError()

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        raise NotImplementedError()


@experimental
class SingleDimensionDependencyMapping(PartitionMapping):
    """
    Defines a correspondence between an upstream single-dimensional partitions definition
    and a downstream MultiPartitionsDefinition. The upstream partitions definition must be
    a dimension of the downstream MultiPartitionsDefinition.

    For an upstream partition key X, this partition mapping assumes that any downstream
    multi-partition key with X in the selected dimension is a downstream dependency.

    Args:
        partition_dimension_name (str): The name of the partition dimension in the downstream
            MultiPartitionsDefinition that matches the upstream partitions definition.
    """

    def __init__(self, partition_dimension_name: str):
        self.partition_dimension_name = partition_dimension_name

    def _check_upstream_partitions_def_equals_selected_dimension(
        self,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: MultiPartitionsDefinition,
    ) -> None:
        matching_dimensions = [
            partitions_def
            for partitions_def in downstream_partitions_def.partitions_defs
            if partitions_def.name == self.partition_dimension_name
        ]
        if len(matching_dimensions) != 1:
            check.failed(f"Partition dimension '{self.partition_dimension_name}' not found")
        matching_dimension_def = next(iter(matching_dimensions))

        if upstream_partitions_def != matching_dimension_def.partitions_def:
            check.failed(
                "The upstream partitions definition does not have the same partitions definition "
                f"as dimension {matching_dimension_def.name}"
            )

    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: Optional[PartitionKeyRange],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        raise NotImplementedError()

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        raise NotImplementedError()

    def get_upstream_partitions_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionsSubset:
        if downstream_partitions_subset is None or not isinstance(
            downstream_partitions_subset.partitions_def, MultiPartitionsDefinition
        ):
            check.failed("downstream asset is not partitioned")

        self._check_upstream_partitions_def_equals_selected_dimension(
            upstream_partitions_def, downstream_partitions_subset.partitions_def
        )
        upstream_partitions = set()
        for partition_key in downstream_partitions_subset.get_partition_keys():
            if not isinstance(partition_key, MultiPartitionKey):
                check.failed(
                    "Partition keys in downstream partition key subset must be MultiPartitionKeys"
                )
            upstream_partitions.add(partition_key.keys_by_dimension[self.partition_dimension_name])
        return upstream_partitions_def.empty_subset().with_partition_keys(upstream_partitions)

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: PartitionsDefinition,
    ) -> PartitionsSubset:
        if downstream_partitions_def is None or not isinstance(
            downstream_partitions_def, MultiPartitionsDefinition
        ):
            check.failed("downstream asset is not multi-partitioned")

        self._check_upstream_partitions_def_equals_selected_dimension(
            upstream_partitions_subset.partitions_def, downstream_partitions_def
        )

        upstream_keys = list(upstream_partitions_subset.get_partition_keys())

        matching_keys = []
        for key in downstream_partitions_def.get_partition_keys():
            key = cast(MultiPartitionKey, key)
            if key.keys_by_dimension[self.partition_dimension_name] in upstream_keys:
                matching_keys.append(key)

        return downstream_partitions_def.empty_subset().with_partition_keys(set(matching_keys))


class StaticPartitionMapping(PartitionMapping):
    """
    Define an explicit correspondence between two StaticPartitionsDefinitions.

    Args:
        downstream_partition_keys_by_upstream_partition_key (Dict[str, str | Collection[str]]):
          The single or multi-valued correspondence from upstream keys to downstream keys.
    """

    def __init__(
        self,
        downstream_partition_keys_by_upstream_partition_key: Mapping[
            str, Union[str, Collection[str]]
        ],
    ):
        check.mapping_param(
            downstream_partition_keys_by_upstream_partition_key,
            "downstream_partition_keys_by_upstream_partition_key",
            key_type=str,
            value_type=(str, collections.abc.Collection),
        )

        # cache forward and reverse mappings
        self._mapping = defaultdict(set)
        for (
            upstream_key,
            downstream_keys,
        ) in downstream_partition_keys_by_upstream_partition_key.items():
            self._mapping[upstream_key] = (
                {downstream_keys} if isinstance(downstream_keys, str) else set(downstream_keys)
            )

        self._inverse_mapping = defaultdict(set)
        for upstream_key, downstream_keys in self._mapping.items():
            for downstream_key in downstream_keys:
                self._inverse_mapping[downstream_key].add(upstream_key)

    @cached_method
    def _check_upstream(self, *, upstream_partitions_def: PartitionsDefinition):
        """
        validate that the mapping from upstream to downstream is only defined on upstream keys
        """
        check.inst(
            upstream_partitions_def,
            StaticPartitionsDefinition,
            "StaticPartitionMapping can only be defined between two StaticPartitionsDefinitions",
        )
        upstream_keys = upstream_partitions_def.get_partition_keys()
        extra_keys = set(self._mapping.keys()).difference(upstream_keys)
        if extra_keys:
            raise ValueError(
                f"mapping source partitions not in the upstream partitions definition: {extra_keys}"
            )

    @cached_method
    def _check_downstream(self, *, downstream_partitions_def: PartitionsDefinition):
        """
        validate that the mapping from upstream to downstream only maps to downstream keys
        """
        check.inst(
            downstream_partitions_def,
            StaticPartitionsDefinition,
            "StaticPartitionMapping can only be defined between two StaticPartitionsDefinitions",
        )
        downstream_keys = downstream_partitions_def.get_partition_keys()
        extra_keys = set(self._inverse_mapping.keys()).difference(downstream_keys)
        if extra_keys:
            raise ValueError(
                "mapping target partitions not in the downstream partitions definition:"
                f" {extra_keys}"
            )

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: PartitionsDefinition,
    ) -> PartitionsSubset:
        self._check_downstream(downstream_partitions_def=downstream_partitions_def)

        downstream_subset = downstream_partitions_def.empty_subset()
        downstream_keys = set()
        for key in upstream_partitions_subset.get_partition_keys():
            downstream_keys.update(self._mapping[key])
        return downstream_subset.with_partition_keys(downstream_keys)

    def get_upstream_partitions_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionsSubset:
        self._check_upstream(upstream_partitions_def=upstream_partitions_def)

        upstream_subset = upstream_partitions_def.empty_subset()
        if downstream_partitions_subset is None:
            return upstream_subset

        upstream_keys = set()
        for key in downstream_partitions_subset.get_partition_keys():
            upstream_keys.update(self._inverse_mapping[key])

        return upstream_subset.with_partition_keys(upstream_keys)

    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: Optional[PartitionKeyRange],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        raise NotImplementedError()

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        raise NotImplementedError()


def infer_partition_mapping(
    partition_mapping: Optional[PartitionMapping], partitions_def: Optional[PartitionsDefinition]
) -> PartitionMapping:
    if partition_mapping is not None:
        return partition_mapping
    elif partitions_def is not None:
        return partitions_def.get_default_partition_mapping()
    else:
        return AllPartitionMapping()


def get_builtin_partition_mapping_types():
    from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping

    return (
        AllPartitionMapping,
        IdentityPartitionMapping,
        LastPartitionMapping,
        StaticPartitionMapping,
        TimeWindowPartitionMapping,
    )
