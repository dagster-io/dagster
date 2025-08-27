import itertools
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple, Optional, Union, cast

import dagster._check as check
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition import (
    MultiPartitionsDefinition,
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.mapping.partition_mapping import (
    PartitionMapping,
    UpstreamPartitionsResult,
)
from dagster._core.definitions.partitions.subset.default import DefaultPartitionsSubset
from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
from dagster._core.definitions.partitions.utils.multi import MultiPartitionKey
from dagster._serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


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
                                cast("MultiPartitionsDefinition", a_partitions_def)
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
                    b_dimension_partitions_def_by_name[dim_name].get_partition_keys()
                    for dim_name in unmapped_b_dim_names
                ],
            ):
                b_partition_keys.add(
                    MultiPartitionKey(
                        {
                            cast("str", (mapped_b_dim_names + unmapped_b_dim_names)[i]): key
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
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> UpstreamPartitionsResult:
        with partition_loading_context(current_time, dynamic_partitions_store):
            if downstream_partitions_subset is None:
                check.failed("downstream asset is not partitioned")

            result = self._get_dependency_partitions_subset(
                check.not_none(downstream_partitions_def),
                downstream_partitions_subset,
                cast("MultiPartitionsDefinition", upstream_partitions_def),
                a_upstream_of_b=False,
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
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> PartitionsSubset:
        with partition_loading_context(current_time, dynamic_partitions_store):
            if upstream_partitions_subset is None:
                check.failed("upstream asset is not partitioned")

            result = self._get_dependency_partitions_subset(
                upstream_partitions_def,
                upstream_partitions_subset,
                cast("MultiPartitionsDefinition", downstream_partitions_def),
                a_upstream_of_b=True,
            )

            if isinstance(result, UpstreamPartitionsResult):
                check.failed("Expected PartitionsSubset")

            return result


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
