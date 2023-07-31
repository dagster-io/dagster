import collections.abc
import itertools
import warnings
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from typing import (
    Collection,
    Dict,
    List,
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
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.instance import DynamicPartitionsStore
from dagster._serdes import whitelist_for_serdes
from dagster._utils.backcompat import ExperimentalWarning
from dagster._utils.cached_method import cached_method


class UpstreamPartitionsResult(NamedTuple):
    """Represents the result of mapping a PartitionsSubset to the corresponding
    partitions in another PartitionsDefinition.

    partitions_subset (PartitionsSubset): The resulting partitions subset that was
        mapped to. Only contains partitions for existent partitions, filtering out nonexistent partitions.
    required_but_nonexistent_partition_keys (Sequence[str]): A list containing invalid partition keys in to_partitions_def
        that partitions in from_partitions_subset were mapped to.
    """

    partitions_subset: PartitionsSubset
    required_but_nonexistent_partition_keys: Sequence[str]


class PartitionMapping(ABC):
    """Defines a correspondence between the partitions in an asset and the partitions in an asset
    that it depends on.

    Overriding PartitionMapping outside of Dagster is not supported. The abstract methods of this
    class may change at any time.
    """

    @public
    @abstractmethod
    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        """Returns the subset of partition keys in the downstream asset that use the data in the given
        partition key subset of the upstream asset.

        Args:
            upstream_partitions_subset (Union[PartitionKeyRange, PartitionsSubset]): The
                subset of partition keys in the upstream asset.
            downstream_partitions_def (PartitionsDefinition): The partitions definition for the
                downstream asset.
        """

    @public
    @abstractmethod
    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        """Returns a UpstreamPartitionsResult object containing the partition keys the downstream
        partitions subset was mapped to in the upstream partitions definition.

        Valid upstream partitions will be included in UpstreamPartitionsResult.partitions_subset.
        Invalid upstream partitions will be included in UpstreamPartitionsResult.required_but_nonexistent_partition_keys.

        For example, if an upstream asset is time-partitioned and starts in June 2023, and the
        downstream asset is time-partitioned and starts in May 2023, this function would return a
        UpstreamPartitionsResult(PartitionsSubset("2023-06-01"), required_but_nonexistent_partition_keys=["2023-05-01"])
        when downstream_partitions_subset contains 2023-05-01 and 2023-06-01.
        """


@whitelist_for_serdes
class IdentityPartitionMapping(PartitionMapping, NamedTuple("_IdentityPartitionMapping", [])):
    """Expects that the upstream and downstream assets are partitioned in the same way, and maps
    partitions in the downstream asset to the same partition in the upstream asset.
    """

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        if downstream_partitions_subset is None:
            check.failed("downstream asset is not partitioned")

        if downstream_partitions_subset.partitions_def == upstream_partitions_def:
            return UpstreamPartitionsResult(downstream_partitions_subset, [])

        upstream_partition_keys = set(
            upstream_partitions_def.get_partition_keys(
                dynamic_partitions_store=dynamic_partitions_store
            )
        )
        downstream_partition_keys = set(downstream_partitions_subset.get_partition_keys())

        return UpstreamPartitionsResult(
            upstream_partitions_def.subset_with_partition_keys(
                list(upstream_partition_keys & downstream_partition_keys)
            ),
            list(downstream_partition_keys - upstream_partition_keys),
        )

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        if upstream_partitions_subset is None:
            check.failed("upstream asset is not partitioned")

        if upstream_partitions_subset.partitions_def == downstream_partitions_def:
            return upstream_partitions_subset

        upstream_partition_keys = set(upstream_partitions_subset.get_partition_keys())
        downstream_partition_keys = set(
            downstream_partitions_def.get_partition_keys(
                dynamic_partitions_store=dynamic_partitions_store
            )
        )

        return downstream_partitions_def.empty_subset().with_partition_keys(
            list(downstream_partition_keys & upstream_partition_keys)
        )


@whitelist_for_serdes
class AllPartitionMapping(PartitionMapping, NamedTuple("_AllPartitionMapping", [])):
    """Maps every partition in the downstream asset to every partition in the upstream asset.

    Commonly used in the case when the downstream asset is not partitioned, in which the entire
    downstream asset depends on all partitions of the usptream asset.
    """

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        upstream_subset = upstream_partitions_def.subset_with_all_partitions(
            current_time=current_time, dynamic_partitions_store=dynamic_partitions_store
        )
        return UpstreamPartitionsResult(upstream_subset, [])

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        raise NotImplementedError()


@whitelist_for_serdes
class LastPartitionMapping(PartitionMapping, NamedTuple("_LastPartitionMapping", [])):
    """Maps all dependencies to the last partition in the upstream asset.

    Commonly used in the case when the downstream asset is not partitioned, in which the entire
    downstream asset depends on the last partition of the upstream asset.
    """

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        last = upstream_partitions_def.get_last_partition_key(
            current_time=None, dynamic_partitions_store=dynamic_partitions_store
        )

        upstream_subset = upstream_partitions_def.empty_subset()
        if last is not None:
            upstream_subset = upstream_subset.with_partition_keys([last])

        return UpstreamPartitionsResult(upstream_subset, [])

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        raise NotImplementedError()


@whitelist_for_serdes
class SpecificPartitionsPartitionMapping(
    PartitionMapping,
    NamedTuple(
        "_SpecificPartitionsPartitionMapping", [("partition_keys", PublicAttr[Sequence[str]])]
    ),
):
    """Maps to a specific subset of partitions in the upstream asset.

    Example:
        .. code-block:: python

            from dagster import SpecificPartitionsPartitionMapping, StaticPartitionsDefinition, asset

            @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c"]))
            def upstream():
                ...

            @asset(
                ins={
                    "upstream": AssetIn(partition_mapping=SpecificPartitionsPartitionMapping(["a"]))
                }
            )
            def a_downstream(upstream):
                ...
    """

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        return UpstreamPartitionsResult(
            upstream_partitions_def.subset_with_partition_keys(self.partition_keys), []
        )

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        # if any of the partition keys in this partition mapping are contained within the upstream
        # partitions subset, then all partitions of the downstream asset are dependencies
        if any(key in upstream_partitions_subset for key in self.partition_keys):
            return downstream_partitions_def.subset_with_all_partitions(
                dynamic_partitions_store=dynamic_partitions_store
            )
        return downstream_partitions_def.empty_subset()


@experimental
@whitelist_for_serdes
class MultiToSingleDimensionPartitionMapping(
    PartitionMapping,
    NamedTuple(
        "_MultiToSingleDimensionPartitionMapping", [("partition_dimension_name", Optional[str])]
    ),
):
    """Defines a correspondence between an single-dimensional partitions definition
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

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
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
            return UpstreamPartitionsResult(
                upstream_partitions_def.empty_subset().with_partition_keys(
                    self._get_matching_multipartition_keys_for_single_dim_subset(
                        downstream_partitions_subset,
                        cast(MultiPartitionsDefinition, upstream_partitions_def),
                        partition_dimension_name,
                        dynamic_partitions_store,
                    )
                ),
                [],
            )
        else:
            # upstream partitions_def has single dimension
            # downstream partitions def is multipartitioned
            return UpstreamPartitionsResult(
                upstream_partitions_def.empty_subset().with_partition_keys(
                    self._get_single_dim_keys_from_multipartitioned_subset(
                        downstream_partitions_subset, partition_dimension_name
                    )
                ),
                [],
            )

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
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
class DimensionPartitionMapping(
    NamedTuple(
        "_DimensionPartitionMapping",
        [
            ("dimension_name", str),
            ("partition_mapping", PartitionMapping),
        ],
    )
):
    """A helper class for MultiPartitionMapping that defines a partition mapping used to calculate
    the dependent partition keys in the selected downstream MultiPartitions definition dimension.

    Args:
        dimension_name (str): The name of the dimension in the downstream MultiPartitionsDefinition.
        partition_mapping (PartitionMapping): The partition mapping object used to calculate
            the downstream dimension partitions from the upstream dimension partitions and vice versa.
    """

    def __new__(
        cls,
        dimension_name: str,
        partition_mapping: PartitionMapping,
    ):
        return super(DimensionPartitionMapping, cls).__new__(
            cls,
            dimension_name=check.str_param(dimension_name, "dimension_name"),
            partition_mapping=check.inst_param(
                partition_mapping, "partition_mapping", PartitionMapping
            ),
        )


@experimental
@whitelist_for_serdes
class MultiPartitionMapping(
    PartitionMapping,
    NamedTuple(
        "_MultiPartitionMapping",
        [("downstream_mappings_by_upstream_dimension", Mapping[str, DimensionPartitionMapping])],
    ),
):
    """Defines a correspondence between two MultiPartitionsDefinitions.

    Accepts a mapping of upstream dimension name to downstream DimensionPartitionMapping, representing
    the explicit correspondence between the upstream and downstream MultiPartitions dimensions
    and the partition mapping used to calculate the downstream partitions.

    Examples:
        .. code-block:: python

            weekly_abc = MultiPartitionsDefinition(
                {
                    "abc": StaticPartitionsDefinition(["a", "b", "c"]),
                    "weekly": WeeklyPartitionsDefinition("2023-01-01"),
                }
            )
            daily_123 = MultiPartitionsDefinition(
                {
                    "123": StaticPartitionsDefinition(["1", "2", "3"]),
                    "daily": DailyPartitionsDefinition("2023-01-01"),
                }
            )

            MultiPartitionsMapping(
                {
                    "abc": DimensionPartitionMapping(
                        dimension_name="123",
                        partition_mapping=StaticPartitionMapping({"a": "1", "b": "2", "c": "3"}),
                    ),
                    "weekly": DimensionPartitionMapping(
                        dimension_name="daily",
                        partition_mapping=TimeWindowPartitionMapping(),
                    )
                }
            )

    For upstream or downstream dimensions not explicitly defined in the mapping, Dagster will
    assume an `AllPartitionsMapping`, meaning that all upstream partitions in those dimensions
    will be mapped to all downstream partitions in those dimensions.

    Examples:
        .. code-block:: python

            weekly_abc = MultiPartitionsDefinition(
                {
                    "abc": StaticPartitionsDefinition(["a", "b", "c"]),
                    "daily": DailyPartitionsDefinition("2023-01-01"),
                }
            )
            daily_123 = MultiPartitionsDefinition(
                {
                    "123": StaticPartitionsDefinition(["1", "2", "3"]),
                    "daily": DailyPartitionsDefinition("2023-01-01"),
                }
            )

            MultiPartitionsMapping(
                {
                    "daily": DimensionPartitionMapping(
                        dimension_name="daily",
                        partition_mapping=IdentityPartitionMapping(),
                    )
                }
            )

            # Will map `daily_123` partition key {"123": "1", "daily": "2023-01-01"} to the upstream:
            # {"abc": "a", "daily": "2023-01-01"}
            # {"abc": "b", "daily": "2023-01-01"}
            # {"abc": "c", "daily": "2023-01-01"}

    Args:
        downstream_mappings_by_upstream_dimension (Mapping[str, DimensionPartitionMapping]): A
            mapping that defines an explicit correspondence between one dimension of the upstream
            MultiPartitionsDefinition and one dimension of the downstream MultiPartitionsDefinition.
            Maps a string representing upstream dimension name to downstream DimensionPartitionMapping,
            containing the downstream dimension name and partition mapping.
    """

    def __new__(
        cls, downstream_mappings_by_upstream_dimension: Mapping[str, DimensionPartitionMapping]
    ):
        return super(MultiPartitionMapping, cls).__new__(
            cls,
            downstream_mappings_by_upstream_dimension=check.mapping_param(
                downstream_mappings_by_upstream_dimension,
                "downstream_mappings_by_upstream_dimension",
                key_type=str,
                value_type=DimensionPartitionMapping,
            ),
        )

    def _check_all_dimensions_accounted_for(
        self,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: PartitionsDefinition,
    ) -> None:
        if any(
            not isinstance(partitions_def, MultiPartitionsDefinition)
            for partitions_def in (upstream_partitions_def, downstream_partitions_def)
        ):
            check.failed(
                "Both partitions defs provided to a MultiPartitionMapping must be multi-partitioned"
            )

        upstream_dimension_names = {
            dim.name
            for dim in cast(MultiPartitionsDefinition, upstream_partitions_def).partitions_defs
        }
        dimension_names = {
            dim.name
            for dim in cast(MultiPartitionsDefinition, downstream_partitions_def).partitions_defs
        }

        for (
            upstream_dimension_name,
            dimension_mapping,
        ) in self.downstream_mappings_by_upstream_dimension.items():
            if upstream_dimension_name not in upstream_dimension_names:
                check.failed(
                    "Dimension mapping has an upstream dimension name that is not in the upstream "
                    "partitions def"
                )
            if dimension_mapping.dimension_name not in dimension_names:
                check.failed(
                    "Dimension mapping has a downstream dimension name that is not in the"
                    " downstream partitions def"
                )

            upstream_dimension_names.remove(upstream_dimension_name)
            dimension_names.remove(dimension_mapping.dimension_name)

    def _get_dependency_partitions_subset(
        self,
        a_partitions_def: MultiPartitionsDefinition,
        a_partition_keys: Sequence[MultiPartitionKey],
        b_partitions_def: MultiPartitionsDefinition,
        a_upstream_of_b: bool,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
        current_time: Optional[datetime] = None,
    ) -> Union[UpstreamPartitionsResult, PartitionsSubset]:
        """Given two partitions definitions a_partitions_def and b_partitions_def that have a dependency
        relationship (a_upstream_of_b is True if a_partitions_def is upstream of b_partitions_def),
        and a_partition_keys, a list of partition keys in a_partitions_def, returns a list of
        partition keys in the partitions definition b_partitions_def that are
        dependencies of the partition keys in a_partition_keys.
        """
        a_partition_keys_by_dimension = defaultdict(set)
        for partition_key in a_partition_keys:
            for dimension_name, key in partition_key.keys_by_dimension.items():
                a_partition_keys_by_dimension[dimension_name].add(key)

        # Maps the dimension name and key of a partition in a_partitions_def to the list of
        # partition keys in b_partitions_def that are dependencies of that partition
        dep_b_keys_by_a_dim_and_key: Dict[str, Dict[str, List[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        required_but_nonexistent_upstream_partitions = set()

        b_dimension_partitions_def_by_name = {
            dimension.name: dimension.partitions_def
            for dimension in b_partitions_def.partitions_defs
        }

        if a_upstream_of_b:
            # a_partitions_def is upstream of b_partitions_def, so we need to map the
            # dimension names of a_partitions_def to the corresponding dependent dimensions of
            # b_partitions_def
            a_dim_to_dependency_b_dim = {
                upstream_dim: (
                    dimension_mapping.dimension_name,
                    dimension_mapping.partition_mapping,
                )
                for upstream_dim, dimension_mapping in self.downstream_mappings_by_upstream_dimension.items()
            }

            for a_dim_name, keys in a_partition_keys_by_dimension.items():
                if a_dim_name in a_dim_to_dependency_b_dim:
                    (
                        b_dim_name,
                        dimension_mapping,
                    ) = a_dim_to_dependency_b_dim[a_dim_name]
                    a_dimension_partitions_def = a_partitions_def.get_partitions_def_for_dimension(
                        a_dim_name
                    )
                    b_dimension_partitions_def = b_partitions_def.get_partitions_def_for_dimension(
                        b_dim_name
                    )
                    for key in keys:
                        # if downstream dimension mapping exists, for a given key, get the list of
                        # downstream partition keys that are dependencies of that key
                        dep_b_keys_by_a_dim_and_key[a_dim_name][key] = list(
                            dimension_mapping.get_downstream_partitions_for_partitions(
                                a_dimension_partitions_def.empty_subset().with_partition_keys(
                                    [key]
                                ),
                                b_dimension_partitions_def,
                                current_time=current_time,
                                dynamic_partitions_store=dynamic_partitions_store,
                            ).get_partition_keys()
                        )

        else:
            # a_partitions_def is downstream of b_partitions_def, so we need to map the
            # dimension names of a_partitions_def to the corresponding dependency dimensions of
            # b_partitions_def
            a_dim_to_dependency_b_dim = {
                dimension_mapping.dimension_name: (
                    upstream_dim,
                    dimension_mapping.partition_mapping,
                )
                for upstream_dim, dimension_mapping in self.downstream_mappings_by_upstream_dimension.items()
            }

            for a_dim_name, keys in a_partition_keys_by_dimension.items():
                if a_dim_name in a_dim_to_dependency_b_dim:
                    (
                        b_dim_name,
                        partition_mapping,
                    ) = a_dim_to_dependency_b_dim[a_dim_name]
                    a_dimension_partitions_def = a_partitions_def.get_partitions_def_for_dimension(
                        a_dim_name
                    )
                    b_dimension_partitions_def = b_partitions_def.get_partitions_def_for_dimension(
                        b_dim_name
                    )
                    for key in keys:
                        mapped_partitions_result = (
                            partition_mapping.get_upstream_mapped_partitions_result_for_partitions(
                                a_dimension_partitions_def.empty_subset().with_partition_keys(
                                    [key]
                                ),
                                b_dimension_partitions_def,
                                current_time=current_time,
                                dynamic_partitions_store=dynamic_partitions_store,
                            )
                        )
                        dep_b_keys_by_a_dim_and_key[a_dim_name][key] = list(
                            mapped_partitions_result.partitions_subset.get_partition_keys()
                        )
                        required_but_nonexistent_upstream_partitions.update(
                            set(mapped_partitions_result.required_but_nonexistent_partition_keys)
                        )

        b_partition_keys = set()

        mapped_a_dim_names = a_dim_to_dependency_b_dim.keys()
        mapped_b_dim_names = [mapping[0] for mapping in a_dim_to_dependency_b_dim.values()]
        unmapped_b_dim_names = list(
            set(b_dimension_partitions_def_by_name.keys()) - set(mapped_b_dim_names)
        )

        for key in a_partition_keys:
            for b_key_values in itertools.product(
                *(
                    [
                        dep_b_keys_by_a_dim_and_key[dim_name][key.keys_by_dimension[dim_name]]
                        for dim_name in mapped_a_dim_names
                    ]
                ),
                *[
                    b_dimension_partitions_def_by_name[dim_name].get_partition_keys()
                    for dim_name in unmapped_b_dim_names
                ],
            ):
                b_partition_keys.add(
                    MultiPartitionKey(
                        {
                            (mapped_b_dim_names + unmapped_b_dim_names)[i]: key
                            for i, key in enumerate(b_key_values)
                        }
                    )
                )

        mapped_subset = b_partitions_def.empty_subset().with_partition_keys(b_partition_keys)
        if a_upstream_of_b:
            return mapped_subset
        else:
            return UpstreamPartitionsResult(
                mapped_subset,
                required_but_nonexistent_partition_keys=list(
                    required_but_nonexistent_upstream_partitions
                ),
            )

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        if downstream_partitions_subset is None:
            check.failed("downstream asset is not partitioned")

        self._check_all_dimensions_accounted_for(
            upstream_partitions_def,
            downstream_partitions_subset.partitions_def,
        )

        result = self._get_dependency_partitions_subset(
            cast(MultiPartitionsDefinition, downstream_partitions_subset.partitions_def),
            list(
                cast(Sequence[MultiPartitionKey], downstream_partitions_subset.get_partition_keys())
            ),
            cast(MultiPartitionsDefinition, upstream_partitions_def),
            a_upstream_of_b=False,
            dynamic_partitions_store=dynamic_partitions_store,
        )

        if not isinstance(result, UpstreamPartitionsResult):
            check.failed("Expected UpstreamPartitionsResult")

        return result

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        if upstream_partitions_subset is None:
            check.failed("upstream asset is not partitioned")

        self._check_all_dimensions_accounted_for(
            upstream_partitions_subset.partitions_def,
            downstream_partitions_def,
        )

        result = self._get_dependency_partitions_subset(
            cast(MultiPartitionsDefinition, upstream_partitions_subset.partitions_def),
            list(
                cast(Sequence[MultiPartitionKey], upstream_partitions_subset.get_partition_keys())
            ),
            cast(MultiPartitionsDefinition, downstream_partitions_def),
            a_upstream_of_b=True,
            dynamic_partitions_store=dynamic_partitions_store,
        )

        if isinstance(result, UpstreamPartitionsResult):
            check.failed("Expected PartitionsSubset")

        return result


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
    """Define an explicit correspondence between two StaticPartitionsDefinitions.

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
        """Validate that the mapping from upstream to downstream is only defined on upstream keys.
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
        """Validate that the mapping from upstream to downstream only maps to downstream keys."""
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
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        self._check_downstream(downstream_partitions_def=downstream_partitions_def)

        downstream_subset = downstream_partitions_def.empty_subset()
        downstream_keys = set()
        for key in upstream_partitions_subset.get_partition_keys():
            downstream_keys.update(self._mapping[key])
        return downstream_subset.with_partition_keys(downstream_keys)

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        self._check_upstream(upstream_partitions_def=upstream_partitions_def)

        upstream_subset = upstream_partitions_def.empty_subset()
        if downstream_partitions_subset is None:
            return UpstreamPartitionsResult(upstream_subset, [])

        upstream_keys = set()
        for key in downstream_partitions_subset.get_partition_keys():
            upstream_keys.update(self._inverse_mapping[key])

        return UpstreamPartitionsResult(upstream_subset.with_partition_keys(upstream_keys), [])


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
        SpecificPartitionsPartitionMapping,
        StaticPartitionMapping,
        TimeWindowPartitionMapping,
        MultiToSingleDimensionPartitionMapping,
        MultiPartitionMapping,
    )
