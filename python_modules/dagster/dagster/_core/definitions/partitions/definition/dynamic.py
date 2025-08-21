from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Callable, NamedTuple, Optional, Union

import dagster._check as check
from dagster._annotations import PublicAttr, deprecated_param, public
from dagster._core.definitions.dynamic_partitions_request import (
    AddDynamicPartitionsRequest,
    DeleteDynamicPartitionsRequest,
)
from dagster._core.definitions.partitions.context import (
    PartitionLoadingContext,
    partition_loading_context,
)
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.partition import Partition
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.pagination import PaginatedResults

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


@deprecated_param(
    param="partition_fn",
    breaking_version="2.0",
    additional_warn_text="Provide partition definition name instead.",
)
@public
class DynamicPartitionsDefinition(
    PartitionsDefinition,
    NamedTuple(
        "_DynamicPartitionsDefinition",
        [
            (
                "partition_fn",
                PublicAttr[
                    Optional[
                        Callable[[Optional[datetime]], Union[Sequence[Partition], Sequence[str]]]
                    ]
                ],
            ),
            ("name", PublicAttr[Optional[str]]),
        ],
    ),
):
    """A partitions definition whose partition keys can be dynamically added and removed.

    This is useful for cases where the set of partitions is not known at definition time,
    but is instead determined at runtime.

    Partitions can be added and removed using `instance.add_dynamic_partitions` and
    `instance.delete_dynamic_partition` methods.

    We recommended limiting partition counts for each asset to 100,000 partitions or fewer.

    Args:
        name (Optional[str]): The name of the partitions definition.
        partition_fn (Optional[Callable[[Optional[datetime]], Union[Sequence[Partition], Sequence[str]]]]):
            A function that returns the current set of partitions. This argument is deprecated and
            will be removed in 2.0.0.

    Examples:
        .. code-block:: python

            fruits = DynamicPartitionsDefinition(name="fruits")

            @sensor(job=my_job)
            def my_sensor(context):
                return SensorResult(
                    run_requests=[RunRequest(partition_key="apple")],
                    dynamic_partitions_requests=[fruits.build_add_request(["apple"])]
                )
    """

    def __new__(
        cls,
        partition_fn: Optional[
            Callable[[Optional[datetime]], Union[Sequence[Partition], Sequence[str]]]
        ] = None,
        name: Optional[str] = None,
    ):
        partition_fn = check.opt_callable_param(partition_fn, "partition_fn")
        name = check.opt_str_param(name, "name")

        if partition_fn is None and name is None:
            raise DagsterInvalidDefinitionError(
                "Must provide either partition_fn or name to DynamicPartitionsDefinition."
            )

        if partition_fn and name:
            raise DagsterInvalidDefinitionError(
                "Cannot provide both partition_fn and name to DynamicPartitionsDefinition."
            )

        return super().__new__(
            cls,
            partition_fn=check.opt_callable_param(partition_fn, "partition_fn"),
            name=check.opt_str_param(name, "name"),
        )

    def _validated_name(self) -> str:
        if self.name is None:
            check.failed(
                "Dynamic partitions definition must have a name to fetch dynamic partitions"
            )
        return self.name

    def __eq__(self, other):
        return (
            isinstance(other, DynamicPartitionsDefinition)
            and self.name == other.name
            and self.partition_fn == other.partition_fn
        )

    def __hash__(self):
        return hash(tuple(self.__repr__()))

    def __str__(self) -> str:
        if self.name:
            return f'Dynamic partitions: "{self._validated_name()}"'
        else:
            return super().__str__()

    def _ensure_dynamic_partitions_store(
        self, dynamic_partitions_store: Optional["DynamicPartitionsStore"]
    ) -> "DynamicPartitionsStore":
        if dynamic_partitions_store is None:
            check.failed(
                "The instance is not available to load partitions. You may be seeing this error"
                " when using dynamic partitions with a version of dagster-webserver or"
                " dagster-cloud that is older than 1.1.18. The other possibility is that an"
                " internal framework error where a dynamic partitions store was not properly"
                " threaded down a call stack."
            )
        return dynamic_partitions_store

    @public
    def get_partition_keys(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> Sequence[str]:
        """Returns a list of strings representing the partition keys of the
        PartitionsDefinition.

        Args:
            current_time (Optional[datetime]): A datetime object representing the current time, only
                applicable to time-based partitions definitions.
            dynamic_partitions_store (Optional[DynamicPartitionsStore]): The DynamicPartitionsStore
                object that is responsible for fetching dynamic partitions. Required when the
                partitions definition is a DynamicPartitionsDefinition with a name defined. Users
                can pass the DagsterInstance fetched via `context.instance` to this argument.

        Returns:
            Sequence[str]
        """
        with partition_loading_context(current_time, dynamic_partitions_store) as ctx:
            if self.partition_fn:
                partitions = self.partition_fn(current_time)
                if all(isinstance(partition, Partition) for partition in partitions):
                    return [partition.name for partition in partitions]  # type: ignore  # (illegible conditional)
                else:
                    return partitions  # type: ignore  # (illegible conditional)
            else:
                return self._ensure_dynamic_partitions_store(
                    ctx.dynamic_partitions_store
                ).get_dynamic_partitions(partitions_def_name=self._validated_name())

    def get_serializable_unique_identifier(
        self, dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None
    ) -> str:
        with partition_loading_context(dynamic_partitions_store=dynamic_partitions_store) as ctx:
            return self._ensure_dynamic_partitions_store(
                ctx.dynamic_partitions_store
            ).get_dynamic_partitions_definition_id(self._validated_name())

    def get_paginated_partition_keys(
        self,
        context: PartitionLoadingContext,
        limit: int,
        ascending: bool,
        cursor: Optional[str] = None,
    ) -> PaginatedResults[str]:
        with partition_loading_context(new_ctx=context):
            partition_keys = self.get_partition_keys()
            return PaginatedResults.create_from_sequence(
                partition_keys, limit=limit, ascending=ascending, cursor=cursor
            )

    def has_partition_key(
        self,
        partition_key: str,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> bool:
        with partition_loading_context(current_time, dynamic_partitions_store) as ctx:
            if self.partition_fn:
                return partition_key in self.get_partition_keys()
            else:
                if ctx.dynamic_partitions_store is None:
                    check.failed(
                        "The instance is not available to load partitions. You may be seeing this error"
                        " when using dynamic partitions with a version of dagster-webserver or"
                        " dagster-cloud that is older than 1.1.18. The other possibility is that an"
                        " internal framework error where a dynamic partitions store was not properly"
                        " threaded down a call stack."
                    )

                return ctx.dynamic_partitions_store.has_dynamic_partition(
                    partitions_def_name=self._validated_name(), partition_key=partition_key
                )

    def build_add_request(self, partition_keys: Sequence[str]) -> AddDynamicPartitionsRequest:
        check.sequence_param(partition_keys, "partition_keys", of_type=str)
        validated_name = self._validated_name()
        return AddDynamicPartitionsRequest(validated_name, partition_keys)

    def build_delete_request(self, partition_keys: Sequence[str]) -> DeleteDynamicPartitionsRequest:
        check.sequence_param(partition_keys, "partition_keys", of_type=str)
        validated_name = self._validated_name()
        return DeleteDynamicPartitionsRequest(validated_name, partition_keys)
