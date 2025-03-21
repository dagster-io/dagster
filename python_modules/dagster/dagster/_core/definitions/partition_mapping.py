import collections.abc
import itertools
import warnings
from abc import ABC, abstractmethod, abstractproperty
from collections import defaultdict
from collections.abc import Collection, Mapping, Sequence
from datetime import datetime
from functools import cached_property, lru_cache
from typing import NamedTuple, Optional, Union, cast

import dagster._check as check
from dagster._annotations import PublicAttr, beta, public
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionKey,
    MultiPartitionsDefinition,
)
from dagster._core.definitions.partition import (
    AllPartitionsSubset,
    DefaultPartitionsSubset,
    PartitionsDefinition,
    PartitionsSubset,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.instance import DynamicPartitionsStore
from dagster._record import record
from dagster._serdes import whitelist_for_serdes
from dagster._utils.cached_method import cached_method
from dagster._utils.warnings import disable_dagster_warnings


@record
class UpstreamPartitionsResult:
    """Represents the result of mapping a PartitionsSubset to the corresponding
    partitions in another PartitionsDefinition.

    partitions_subset (PartitionsSubset): The resulting partitions subset that was
        mapped to. Only contains partitions for existent partitions, filtering out nonexistent partitions.
    required_but_nonexistent_subset (PartitionsSubset): A set of invalid partition keys in to_partitions_def
        that partitions in from_partitions_subset were mapped to.
    """

    partitions_subset: PartitionsSubset
    required_but_nonexistent_subset: PartitionsSubset

    @cached_property
    def required_but_nonexistent_partition_keys(self) -> Sequence[str]:
        return list(self.required_but_nonexistent_subset.get_partition_keys())


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
        upstream_partitions_def: PartitionsDefinition,
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
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        """Returns a UpstreamPartitionsResult object containing the partition keys the downstream
        partitions subset was mapped to in the upstream partitions definition.

        Valid upstream partitions will be included in UpstreamPartitionsResult.partitions_subset.
        Invalid upstream partitions will be included in UpstreamPartitionsResult.required_but_nonexistent_subset.

        For example, if an upstream asset is time-partitioned and starts in June 2023, and the
        downstream asset is time-partitioned and starts in May 2023, this function would return a
        UpstreamPartitionsResult(PartitionsSubset("2023-06-01"), required_but_nonexistent_subset=PartitionsSubset("2023-05-01"))
        when downstream_partitions_subset contains 2023-05-01 and 2023-06-01.
        """

    @abstractproperty
    def description(self) -> str:
        """A human-readable description of the partition mapping, displayed in the Dagster UI."""
        raise NotImplementedError()


@whitelist_for_serdes
class IdentityPartitionMapping(PartitionMapping, NamedTuple("_IdentityPartitionMapping", [])):
    """Expects that the upstream and downstream assets are partitioned in the same way, and maps
    partitions in the downstream asset to the same partition in the upstream asset.
    """

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        if downstream_partitions_subset is None:
            check.failed("downstream asset is not partitioned")

        if downstream_partitions_def == upstream_partitions_def:
            return UpstreamPartitionsResult(
                partitions_subset=downstream_partitions_subset,
                required_but_nonexistent_subset=upstream_partitions_def.empty_subset(),
            )

        # must list out the keys before combining them since they might be from
        # different asset keys
        upstream_partition_keys = set(
            upstream_partitions_def.get_partition_keys(
                current_time=current_time,
                dynamic_partitions_store=dynamic_partitions_store,
            )
        )
        downstream_partition_keys = set(downstream_partitions_subset.get_partition_keys())

        return UpstreamPartitionsResult(
            partitions_subset=upstream_partitions_def.subset_with_partition_keys(
                list(upstream_partition_keys & downstream_partition_keys)
            ),
            required_but_nonexistent_subset=DefaultPartitionsSubset(
                downstream_partition_keys - upstream_partition_keys,
            ),
        )

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        if upstream_partitions_subset is None:
            check.failed("upstream asset is not partitioned")

        if upstream_partitions_def == downstream_partitions_def:
            return upstream_partitions_subset

        upstream_partition_keys = set(upstream_partitions_subset.get_partition_keys())
        downstream_partition_keys = set(
            downstream_partitions_def.get_partition_keys(
                current_time=current_time,
                dynamic_partitions_store=dynamic_partitions_store,
            )
        )

        return downstream_partitions_def.empty_subset().with_partition_keys(
            list(downstream_partition_keys & upstream_partition_keys)
        )

    @property
    def description(self) -> str:
        return (
            "Assumes upstream and downstream assets share the same partitions definition. "
            "Maps each partition in the downstream asset to the same partition in the upstream asset."
        )


@whitelist_for_serdes
class AllPartitionMapping(PartitionMapping, NamedTuple("_AllPartitionMapping", [])):
    """Maps every partition in the downstream asset to every partition in the upstream asset.

    Commonly used in the case when the downstream asset is not partitioned, in which the entire
    downstream asset depends on all partitions of the upstream asset.
    """

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        if dynamic_partitions_store is not None and current_time is not None:
            partitions_subset = AllPartitionsSubset(
                partitions_def=upstream_partitions_def,
                dynamic_partitions_store=dynamic_partitions_store,
                current_time=current_time,
            )
        else:
            partitions_subset = upstream_partitions_def.subset_with_all_partitions(
                current_time=current_time, dynamic_partitions_store=dynamic_partitions_store
            )
        return UpstreamPartitionsResult(
            partitions_subset=partitions_subset,
            required_but_nonexistent_subset=upstream_partitions_def.empty_subset(),
        )

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        if upstream_partitions_subset is None:
            check.failed("upstream asset is not partitioned")

        if len(upstream_partitions_subset) == 0:
            return downstream_partitions_def.empty_subset()

        return downstream_partitions_def.subset_with_all_partitions(
            current_time=current_time, dynamic_partitions_store=dynamic_partitions_store
        )

    @property
    def description(self) -> str:
        return "Each downstream partition depends on all partitions of the upstream asset."


@whitelist_for_serdes
class LastPartitionMapping(PartitionMapping, NamedTuple("_LastPartitionMapping", [])):
    """Maps all dependencies to the last partition in the upstream asset.

    Commonly used in the case when the downstream asset is not partitioned, in which the entire
    downstream asset depends on the last partition of the upstream asset.
    """

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        last = upstream_partitions_def.get_last_partition_key(
            current_time=current_time, dynamic_partitions_store=dynamic_partitions_store
        )

        upstream_subset = upstream_partitions_def.empty_subset()
        if last is not None:
            upstream_subset = upstream_subset.with_partition_keys([last])

        return UpstreamPartitionsResult(
            partitions_subset=upstream_subset,
            required_but_nonexistent_subset=upstream_partitions_def.empty_subset(),
        )

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        last_upstream_partition = upstream_partitions_def.get_last_partition_key(
            current_time=current_time, dynamic_partitions_store=dynamic_partitions_store
        )
        if last_upstream_partition and last_upstream_partition in upstream_partitions_subset:
            return downstream_partitions_def.subset_with_all_partitions(
                current_time=current_time, dynamic_partitions_store=dynamic_partitions_store
            )
        else:
            return downstream_partitions_def.empty_subset()

    @property
    def description(self) -> str:
        return "Each downstream partition depends on the last partition of the upstream asset."


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
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        return UpstreamPartitionsResult(
            partitions_subset=upstream_partitions_def.subset_with_partition_keys(
                self.partition_keys
            ),
            required_but_nonexistent_subset=upstream_partitions_def.empty_subset(),
        )

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        upstream_partitions_def: PartitionsDefinition,
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

    @property
    def description(self) -> str:
        return f"Each downstream partition depends on the following upstream partitions: {self.partition_keys}"


class DimensionDependency(NamedTuple):
    partition_mapping: PartitionMapping
    upstream_dimension_name: Optional[str] = None
    downstream_dimension_name: Optional[str] = None


class BaseMultiPartitionMapping(ABC):
    @abstractmethod
    def get_dimension_dependencies(
        self,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: PartitionsDefinition,
    ) -> Sequence[DimensionDependency]: ...

    def get_partitions_def(
        self, partitions_def: PartitionsDefinition, dimension_name: Optional[str]
    ) -> PartitionsDefinition:
        if isinstance(partitions_def, MultiPartitionsDefinition):
            if not isinstance(dimension_name, str):
                check.failed("Expected dimension_name to be a string")
            return partitions_def.get_partitions_def_for_dimension(dimension_name)
        return partitions_def

    def _get_dependency_partitions_subset(
        self,
        a_partitions_def: PartitionsDefinition,
        a_partitions_subset: PartitionsSubset,
        b_partitions_def: PartitionsDefinition,
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
        if isinstance(a_partitions_def, MultiPartitionsDefinition):
            for partition_key in a_partitions_subset.get_partition_keys():
                key = a_partitions_def.get_partition_key_from_str(partition_key)
                for dimension_name, key in key.keys_by_dimension.items():
                    a_partition_keys_by_dimension[dimension_name].add(key)
        else:
            for partition_key in a_partitions_subset.get_partition_keys():
                a_partition_keys_by_dimension[None].add(partition_key)

        # Maps the dimension name and key of a partition in a_partitions_def to the list of
        # partition keys in b_partitions_def that are dependencies of that partition
        dep_b_keys_by_a_dim_and_key: dict[Optional[str], dict[Optional[str], list[str]]] = (
            defaultdict(lambda: defaultdict(list))
        )
        required_but_nonexistent_upstream_partitions = set()

        b_dimension_partitions_def_by_name: dict[Optional[str], PartitionsDefinition] = (
            {
                dimension.name: dimension.partitions_def
                for dimension in b_partitions_def.partitions_defs
            }
            if isinstance(b_partitions_def, MultiPartitionsDefinition)
            else {None: b_partitions_def}
        )

        if a_upstream_of_b:
            # a_partitions_def is upstream of b_partitions_def, so we need to map the
            # dimension names of a_partitions_def to the corresponding dependent dimensions of
            # b_partitions_def
            a_dim_to_dependency_b_dim = {
                dimension_mapping.upstream_dimension_name: (
                    dimension_mapping.downstream_dimension_name,
                    dimension_mapping.partition_mapping,
                )
                for dimension_mapping in self.get_dimension_dependencies(
                    a_partitions_def, b_partitions_def
                )
            }

            for a_dim_name, keys in a_partition_keys_by_dimension.items():
                if a_dim_name in a_dim_to_dependency_b_dim:
                    (
                        b_dim_name,
                        dimension_mapping,
                    ) = a_dim_to_dependency_b_dim[a_dim_name]
                    a_dimension_partitions_def = self.get_partitions_def(
                        a_partitions_def, a_dim_name
                    )
                    b_dimension_partitions_def = self.get_partitions_def(
                        b_partitions_def, b_dim_name
                    )
                    for key in keys:
                        # if downstream dimension mapping exists, for a given key, get the list of
                        # downstream partition keys that are dependencies of that key
                        dep_b_keys_by_a_dim_and_key[a_dim_name][key] = list(
                            dimension_mapping.get_downstream_partitions_for_partitions(
                                a_dimension_partitions_def.empty_subset().with_partition_keys(
                                    [key]
                                ),
                                a_dimension_partitions_def,
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
                dimension_mapping.downstream_dimension_name: (
                    dimension_mapping.upstream_dimension_name,
                    dimension_mapping.partition_mapping,
                )
                for dimension_mapping in self.get_dimension_dependencies(
                    b_partitions_def, a_partitions_def
                )
            }

            for a_dim_name, keys in a_partition_keys_by_dimension.items():
                if a_dim_name in a_dim_to_dependency_b_dim:
                    (
                        b_dim_name,
                        partition_mapping,
                    ) = a_dim_to_dependency_b_dim[a_dim_name]
                    a_dimension_partitions_def = self.get_partitions_def(
                        a_partitions_def, a_dim_name
                    )
                    b_dimension_partitions_def = self.get_partitions_def(
                        b_partitions_def, b_dim_name
                    )
                    for key in keys:
                        mapped_partitions_result = (
                            partition_mapping.get_upstream_mapped_partitions_result_for_partitions(
                                a_dimension_partitions_def.empty_subset().with_partition_keys(
                                    [key]
                                ),
                                a_dimension_partitions_def,
                                b_dimension_partitions_def,
                                current_time=current_time,
                                dynamic_partitions_store=dynamic_partitions_store,
                            )
                        )
                        dep_b_keys_by_a_dim_and_key[a_dim_name][key] = list(
                            mapped_partitions_result.partitions_subset.get_partition_keys()
                        )

                        # enumerating partition keys since the two subsets might be from different
                        # asset keys
                        required_but_nonexistent_upstream_partitions.update(
                            set(
                                mapped_partitions_result.required_but_nonexistent_subset.get_partition_keys()
                            )
                        )

        b_partition_keys = set()

        mapped_a_dim_names = a_dim_to_dependency_b_dim.keys()
        mapped_b_dim_names = [mapping[0] for mapping in a_dim_to_dependency_b_dim.values()]
        unmapped_b_dim_names = list(
            set(b_dimension_partitions_def_by_name.keys()) - set(mapped_b_dim_names)
        )

        for key in a_partitions_subset.get_partition_keys():
            for b_key_values in itertools.product(
                *(
                    [
                        dep_b_keys_by_a_dim_and_key[dim_name][
                            (
                                cast(MultiPartitionsDefinition, a_partitions_def)
                                .get_partition_key_from_str(key)
                                .keys_by_dimension[dim_name]
                                if dim_name
                                else key
                            )
                        ]
                        for dim_name in mapped_a_dim_names
                    ]
                ),
                *[
                    b_dimension_partitions_def_by_name[dim_name].get_partition_keys(
                        dynamic_partitions_store=dynamic_partitions_store, current_time=current_time
                    )
                    for dim_name in unmapped_b_dim_names
                ],
            ):
                b_partition_keys.add(
                    MultiPartitionKey(
                        {
                            cast(str, (mapped_b_dim_names + unmapped_b_dim_names)[i]): key
                            for i, key in enumerate(b_key_values)
                        }
                    )
                    if len(b_key_values) > 1
                    else b_key_values[0]  # type: ignore
                )

        mapped_subset = b_partitions_def.empty_subset().with_partition_keys(b_partition_keys)
        if a_upstream_of_b:
            return mapped_subset
        else:
            return UpstreamPartitionsResult(
                partitions_subset=mapped_subset,
                required_but_nonexistent_subset=DefaultPartitionsSubset(
                    required_but_nonexistent_upstream_partitions
                ),
            )

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        if downstream_partitions_subset is None:
            check.failed("downstream asset is not partitioned")

        result = self._get_dependency_partitions_subset(
            check.not_none(downstream_partitions_def),
            downstream_partitions_subset,
            cast(MultiPartitionsDefinition, upstream_partitions_def),
            a_upstream_of_b=False,
            dynamic_partitions_store=dynamic_partitions_store,
            current_time=current_time,
        )

        if not isinstance(result, UpstreamPartitionsResult):
            check.failed("Expected UpstreamPartitionsResult")

        return result

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        if upstream_partitions_subset is None:
            check.failed("upstream asset is not partitioned")

        result = self._get_dependency_partitions_subset(
            upstream_partitions_def,
            upstream_partitions_subset,
            cast(MultiPartitionsDefinition, downstream_partitions_def),
            a_upstream_of_b=True,
            dynamic_partitions_store=dynamic_partitions_store,
        )

        if isinstance(result, UpstreamPartitionsResult):
            check.failed("Expected PartitionsSubset")

        return result


@beta
@whitelist_for_serdes
class MultiToSingleDimensionPartitionMapping(
    BaseMultiPartitionMapping,
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
        return super().__new__(
            cls,
            partition_dimension_name=check.opt_str_param(
                partition_dimension_name, "partition_dimension_name"
            ),
        )

    @property
    def description(self) -> str:
        return (
            "Assumes that the single-dimension partitions definition is a dimension of the "
            "multi-partitions definition. For a single-dimension partition key X, any "
            "multi-partition key with X in the matching dimension is a dependency."
        )

    def get_dimension_dependencies(
        self,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: PartitionsDefinition,
    ) -> Sequence[DimensionDependency]:
        infer_mapping_result = _get_infer_single_to_multi_dimension_deps_result(
            upstream_partitions_def, downstream_partitions_def
        )

        if not infer_mapping_result.can_infer:
            check.invariant(isinstance(infer_mapping_result.inference_failure_reason, str))
            check.failed(cast(str, infer_mapping_result.inference_failure_reason))

        return [cast(DimensionDependency, infer_mapping_result.dimension_dependency)]


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
        return super().__new__(
            cls,
            dimension_name=check.str_param(dimension_name, "dimension_name"),
            partition_mapping=check.inst_param(
                partition_mapping, "partition_mapping", PartitionMapping
            ),
        )


@beta
@whitelist_for_serdes
class MultiPartitionMapping(
    BaseMultiPartitionMapping,
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

            MultiPartitionMapping(
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

            MultiPartitionMapping(
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
        return super().__new__(
            cls,
            downstream_mappings_by_upstream_dimension=check.mapping_param(
                downstream_mappings_by_upstream_dimension,
                "downstream_mappings_by_upstream_dimension",
                key_type=str,
                value_type=DimensionPartitionMapping,
            ),
        )

    @property
    def description(self) -> str:
        return "\n ".join(
            [
                (
                    f"Upstream dimension '{upstream_dim}' mapped to downstream dimension "
                    f"'{downstream_mapping.dimension_name}' using {type(downstream_mapping.partition_mapping).__name__}."
                )
                for upstream_dim, downstream_mapping in self.downstream_mappings_by_upstream_dimension.items()
            ]
        )

    def get_dimension_dependencies(
        self,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: PartitionsDefinition,
    ) -> Sequence[DimensionDependency]:
        self._check_all_dimensions_accounted_for(
            upstream_partitions_def,
            downstream_partitions_def,
        )

        return [
            DimensionDependency(
                mapping.partition_mapping,
                upstream_dimension_name=upstream_dimension,
                downstream_dimension_name=mapping.dimension_name,
            )
            for upstream_dimension, mapping in self.downstream_mappings_by_upstream_dimension.items()
        ]

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
    def _check_upstream(self, *, upstream_partitions_def: StaticPartitionsDefinition):
        """Validate that the mapping from upstream to downstream is only defined on upstream keys."""
        check.inst_param(
            upstream_partitions_def,
            "upstream_partitions_def",
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
    def _check_downstream(self, *, downstream_partitions_def: StaticPartitionsDefinition):
        """Validate that the mapping from upstream to downstream only maps to downstream keys."""
        check.inst_param(
            downstream_partitions_def,
            "downstream_partitions_def",
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

    def get_downstream_partitions_for_partitions(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        upstream_partitions_subset: PartitionsSubset,
        upstream_partitions_def: StaticPartitionsDefinition,
        downstream_partitions_def: StaticPartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        self._check_downstream(downstream_partitions_def=downstream_partitions_def)

        downstream_subset = downstream_partitions_def.empty_subset()
        downstream_keys = set()
        for key in upstream_partitions_subset.get_partition_keys():
            downstream_keys.update(self._mapping[key])
        return downstream_subset.with_partition_keys(downstream_keys)

    def get_upstream_mapped_partitions_result_for_partitions(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: StaticPartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        self._check_upstream(upstream_partitions_def=upstream_partitions_def)

        upstream_subset = upstream_partitions_def.empty_subset()
        if downstream_partitions_subset is None:
            return UpstreamPartitionsResult(
                partitions_subset=upstream_subset,
                required_but_nonexistent_subset=upstream_partitions_def.empty_subset(),
            )

        upstream_keys = set()
        for key in downstream_partitions_subset.get_partition_keys():
            upstream_keys.update(self._inverse_mapping[key])

        return UpstreamPartitionsResult(
            partitions_subset=upstream_subset.with_partition_keys(upstream_keys),
            required_but_nonexistent_subset=upstream_partitions_def.empty_subset(),
        )

    @property
    def description(self) -> str:
        return (
            f"Maps upstream partitions to their downstream dependencies according to the "
            f"following mapping: \n{self.downstream_partition_keys_by_upstream_partition_key}"
        )


class InferSingleToMultiDimensionDepsResult(
    NamedTuple(
        "_InferSingleToMultiDimensionDepsResult",
        [
            ("can_infer", bool),
            ("inference_failure_reason", Optional[str]),
            ("dimension_dependency", Optional[DimensionDependency]),
        ],
    )
):
    def __new__(
        cls,
        can_infer: bool,
        inference_failure_reason: Optional[str] = None,
        dimension_dependency: Optional[DimensionDependency] = None,
    ):
        if can_infer and dimension_dependency is None:
            check.failed("dimension_dependency must be provided if can_infer is True")
        if not can_infer and inference_failure_reason is None:
            check.failed("inference_failure_reason must be provided if can_infer is False")

        return super().__new__(
            cls,
            can_infer,
            inference_failure_reason,
            dimension_dependency,
        )


def _get_infer_single_to_multi_dimension_deps_result(
    upstream_partitions_def: PartitionsDefinition,
    downstream_partitions_def: PartitionsDefinition,
    partition_dimension_name: Optional[str] = None,
) -> InferSingleToMultiDimensionDepsResult:
    from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping

    upstream_is_multipartitioned = isinstance(upstream_partitions_def, MultiPartitionsDefinition)

    multipartitions_defs = [
        partitions_def
        for partitions_def in [upstream_partitions_def, downstream_partitions_def]
        if isinstance(partitions_def, MultiPartitionsDefinition)
    ]
    if len(multipartitions_defs) != 1:
        return InferSingleToMultiDimensionDepsResult(
            False,
            "Can only use MultiToSingleDimensionPartitionMapping when upstream asset is"
            " multipartitioned and the downstream asset is single dimensional, or vice versa."
            f" Instead received {len(multipartitions_defs)} multi-partitioned assets.",
        )

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

    filtered_multipartition_dims = (
        multipartitions_def.partitions_defs
        if partition_dimension_name is None
        else [
            dim
            for dim in multipartitions_def.partitions_defs
            if dim.name == partition_dimension_name
        ]
    )

    if partition_dimension_name:
        if len(filtered_multipartition_dims) != 1:
            return InferSingleToMultiDimensionDepsResult(
                False,
                f"Provided partition dimension name {partition_dimension_name} not found in"
                f" multipartitions definition {multipartitions_def}.",
            )

    matching_dimension_defs = [
        dimension_def
        for dimension_def in filtered_multipartition_dims
        if dimension_def.partitions_def == single_dimension_partitions_def
    ]

    if len(matching_dimension_defs) == 1:
        return InferSingleToMultiDimensionDepsResult(
            True,
            dimension_dependency=DimensionDependency(
                IdentityPartitionMapping(),
                upstream_dimension_name=(
                    matching_dimension_defs[0].name if upstream_is_multipartitioned else None
                ),
                downstream_dimension_name=(
                    matching_dimension_defs[0].name if not upstream_is_multipartitioned else None
                ),
            ),
        )
    elif len(matching_dimension_defs) > 1:
        return InferSingleToMultiDimensionDepsResult(
            False,
            "partition dimension name must be specified when multiple dimensions of the"
            " MultiPartitionsDefinition match the single dimension partitions def",
        )

    time_dimensions = [
        dimension_def
        for dimension_def in filtered_multipartition_dims
        if isinstance(dimension_def.partitions_def, TimeWindowPartitionsDefinition)
    ]

    if len(time_dimensions) == 1 and isinstance(
        single_dimension_partitions_def, TimeWindowPartitionsDefinition
    ):
        return InferSingleToMultiDimensionDepsResult(
            True,
            dimension_dependency=DimensionDependency(
                TimeWindowPartitionMapping(),
                upstream_dimension_name=(
                    time_dimensions[0].name if upstream_is_multipartitioned else None
                ),
                downstream_dimension_name=(
                    time_dimensions[0].name if not upstream_is_multipartitioned else None
                ),
            ),
        )

    return InferSingleToMultiDimensionDepsResult(
        False,
        "MultiToSingleDimensionPartitionMapping can only be used when: \n(a) The single dimensional"
        " partitions definition is a dimension of the MultiPartitionsDefinition.\n(b) The single"
        " dimensional partitions definition is a TimeWindowPartitionsDefinition and the"
        " MultiPartitionsDefinition has a single time dimension.",
    )


def infer_partition_mapping(
    partition_mapping: Optional[PartitionMapping],
    downstream_partitions_def: Optional[PartitionsDefinition],
    upstream_partitions_def: Optional[PartitionsDefinition],
) -> PartitionMapping:
    from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping

    if partition_mapping is not None:
        return partition_mapping
    elif upstream_partitions_def and downstream_partitions_def:
        if _get_infer_single_to_multi_dimension_deps_result(
            upstream_partitions_def, downstream_partitions_def
        ).can_infer:
            with disable_dagster_warnings():
                return MultiToSingleDimensionPartitionMapping()
        elif isinstance(upstream_partitions_def, TimeWindowPartitionsDefinition) and isinstance(
            downstream_partitions_def, TimeWindowPartitionsDefinition
        ):
            return TimeWindowPartitionMapping()
        else:
            return IdentityPartitionMapping()
    else:
        return AllPartitionMapping()


@lru_cache(maxsize=1)
def get_builtin_partition_mapping_types() -> tuple[type[PartitionMapping], ...]:
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


def warn_if_partition_mapping_not_builtin(partition_mapping: PartitionMapping) -> None:
    builtin_partition_mappings = get_builtin_partition_mapping_types()
    if not isinstance(partition_mapping, builtin_partition_mappings):
        warnings.warn(
            f"Non-built-in PartitionMappings, such as {type(partition_mapping).__name__} "
            "are deprecated and will not work with asset reconciliation. The built-in "
            "partition mappings are "
            + ", ".join(
                builtin_partition_mapping.__name__
                for builtin_partition_mapping in builtin_partition_mappings
            )
            + ".",
            category=DeprecationWarning,
        )
