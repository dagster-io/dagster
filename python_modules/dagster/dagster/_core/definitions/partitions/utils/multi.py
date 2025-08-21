import base64
import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, NamedTuple, Optional, cast

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.partitions.context import (
    PartitionLoadingContext,
    partition_loading_context,
)
from dagster._core.storage.tags import (
    MULTIDIMENSIONAL_PARTITION_PREFIX,
    get_multidimensional_partition_tag,
)
from dagster._record import record

if TYPE_CHECKING:
    from dagster._core.definitions.partitions.definition.partitions_definition import (
        PartitionsDefinition,
    )
    from dagster._core.definitions.partitions.definition.time_window import (
        TimeWindowPartitionsDefinition,
    )

INVALID_STATIC_PARTITIONS_KEY_CHARACTERS = set(["|", ",", "[", "]"])

MULTIPARTITION_KEY_DELIMITER = "|"


def has_one_dimension_time_window_partitioning(
    partitions_def: Optional["PartitionsDefinition"],
) -> bool:
    from dagster._core.definitions.partitions.definition.multi import MultiPartitionsDefinition
    from dagster._core.definitions.partitions.definition.time_window import (
        TimeWindowPartitionsDefinition,
    )

    if isinstance(partitions_def, TimeWindowPartitionsDefinition):
        return True
    elif isinstance(partitions_def, MultiPartitionsDefinition):
        time_window_dims = [
            dim
            for dim in partitions_def.partitions_defs
            if isinstance(dim.partitions_def, TimeWindowPartitionsDefinition)
        ]
        if len(time_window_dims) == 1:
            return True

    return False


def get_time_partitions_def(
    partitions_def: Optional["PartitionsDefinition"],
) -> Optional["TimeWindowPartitionsDefinition"]:
    """For a given PartitionsDefinition, return the associated TimeWindowPartitionsDefinition if it
    exists.
    """
    from dagster._core.definitions.partitions.definition.multi import MultiPartitionsDefinition
    from dagster._core.definitions.partitions.definition.time_window import (
        TimeWindowPartitionsDefinition,
    )

    if partitions_def is None:
        return None
    elif isinstance(partitions_def, TimeWindowPartitionsDefinition):
        return partitions_def
    elif isinstance(
        partitions_def, MultiPartitionsDefinition
    ) and has_one_dimension_time_window_partitioning(partitions_def):
        return cast(
            "TimeWindowPartitionsDefinition", partitions_def.time_window_dimension.partitions_def
        )
    else:
        return None


def get_time_partition_key(
    partitions_def: Optional["PartitionsDefinition"], partition_key: Optional[str]
) -> str:
    from dagster._core.definitions.partitions.definition.multi import MultiPartitionsDefinition
    from dagster._core.definitions.partitions.definition.time_window import (
        TimeWindowPartitionsDefinition,
    )

    if partitions_def is None or partition_key is None:
        check.failed(
            "Cannot get time partitions key from when partitions def is None or partition key is"
            " None"
        )
    elif isinstance(partitions_def, TimeWindowPartitionsDefinition):
        return partition_key
    elif isinstance(partitions_def, MultiPartitionsDefinition):
        return partitions_def.get_partition_key_from_str(partition_key).keys_by_dimension[
            partitions_def.time_window_dimension.name
        ]
    else:
        check.failed(f"Cannot get time partition from non-time partitions def {partitions_def}")


class PartitionDimensionKey(
    NamedTuple("_PartitionDimensionKey", [("dimension_name", str), ("partition_key", str)])
):
    """Representation of a single dimension of a multi-dimensional partition key."""

    def __new__(cls, dimension_name: str, partition_key: str):
        return super().__new__(
            cls,
            dimension_name=check.str_param(dimension_name, "dimension_name"),
            partition_key=check.str_param(partition_key, "partition_key"),
        )


@public
class MultiPartitionKey(str):
    """A multi-dimensional partition key stores the partition key for each dimension.
    Subclasses the string class to keep partition key type as a string.

    Contains additional methods to access the partition key for each dimension.
    Creates a string representation of the partition key for each dimension, separated by a pipe (|).
    Orders the dimensions by name, to ensure consistent string representation.
    """

    dimension_keys: list[PartitionDimensionKey] = []

    def __new__(cls, keys_by_dimension: Mapping[str, str]):
        check.mapping_param(
            keys_by_dimension, "partitions_by_dimension", key_type=str, value_type=str
        )

        dimension_keys: list[PartitionDimensionKey] = [
            PartitionDimensionKey(dimension, keys_by_dimension[dimension])
            for dimension in sorted(list(keys_by_dimension.keys()))
        ]

        str_key = super().__new__(
            cls,
            MULTIPARTITION_KEY_DELIMITER.join(
                [dim_key.partition_key for dim_key in dimension_keys]
            ),
        )

        str_key.dimension_keys = dimension_keys

        return str_key

    def __getnewargs__(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        # When this instance is pickled, replace the argument to __new__ with the
        # dimension key mapping instead of the string representation.
        return ({dim_key.dimension_name: dim_key.partition_key for dim_key in self.dimension_keys},)

    @property
    def keys_by_dimension(self) -> Mapping[str, str]:
        return {dim_key.dimension_name: dim_key.partition_key for dim_key in self.dimension_keys}


def get_tags_from_multi_partition_key(multi_partition_key: MultiPartitionKey) -> Mapping[str, str]:
    check.inst_param(multi_partition_key, "multi_partition_key", MultiPartitionKey)

    return {
        get_multidimensional_partition_tag(dimension.dimension_name): dimension.partition_key
        for dimension in multi_partition_key.dimension_keys
    }


def get_multipartition_key_from_tags(tags: Mapping[str, str]) -> str:
    partitions_by_dimension: dict[str, str] = {}
    for tag in tags:
        if tag.startswith(MULTIDIMENSIONAL_PARTITION_PREFIX):
            dimension = tag[len(MULTIDIMENSIONAL_PARTITION_PREFIX) :]
            partitions_by_dimension[dimension] = tags[tag]

    return MultiPartitionKey(partitions_by_dimension)


@record
class MultiPartitionCursor:
    """A cursor for MultiPartitionsDefinition that tracks last seen keys for each dimension."""

    last_seen_key: Optional[MultiPartitionKey]

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        raw = json.dumps(
            {
                "last_seen_key": self.last_seen_key.keys_by_dimension if self.last_seen_key else {},
            }
        )
        return base64.b64encode(bytes(raw, encoding="utf-8")).decode("utf-8")

    @classmethod
    def from_cursor(cls, cursor: Optional[str]):
        if cursor is None:
            return MultiPartitionCursor(last_seen_key=None)

        raw = json.loads(base64.b64decode(cursor).decode("utf-8"))
        if "last_seen_key" not in raw:
            raise ValueError(f"Invalid cursor: {cursor}")
        return MultiPartitionCursor(last_seen_key=MultiPartitionKey(raw["last_seen_key"]))


class PartitionDimensionDefinition(
    NamedTuple(
        "_PartitionDimensionDefinition",
        [
            ("name", str),
            ("partitions_def", "PartitionsDefinition"),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        partitions_def: "PartitionsDefinition",
    ):
        from dagster._core.definitions.partitions.definition.partitions_definition import (
            PartitionsDefinition,
        )

        return super().__new__(
            cls,
            name=check.str_param(name, "name"),
            partitions_def=check.inst_param(partitions_def, "partitions_def", PartitionsDefinition),
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, PartitionDimensionDefinition)
            and self.name == other.name
            and self.partitions_def == other.partitions_def
        )


class MultiDimensionalPartitionKeyIterator:
    """Helper class to iterate through all the partition keys in a MultiPartitionsDefinition."""

    def __init__(
        self,
        context: PartitionLoadingContext,
        partition_defs: list[PartitionDimensionDefinition],
        cursor: MultiPartitionCursor,
        ascending: bool,
    ):
        with partition_loading_context(new_ctx=context):
            self._ascending = ascending
            self._dimension_names = [dim.name for dim in partition_defs]
            self._dimension_keys = self._initialize_dimension_keys(partition_defs)
            if cursor and cursor.last_seen_key:
                self._last_seen_state = self._initialize_state_to_last_seen_key(
                    self._dimension_keys, ascending, cursor.last_seen_key
                )
            else:
                self._last_seen_state = None

    def __iter__(self):
        return self

    def __next__(self):
        current_state = self.next_state()
        if self._is_state_invalid(current_state, self._dimension_keys):
            raise StopIteration
        self._last_seen_state = current_state
        return self._partition_key_from_state(current_state, self._dimension_keys)

    def next_state(self):
        if self._last_seen_state is None:
            return self._get_initial_state(self._dimension_keys, self._ascending)

        advanced = False
        next_state = {}
        # Iterate through dimensions in reverse order to advance the state by dimension, from the
        # least significant to the most significant dimension.  State is represented by the indices
        # of the cross-product of the keys for each dimension.
        for idx, dim_name in enumerate(reversed(self._dimension_names)):
            if advanced:
                # we've already advanced in the lower dimension, so copy the current dimension index as is
                next_state[dim_name] = self._last_seen_state[dim_name]
                continue
            is_most_significant_dim = idx == len(self._dimension_names) - 1
            delta = 1 if self._ascending else -1
            next_state[dim_name] = self._last_seen_state[dim_name] + delta
            if (self._ascending and next_state[dim_name] < len(self._dimension_keys[dim_name])) or (
                not self._ascending and next_state[dim_name] >= 0
            ):
                advanced = True
            elif not is_most_significant_dim:
                next_state[dim_name] = (
                    0 if self._ascending else len(self._dimension_keys[dim_name]) - 1
                )

        return next_state

    def has_next(self):
        next_state = self.next_state()
        return not self._is_state_invalid(next_state, self._dimension_keys)

    def cursor(self):
        last_partition_key = self._partition_key_from_state(
            self._last_seen_state, self._dimension_keys
        )
        return MultiPartitionCursor(last_seen_key=last_partition_key)

    def _initialize_dimension_keys(self, partition_defs):
        dimension_keys = {}
        for dimension in partition_defs:
            dimension_keys[dimension.name] = dimension.partitions_def.get_partition_keys()

        return dimension_keys

    def _get_initial_state(self, dimension_keys, ascending: bool):
        state = {}
        for dim_name, results in dimension_keys.items():
            if ascending:
                state[dim_name] = 0
            else:
                state[dim_name] = len(results) - 1
        return state

    def _initialize_state_to_last_seen_key(
        self, dimension_keys, ascending: bool, last_seen_key: MultiPartitionKey
    ):
        state = {}
        for dim_name, results in dimension_keys.items():
            if dim_name in last_seen_key.keys_by_dimension:
                dimension_value = last_seen_key.keys_by_dimension[dim_name]
                if dimension_value in results:
                    # the cursor dimension value is in the set of valid values for that dimension
                    state[dim_name] = results.index(dimension_value)
                elif ascending:
                    state[dim_name] = 0
                else:
                    state[dim_name] = len(results) - 1
            elif ascending:
                state[dim_name] = 0
            else:
                state[dim_name] = len(results) - 1
        return state

    def _is_state_invalid(self, state, dimension_keys):
        return any(state[dim_name] >= len(dimension_keys[dim_name]) for dim_name in state) or any(
            state[dim_name] < 0 for dim_name in state
        )

    def _partition_key_from_state(self, state, dimension_keys) -> Optional[MultiPartitionKey]:
        if self._is_state_invalid(state, dimension_keys):
            return None

        partition_tuple = {}
        for dim_name, idx in state.items():
            partition_tuple[dim_name] = dimension_keys[dim_name][idx]

        return MultiPartitionKey(partition_tuple)
