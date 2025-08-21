from collections.abc import Mapping, Sequence
from typing import NamedTuple, Optional, cast

import dagster._check as check
from dagster._annotations import beta, public
from dagster._core.definitions.partitions.definition.multi import MultiPartitionsDefinition
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.mapping.multi.base import (
    BaseMultiPartitionMapping,
    DimensionDependency,
    DimensionPartitionMapping,
)
from dagster._core.definitions.partitions.mapping.partition_mapping import PartitionMapping
from dagster._serdes import whitelist_for_serdes


@beta
@whitelist_for_serdes
@public
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

    def validate_partition_mapping(
        self,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: Optional[PartitionsDefinition],
    ):
        self._check_all_dimensions_accounted_for(
            upstream_partitions_def,
            downstream_partitions_def,
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
        downstream_partitions_def: Optional[PartitionsDefinition],
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
            for dim in cast("MultiPartitionsDefinition", upstream_partitions_def).partitions_defs
        }
        dimension_names = {
            dim.name
            for dim in cast("MultiPartitionsDefinition", downstream_partitions_def).partitions_defs
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
