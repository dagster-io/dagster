import collections.abc
import warnings
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import (
    Collection,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

import dagster._check as check
from dagster._annotations import PublicAttr, experimental, public
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
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.instance import DynamicPartitionsStore
from dagster._serdes import whitelist_for_serdes
from dagster._utils.backcompat import ExperimentalWarning
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
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
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
            for key_range in downstream_partitions_subset.get_partition_key_ranges(
                dynamic_partitions_store=dynamic_partitions_store
            ):
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
            for pk in upstream_partitions_def.get_partition_keys_in_range(
                upstream_key_range, dynamic_partitions_store=dynamic_partitions_store
            )
        )

    @public
    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: PartitionsDefinition,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
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
        for key_range in upstream_partitions_subset.get_partition_key_ranges(
            dynamic_partitions_store=dynamic_partitions_store
        ):
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
            for pk in downstream_partitions_def.get_partition_keys_in_range(
                upstream_key_range, dynamic_partitions_store=dynamic_partitions_store
            )
        )


@whitelist_for_serdes
class IdentityPartitionMapping(PartitionMapping, NamedTuple("_IdentityPartitionMapping", [])):
    """
    Expects that the upstream and downstream assets are partitioned in the same way, and maps
    partitions in the downstream asset to the same partition in the upstream asset.
    """

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
    """
    Maps every partition in the downstream asset to every partition in the upstream asset.

    Commonly used in the case when the downstream asset is not partitioned, in which the entire
    downstream asset depends on all partitions of the usptream asset.
    """

    def get_upstream_partitions_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        first = upstream_partitions_def.get_first_partition_key(
            current_time=None, dynamic_partitions_store=dynamic_partitions_store
        )
        last = upstream_partitions_def.get_last_partition_key(
            current_time=None, dynamic_partitions_store=dynamic_partitions_store
        )

        empty_subset = upstream_partitions_def.empty_subset()
        if first is not None and last is not None:
            return empty_subset.with_partition_key_range(
                PartitionKeyRange(first, last), dynamic_partitions_store=dynamic_partitions_store
            )
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
    """
    Maps all dependencies to the last partition in the upstream asset.

    Commonly used in the case when the downstream asset is not partitioned, in which the entire
    downstream asset depends on the last partition of the upstream asset.
    """

    def get_upstream_partitions_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        last = upstream_partitions_def.get_last_partition_key(
            current_time=None, dynamic_partitions_store=dynamic_partitions_store
        )

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
@whitelist_for_serdes
class MultiToSingleDimensionPartitionMapping(
    PartitionMapping,
    NamedTuple(
        "_MultiToSingleDimensionPartitionMapping", [("partition_dimension_name", Optional[str])]
    ),
):
    """
    Defines a correspondence between an single-dimensional partitions definition
    and a MultiPartitionsDefinition. The single-dimensional partitions definition must be
    a dimension of the MultiPartitionsDefinition.

    This class handles the case where the upstream asset is multipartitioned and the
    downstream asset is single dimensional, and vice versa.

    For a partition key X, this partition mapping assumes that any multi-partition key with
    X in the selected dimension is a dependency.

    Args:
        partition_dimension_name (Optional[str]): The name of the partition dimension in the
            MultiPartitionsDefinition that matches the single-dimension partitions definition.
    """

    def __new__(cls, partition_dimension_name: Optional[str] = None):
        return super(MultiToSingleDimensionPartitionMapping, cls).__new__(
            cls,
            partition_dimension_name=check.opt_str_param(
                partition_dimension_name, "partition_dimension_name"
            ),
        )

    def _check_partitions_defs_and_get_partition_dimension_name(
        self,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: PartitionsDefinition,
    ) -> Tuple[PartitionsDefinition, PartitionsDefinition, str]:
        if not _can_infer_single_to_multi_partition_mapping(
            upstream_partitions_def, downstream_partitions_def
        ):
            check.failed(
                "This partition mapping defines a relationship between a multipartitioned and"
                " single dimensional asset. The single dimensional partitions definition must be a"
                " dimension of the MultiPartitionsDefinition."
            )

        multipartitions_def = cast(
            MultiPartitionsDefinition,
            (
                upstream_partitions_def
                if isinstance(upstream_partitions_def, MultiPartitionsDefinition)
                else downstream_partitions_def
            ),
        )

        single_dimension_partitions_def = (
            upstream_partitions_def
            if not isinstance(upstream_partitions_def, MultiPartitionsDefinition)
            else downstream_partitions_def
        )

        if self.partition_dimension_name is None:
            dimension_partitions_defs = [
                partitions_def.partitions_def
                for partitions_def in multipartitions_def.partitions_defs
            ]
            if len(set(dimension_partitions_defs)) != len(dimension_partitions_defs):
                check.failed(
                    "Partition dimension name must be specified on the "
                    "MultiToSingleDimensionPartitionMapping object when dimensions of a"
                    " MultiPartitions definition share the same partitions definition."
                )
            matching_dimension_defs = [
                dimension_def
                for dimension_def in multipartitions_def.partitions_defs
                if dimension_def.partitions_def == single_dimension_partitions_def
            ]
            if len(matching_dimension_defs) != 1:
                check.failed(
                    "No partition dimension name was specified and no dimensions of the"
                    " MultiPartitionsDefinition match the single dimension"
                    " PartitionsDefinition."
                )
            partition_dimension_name = next(iter(matching_dimension_defs)).name
        else:
            matching_dimensions = [
                partitions_def
                for partitions_def in multipartitions_def.partitions_defs
                if partitions_def.name == self.partition_dimension_name
            ]
            if len(matching_dimensions) != 1:
                check.failed(f"Partition dimension '{self.partition_dimension_name}' not found")
            matching_dimension_def = next(iter(matching_dimensions))

            if single_dimension_partitions_def != matching_dimension_def.partitions_def:
                check.failed(
                    "The single dimension partitions definition does not have the same partitions"
                    f" definition as dimension {matching_dimension_def.name}"
                )
            partition_dimension_name = self.partition_dimension_name

        return (upstream_partitions_def, downstream_partitions_def, partition_dimension_name)

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

    def _get_matching_multipartition_keys_for_single_dim_subset(
        self,
        partitions_subset: PartitionsSubset,
        multipartitions_def: MultiPartitionsDefinition,
        partition_dimension_name: str,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Sequence[str]:
        matching_keys = []
        for key in multipartitions_def.get_partition_keys(
            current_time=None, dynamic_partitions_store=dynamic_partitions_store
        ):
            key = cast(MultiPartitionKey, key)
            if (
                key.keys_by_dimension[partition_dimension_name]
                in partitions_subset.get_partition_keys()
            ):
                matching_keys.append(key)
        return matching_keys

    def _get_single_dim_keys_from_multipartitioned_subset(
        self,
        partitions_subset: PartitionsSubset,
        partition_dimension_name: str,
    ) -> Set[str]:
        upstream_partitions = set()
        for partition_key in partitions_subset.get_partition_keys():
            if not isinstance(partition_key, MultiPartitionKey):
                check.failed("Partition keys in subset must be MultiPartitionKeys")
            upstream_partitions.add(partition_key.keys_by_dimension[partition_dimension_name])
        return upstream_partitions

    def get_upstream_partitions_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        if downstream_partitions_subset is None:
            check.failed("downstream asset is not partitioned")

        (
            upstream_partitions_def,
            _,
            partition_dimension_name,
        ) = self._check_partitions_defs_and_get_partition_dimension_name(
            upstream_partitions_def, downstream_partitions_subset.partitions_def
        )

        if isinstance(upstream_partitions_def, MultiPartitionsDefinition):
            # upstream partitions def is multipartitioned
            # downstream partitions def has single dimension
            return upstream_partitions_def.empty_subset().with_partition_keys(
                self._get_matching_multipartition_keys_for_single_dim_subset(
                    downstream_partitions_subset,
                    cast(MultiPartitionsDefinition, upstream_partitions_def),
                    partition_dimension_name,
                    dynamic_partitions_store,
                )
            )
        else:
            # upstream partitions_def has single dimension
            # downstream partitions def is multipartitioned
            return upstream_partitions_def.empty_subset().with_partition_keys(
                self._get_single_dim_keys_from_multipartitioned_subset(
                    downstream_partitions_subset, partition_dimension_name
                )
            )

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: PartitionsDefinition,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        if downstream_partitions_def is None:
            check.failed("downstream asset is not multi-partitioned")

        (
            _,
            downstream_partitions_def,
            partition_dimension_name,
        ) = self._check_partitions_defs_and_get_partition_dimension_name(
            upstream_partitions_subset.partitions_def, downstream_partitions_def
        )

        if isinstance(downstream_partitions_def, MultiPartitionsDefinition):
            # upstream partitions def has single dimension
            # downstream partitions def is multipartitioned
            return downstream_partitions_def.empty_subset().with_partition_keys(
                self._get_matching_multipartition_keys_for_single_dim_subset(
                    upstream_partitions_subset,
                    downstream_partitions_def,
                    partition_dimension_name,
                    dynamic_partitions_store,
                )
            )
        else:
            # upstream partitions def is multipartitioned
            # downstream partitions def has single dimension
            return downstream_partitions_def.empty_subset().with_partition_keys(
                self._get_single_dim_keys_from_multipartitioned_subset(
                    upstream_partitions_subset, partition_dimension_name
                )
            )


@whitelist_for_serdes
class StaticPartitionMapping(
    PartitionMapping,
    NamedTuple(
        "_StaticPartitionMapping",
        [
            (
                "downstream_partition_keys_by_upstream_partition_key",
                PublicAttr[Mapping[str, Union[str, Collection[str]]]],
            )
        ],
    ),
):
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
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
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
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
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


def _can_infer_single_to_multi_partition_mapping(
    upstream_partitions_def: PartitionsDefinition, downstream_partitions_def: PartitionsDefinition
) -> bool:
    multipartitions_defs = [
        partitions_def
        for partitions_def in [upstream_partitions_def, downstream_partitions_def]
        if isinstance(partitions_def, MultiPartitionsDefinition)
    ]

    if len(multipartitions_defs) != 1:
        return False

    multipartitions_def = cast(MultiPartitionsDefinition, next(iter(multipartitions_defs)))

    single_dimension_partitions_def = next(
        iter(
            {
                upstream_partitions_def,
                downstream_partitions_def,
            }
            - set(multipartitions_defs)
        )
    )

    matching_dimension_defs = [
        dimension_def
        for dimension_def in multipartitions_def.partitions_defs
        if dimension_def.partitions_def == single_dimension_partitions_def
    ]

    if not matching_dimension_defs:
        return False

    return True


def infer_partition_mapping(
    partition_mapping: Optional[PartitionMapping],
    downstream_partitions_def: Optional[PartitionsDefinition],
    upstream_partitions_def: Optional[PartitionsDefinition],
) -> PartitionMapping:
    from .time_window_partition_mapping import TimeWindowPartitionMapping

    if partition_mapping is not None:
        return partition_mapping
    elif upstream_partitions_def and downstream_partitions_def:
        if _can_infer_single_to_multi_partition_mapping(
            upstream_partitions_def, downstream_partitions_def
        ):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=ExperimentalWarning)
                return MultiToSingleDimensionPartitionMapping()
        elif isinstance(upstream_partitions_def, TimeWindowPartitionsDefinition) and isinstance(
            downstream_partitions_def, TimeWindowPartitionsDefinition
        ):
            return TimeWindowPartitionMapping()
        else:
            return IdentityPartitionMapping()
    else:
        return AllPartitionMapping()


def get_builtin_partition_mapping_types() -> Tuple[Type[PartitionMapping], ...]:
    from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping

    return (
        AllPartitionMapping,
        IdentityPartitionMapping,
        LastPartitionMapping,
        StaticPartitionMapping,
        TimeWindowPartitionMapping,
        MultiToSingleDimensionPartitionMapping,
    )
