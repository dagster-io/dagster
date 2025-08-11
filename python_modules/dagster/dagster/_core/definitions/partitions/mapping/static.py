import collections.abc
from collections import defaultdict
from collections.abc import Collection, Mapping
from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple, Optional, Union, cast

import dagster._check as check
from dagster._annotations import PublicAttr
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.definition.static import StaticPartitionsDefinition
from dagster._core.definitions.partitions.mapping.partition_mapping import (
    PartitionMapping,
    UpstreamPartitionsResult,
)
from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._serdes import whitelist_for_serdes
from dagster._utils.cached_method import cached_method

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


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

    def validate_partition_mapping(
        self,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: Optional[PartitionsDefinition],
    ):
        if not isinstance(upstream_partitions_def, StaticPartitionsDefinition):
            raise DagsterInvalidDefinitionError(
                "Upstream partitions definition must be a StaticPartitionsDefinition"
            )
        if not isinstance(downstream_partitions_def, StaticPartitionsDefinition):
            raise DagsterInvalidDefinitionError(
                "Downstream partitions definition must be a StaticPartitionsDefinition",
            )
        self._check_upstream(
            upstream_partitions_def=cast("StaticPartitionsDefinition", upstream_partitions_def)
        )
        self._check_downstream(
            downstream_partitions_def=cast("StaticPartitionsDefinition", downstream_partitions_def)
        )

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
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> PartitionsSubset:
        with partition_loading_context(current_time, dynamic_partitions_store):
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
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> UpstreamPartitionsResult:
        with partition_loading_context(current_time, dynamic_partitions_store):
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
