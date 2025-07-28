from collections.abc import Sequence
from typing import NamedTuple, Optional, cast

import dagster._check as check
from dagster._annotations import beta, public
from dagster._core.definitions.partitions.definition.multi import MultiPartitionsDefinition
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.definition.time_window import (
    TimeWindowPartitionsDefinition,
)
from dagster._core.definitions.partitions.mapping.identity import IdentityPartitionMapping
from dagster._core.definitions.partitions.mapping.multi.base import (
    BaseMultiPartitionMapping,
    DimensionDependency,
)
from dagster._core.definitions.partitions.mapping.partition_mapping import PartitionMapping
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._serdes import whitelist_for_serdes


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


def get_infer_single_to_multi_dimension_deps_result(
    upstream_partitions_def: PartitionsDefinition,
    downstream_partitions_def: PartitionsDefinition,
    partition_dimension_name: Optional[str] = None,
) -> InferSingleToMultiDimensionDepsResult:
    from dagster._core.definitions.partitions.mapping import TimeWindowPartitionMapping

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

    multipartitions_def = cast("MultiPartitionsDefinition", next(iter(multipartitions_defs)))

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


@public
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

    def validate_partition_mapping(
        self,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: Optional[PartitionsDefinition],
    ):
        if not downstream_partitions_def:
            raise DagsterInvalidDefinitionError(
                "downstream_partitions_def must be provided for MultiToSingleDimensionPartitionMapping"
            )
        infer_mapping_result = get_infer_single_to_multi_dimension_deps_result(
            upstream_partitions_def, downstream_partitions_def
        )
        if not infer_mapping_result.can_infer:
            check.invariant(isinstance(infer_mapping_result.inference_failure_reason, str))
            check.failed(cast("str", infer_mapping_result.inference_failure_reason))

    def get_dimension_dependencies(
        self,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: PartitionsDefinition,
    ) -> Sequence[DimensionDependency]:
        infer_mapping_result = get_infer_single_to_multi_dimension_deps_result(
            upstream_partitions_def, downstream_partitions_def
        )

        if not infer_mapping_result.can_infer:
            check.invariant(isinstance(infer_mapping_result.inference_failure_reason, str))
            check.failed(cast("str", infer_mapping_result.inference_failure_reason))

        return [cast("DimensionDependency", infer_mapping_result.dimension_dependency)]
