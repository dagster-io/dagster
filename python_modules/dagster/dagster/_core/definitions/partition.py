import copy
import hashlib
import json
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import (
    datetime,
    timedelta,
)
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Type,
    Union,
    cast,
)

from dateutil.relativedelta import relativedelta
from typing_extensions import TypeVar

import dagster._check as check
from dagster._annotations import PublicAttr, deprecated, public
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.run_request import (
    AddDynamicPartitionsRequest,
    DeleteDynamicPartitionsRequest,
)
from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
from dagster._core.storage.tags import PARTITION_NAME_TAG, PARTITION_SET_TAG
from dagster._serdes import whitelist_for_serdes
from dagster._utils import xor
from dagster._utils.backcompat import (
    canonicalize_backcompat_args,
    deprecation_warning,
)
from dagster._utils.cached_method import cached_method

from ..errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidDeserializationVersionError,
    DagsterInvalidInvocationError,
    DagsterUnknownPartitionError,
)
from .config import ConfigMapping
from .utils import validate_tags

DEFAULT_DATE_FORMAT = "%Y-%m-%d"

T_cov = TypeVar("T_cov", default=Any, covariant=True)
T_str = TypeVar("T_str", bound=str, default=str, covariant=True)
T_PartitionsDefinition = TypeVar(
    "T_PartitionsDefinition",
    bound="PartitionsDefinition",
    default="PartitionsDefinition",
    covariant=True,
)

# In the Dagster UI users can select partition ranges following the format '2022-01-13...2022-01-14'
# "..." is an invalid substring in partition keys
# The other escape characters are characters that may not display in the Dagster UI.
INVALID_PARTITION_SUBSTRINGS = ["...", "\a", "\b", "\f", "\n", "\r", "\t", "\v", "\0"]


@deprecated
class Partition(Generic[T_cov]):
    """A Partition represents a single slice of the entire set of a job's possible work. It consists
    of a value, which is an object that represents that partition, and an optional name, which is
    used to label the partition in a human-readable way.

    Args:
        value (Any): The object for this partition
        name (str): Name for this partition
    """

    def __init__(self, value: Any, name: Optional[str] = None):
        self._value = value
        self._name = check.str_param(name or str(value), "name")

    @property
    def value(self) -> T_cov:
        return self._value

    @property
    def name(self) -> str:
        return self._name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Partition):
            return False
        else:
            return self.value == other.value and self.name == other.name


@whitelist_for_serdes
class ScheduleType(Enum):
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

    @property
    def ordinal(self):
        return {"HOURLY": 1, "DAILY": 2, "WEEKLY": 3, "MONTHLY": 4}[self.value]

    @property
    def delta(self):
        if self == ScheduleType.HOURLY:
            return timedelta(hours=1)
        elif self == ScheduleType.DAILY:
            return timedelta(days=1)
        elif self == ScheduleType.WEEKLY:
            return timedelta(weeks=1)
        elif self == ScheduleType.MONTHLY:
            return relativedelta(months=1)
        else:
            check.failed(f"Unexpected ScheduleType {self}")

    def __gt__(self, other: "ScheduleType") -> bool:
        check.inst(other, ScheduleType, "Cannot compare ScheduleType with non-ScheduleType")
        return self.ordinal > other.ordinal

    def __lt__(self, other: "ScheduleType") -> bool:
        check.inst(other, ScheduleType, "Cannot compare ScheduleType with non-ScheduleType")
        return self.ordinal < other.ordinal


class PartitionsDefinition(ABC, Generic[T_str]):
    """Defines a set of partitions, which can be attached to a software-defined asset or job.

    Abstract class with implementations for different kinds of partitions.
    """

    @property
    def partitions_subset_class(self) -> Type["PartitionsSubset[T_str]"]:
        return DefaultPartitionsSubset[T_str]

    @abstractmethod
    @public
    def get_partition_keys(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Sequence[T_str]:
        """Returns a list of strings representing the partition keys of the PartitionsDefinition.

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
        ...

    def __str__(self) -> str:
        joined_keys = ", ".join([f"'{key}'" for key in self.get_partition_keys()])
        return joined_keys

    def get_last_partition_key(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Optional[T_str]:
        partition_keys = self.get_partition_keys(current_time, dynamic_partitions_store)
        return partition_keys[-1] if partition_keys else None

    def get_first_partition_key(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Optional[T_str]:
        partition_keys = self.get_partition_keys(current_time, dynamic_partitions_store)
        return partition_keys[0] if partition_keys else None

    def get_partition_keys_in_range(
        self,
        partition_key_range: PartitionKeyRange,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Sequence[T_str]:
        keys_exist = {
            partition_key_range.start: self.has_partition_key(
                partition_key_range.start, dynamic_partitions_store=dynamic_partitions_store
            ),
            partition_key_range.end: self.has_partition_key(
                partition_key_range.end, dynamic_partitions_store=dynamic_partitions_store
            ),
        }
        if not all(keys_exist.values()):
            raise DagsterInvalidInvocationError(
                f"""Partition range {partition_key_range.start} to {partition_key_range.end} is
                not a valid range. Nonexistent partition keys:
                {list(key for key in keys_exist if keys_exist[key] is False)}"""
            )

        # in the simple case, simply return the single key in the range
        if partition_key_range.start == partition_key_range.end:
            return [cast(T_str, partition_key_range.start)]

        # defer this call as it is potentially expensive
        partition_keys = self.get_partition_keys(dynamic_partitions_store=dynamic_partitions_store)
        return partition_keys[
            partition_keys.index(partition_key_range.start) : partition_keys.index(
                partition_key_range.end
            )
            + 1
        ]

    def empty_subset(self) -> "PartitionsSubset[T_str]":
        return self.partitions_subset_class.empty_subset(self)

    def subset_with_partition_keys(
        self, partition_keys: Iterable[str]
    ) -> "PartitionsSubset[T_str]":
        return self.empty_subset().with_partition_keys(partition_keys)

    def subset_with_all_partitions(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> "PartitionsSubset[T_str]":
        return self.subset_with_partition_keys(
            self.get_partition_keys(
                current_time=current_time, dynamic_partitions_store=dynamic_partitions_store
            )
        )

    def deserialize_subset(self, serialized: str) -> "PartitionsSubset[T_str]":
        return self.partitions_subset_class.from_serialized(self, serialized)

    def can_deserialize_subset(
        self,
        serialized: str,
        serialized_partitions_def_unique_id: Optional[str],
        serialized_partitions_def_class_name: Optional[str],
    ) -> bool:
        return self.partitions_subset_class.can_deserialize(
            self,
            serialized,
            serialized_partitions_def_unique_id,
            serialized_partitions_def_class_name,
        )

    def get_serializable_unique_identifier(
        self, dynamic_partitions_store: Optional[DynamicPartitionsStore] = None
    ) -> str:
        return hashlib.sha1(
            json.dumps(
                self.get_partition_keys(dynamic_partitions_store=dynamic_partitions_store)
            ).encode("utf-8")
        ).hexdigest()

    def get_tags_for_partition_key(self, partition_key: str) -> Mapping[str, str]:
        tags = {PARTITION_NAME_TAG: partition_key}
        return tags

    def get_num_partitions(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> int:
        return len(self.get_partition_keys(current_time, dynamic_partitions_store))

    def has_partition_key(
        self,
        partition_key: str,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> bool:
        return partition_key in self.get_partition_keys(
            current_time=current_time,
            dynamic_partitions_store=dynamic_partitions_store,
        )

    def validate_partition_key(
        self,
        partition_key: str,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> None:
        if not self.has_partition_key(partition_key, current_time, dynamic_partitions_store):
            raise DagsterUnknownPartitionError(
                f"Could not find a partition with key `{partition_key}`."
            )


def raise_error_on_invalid_partition_key_substring(partition_keys: Sequence[str]) -> None:
    for partition_key in partition_keys:
        found_invalid_substrs = [
            invalid_substr
            for invalid_substr in INVALID_PARTITION_SUBSTRINGS
            if invalid_substr in partition_key
        ]
        if found_invalid_substrs:
            raise DagsterInvalidDefinitionError(
                f"{found_invalid_substrs} are invalid substrings in a partition key"
            )


def raise_error_on_duplicate_partition_keys(partition_keys: Sequence[str]) -> None:
    counts: Dict[str, int] = defaultdict(lambda: 0)
    for partition_key in partition_keys:
        counts[partition_key] += 1
        found_duplicates = [key for key in counts.keys() if counts[key] > 1]
        if found_duplicates:
            raise DagsterInvalidDefinitionError(
                "Partition keys must be unique. Duplicate instances of partition keys:"
                f" {found_duplicates}."
            )


class StaticPartitionsDefinition(PartitionsDefinition[str]):
    """A statically-defined set of partitions.

    Example:
        .. code-block:: python

            from dagster import StaticPartitionsDefinition, asset

            oceans_partitions_def = StaticPartitionsDefinition(
                ["arctic", "atlantic", "indian", "pacific", "southern"]
            )

            @asset(partitions_def=oceans_partitions_defs)
            def ml_model_for_each_ocean():
                ...
    """

    def __init__(self, partition_keys: Sequence[str]):
        check.sequence_param(partition_keys, "partition_keys", of_type=str)

        raise_error_on_invalid_partition_key_substring(partition_keys)
        raise_error_on_duplicate_partition_keys(partition_keys)

        self._partition_keys = partition_keys

    @public
    def get_partition_keys(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Sequence[str]:
        """Returns a list of strings representing the partition keys of the PartitionsDefinition.

        Args:
            current_time (Optional[datetime]): A datetime object representing the current time, only
                applicable to time-based partitions definitions.
            dynamic_partitions_store (Optional[DynamicPartitionsStore]): The DynamicPartitionsStore
                object that is responsible for fetching dynamic partitions. Only applicable to
                DynamicPartitionsDefinitions.

        Returns:
            Sequence[str]

        """
        return self._partition_keys

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other) -> bool:
        return isinstance(other, StaticPartitionsDefinition) and (
            self is other or self._partition_keys == other.get_partition_keys()
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}(partition_keys={self._partition_keys})"

    def get_num_partitions(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> int:
        # We don't currently throw an error when a duplicate partition key is defined
        # in a static partitions definition, though we will at 1.3.0.
        # This ensures that partition counts are correct in the Dagster UI.
        return len(set(self.get_partition_keys(current_time, dynamic_partitions_store)))


class CachingDynamicPartitionsLoader(DynamicPartitionsStore):
    """A batch loader that caches the partition keys for a given dynamic partitions definition,
    to avoid repeated calls to the database for the same partitions definition.
    """

    def __init__(self, instance: DagsterInstance):
        self._instance = instance

    @cached_method
    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        return self._instance.get_dynamic_partitions(partitions_def_name)

    @cached_method
    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        return self._instance.has_dynamic_partition(partitions_def_name, partition_key)


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

        if partition_fn:
            deprecation_warning(
                "partition_fn", "2.0.0", "Provide partition definition name instead."
            )

        if partition_fn is None and name is None:
            raise DagsterInvalidDefinitionError(
                "Must provide either partition_fn or name to DynamicPartitionsDefinition."
            )

        if partition_fn and name:
            raise DagsterInvalidDefinitionError(
                "Cannot provide both partition_fn and name to DynamicPartitionsDefinition."
            )

        return super(DynamicPartitionsDefinition, cls).__new__(
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

    @public
    def get_partition_keys(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
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
        if self.partition_fn:
            partitions = self.partition_fn(current_time)
            if all(isinstance(partition, Partition) for partition in partitions):
                return [partition.name for partition in partitions]  # type: ignore  # (illegible conditional)
            else:
                return partitions  # type: ignore  # (illegible conditional)
        else:
            check.opt_inst_param(
                dynamic_partitions_store, "dynamic_partitions_store", DynamicPartitionsStore
            )

            if dynamic_partitions_store is None:
                check.failed(
                    "The instance is not available to load partitions. You may be seeing this error"
                    " when using dynamic partitions with a version of dagster-webserver or"
                    " dagster-cloud that is older than 1.1.18."
                )

            return dynamic_partitions_store.get_dynamic_partitions(
                partitions_def_name=self._validated_name()
            )

    def has_partition_key(
        self,
        partition_key: str,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> bool:
        if self.partition_fn:
            return partition_key in self.get_partition_keys(current_time)
        else:
            if dynamic_partitions_store is None:
                check.failed(
                    "The instance is not available to load partitions. You may be seeing this error"
                    " when using dynamic partitions with a version of dagster-webserver or"
                    " dagster-cloud that is older than 1.1.18."
                )

            return dynamic_partitions_store.has_dynamic_partition(
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


class PartitionedConfig(Generic[T_PartitionsDefinition]):
    """Defines a way of configuring a job where the job can be run on one of a discrete set of
    partitions, and each partition corresponds to run configuration for the job.

    Setting PartitionedConfig as the config for a job allows you to launch backfills for that job
    and view the run history across partitions.
    """

    def __init__(
        self,
        partitions_def: T_PartitionsDefinition,
        run_config_for_partition_fn: Optional[Callable[[Partition], Mapping[str, Any]]] = None,
        decorated_fn: Optional[Callable[..., Mapping[str, Any]]] = None,
        tags_for_partition_fn: Optional[Callable[[Partition[Any]], Mapping[str, str]]] = None,
        run_config_for_partition_key_fn: Optional[Callable[[str], Mapping[str, Any]]] = None,
        tags_for_partition_key_fn: Optional[Callable[[str], Mapping[str, str]]] = None,
    ):
        self._partitions = check.inst_param(partitions_def, "partitions_def", PartitionsDefinition)
        self._decorated_fn = decorated_fn

        check.invariant(
            xor(run_config_for_partition_fn, run_config_for_partition_key_fn),
            (
                "Must provide exactly one of run_config_for_partition_fn or"
                " run_config_for_partition_key_fn"
            ),
        )
        check.invariant(
            not (tags_for_partition_fn and tags_for_partition_key_fn),
            "Cannot provide both of tags_for_partition_fn or tags_for_partition_key_fn",
        )
        if run_config_for_partition_fn:
            deprecation_warning(
                "run_config_for_partition_fn", "2.0", "Use run_config_for_partition_key_fn instead"
            )
        if tags_for_partition_fn:
            deprecation_warning(
                "tags_for_partition_fn", "2.0", "Use tags_for_partition_key_fn instead"
            )

        self._run_config_for_partition_fn = check.opt_callable_param(
            run_config_for_partition_fn, "run_config_for_partition_fn"
        )
        self._run_config_for_partition_key_fn = check.opt_callable_param(
            run_config_for_partition_key_fn, "run_config_for_partition_key_fn"
        )
        self._tags_for_partition_fn = check.opt_callable_param(
            tags_for_partition_fn, "tags_for_partition_fn"
        )
        self._tags_for_partition_key_fn = check.opt_callable_param(
            tags_for_partition_key_fn, "tags_for_partition_key_fn"
        )

    @public
    @property
    def partitions_def(
        self,
    ) -> T_PartitionsDefinition:
        """T_PartitionsDefinition: The partitions definition associated with this PartitionedConfig.
        """
        return self._partitions

    @deprecated
    @public
    @property
    def run_config_for_partition_fn(
        self,
    ) -> Optional[Callable[[Partition], Mapping[str, Any]]]:
        """Optional[Callable[[Partition], Mapping[str, Any]]]: A function that accepts a partition
        and returns a dictionary representing the config to attach to runs for that partition.
        Deprecated as of 1.3.3.
        """
        return self._run_config_for_partition_fn

    @public
    @property
    def run_config_for_partition_key_fn(
        self,
    ) -> Optional[Callable[[str], Mapping[str, Any]]]:
        """Optional[Callable[[str], Mapping[str, Any]]]: A function that accepts a partition key
        and returns a dictionary representing the config to attach to runs for that partition.
        """

    @deprecated
    @public
    @property
    def tags_for_partition_fn(self) -> Optional[Callable[[Partition], Mapping[str, str]]]:
        """Optional[Callable[[Partition], Mapping[str, str]]]: A function that
        accepts a partition and returns a dictionary of tags to attach to runs for
        that partition. Deprecated as of 1.3.3.
        """
        return self._tags_for_partition_fn

    @public
    @property
    def tags_for_partition_key_fn(
        self,
    ) -> Optional[Callable[[str], Mapping[str, str]]]:
        """Optional[Callable[[str], Mapping[str, str]]]: A function that
        accepts a partition key and returns a dictionary of tags to attach to runs for
        that partition.
        """
        return self._tags_for_partition_key_fn

    @public
    def get_partition_keys(self, current_time: Optional[datetime] = None) -> Sequence[str]:
        """Returns a list of partition keys, representing the full set of partitions that
        config can be applied to.

        Args:
            current_time (Optional[datetime]): A datetime object representing the current time. Only
                applicable to time-based partitions definitions.

        Returns:
            Sequence[str]
        """
        return self.partitions_def.get_partition_keys(current_time)

    # Assumes partition key already validated
    def get_run_config_for_partition_key(
        self,
        partition_key: str,
    ) -> Mapping[str, Any]:
        """Generates the run config corresponding to a partition key.

        Args:
            partition_key (str): the key for a partition that should be used to generate a run config.
        """
        # _run_config_for_partition_fn is deprecated, we can remove this branching logic in 2.0
        if self._run_config_for_partition_fn:
            run_config = self._run_config_for_partition_fn(Partition(partition_key))
        elif self._run_config_for_partition_key_fn:
            run_config = self._run_config_for_partition_key_fn(partition_key)
        else:
            check.failed("Unreachable.")  # one of the above funcs always defined
        return copy.deepcopy(run_config)

    # Assumes partition key already validated
    def get_tags_for_partition_key(
        self,
        partition_key: str,
        job_name: Optional[str] = None,
    ) -> Mapping[str, str]:
        from dagster._core.host_representation.external_data import (
            external_partition_set_name_for_job_name,
        )

        # _tags_for_partition_fn is deprecated, we can remove this branching logic in 2.0
        if self._tags_for_partition_fn:
            user_tags = self._tags_for_partition_fn(Partition(partition_key))
        elif self._tags_for_partition_key_fn:
            user_tags = self._tags_for_partition_key_fn(partition_key)
        else:
            user_tags = {}
        user_tags = validate_tags(user_tags, allow_reserved_tags=False)

        system_tags = {
            **self.partitions_def.get_tags_for_partition_key(partition_key),
            **(
                # `PartitionSetDefinition` has been deleted but we still need to attach this special tag in
                # order for reexecution against partitions to work properly.
                {PARTITION_SET_TAG: external_partition_set_name_for_job_name(job_name)}
                if job_name
                else {}
            ),
        }

        return {**user_tags, **system_tags}

    @classmethod
    def from_flexible_config(
        cls,
        config: Optional[Union[ConfigMapping, Mapping[str, object], "PartitionedConfig"]],
        partitions_def: PartitionsDefinition,
    ) -> "PartitionedConfig":
        check.invariant(
            not isinstance(config, ConfigMapping),
            "Can't supply a ConfigMapping for 'config' when 'partitions_def' is supplied.",
        )

        if isinstance(config, PartitionedConfig):
            check.invariant(
                config.partitions_def == partitions_def,
                (
                    "Can't supply a PartitionedConfig for 'config' with a different "
                    "PartitionsDefinition than supplied for 'partitions_def'."
                ),
            )
            return config
        else:
            hardcoded_config = config if config else {}
            return cls(
                partitions_def,
                run_config_for_partition_key_fn=lambda _: cast(Mapping, hardcoded_config),
            )

    def __call__(self, *args, **kwargs):
        if self._decorated_fn is None:
            raise DagsterInvalidInvocationError(
                "Only PartitionedConfig objects created using one of the partitioned config "
                "decorators can be directly invoked."
            )
        else:
            return self._decorated_fn(*args, **kwargs)


def static_partitioned_config(
    partition_keys: Sequence[str],
    tags_for_partition_fn: Optional[Callable[[str], Mapping[str, str]]] = None,
    tags_for_partition_key_fn: Optional[Callable[[str], Mapping[str, str]]] = None,
) -> Callable[[Callable[[str], Mapping[str, Any]]], PartitionedConfig[StaticPartitionsDefinition]]:
    """Creates a static partitioned config for a job.

    The provided partition_keys is a static list of strings identifying the set of partitions. The
    list of partitions is static, so while the run config returned by the decorated function may
    change over time, the list of valid partition keys does not.

    This has performance advantages over `dynamic_partitioned_config` in terms of loading different
    partition views in the Dagster UI.

    The decorated function takes in a partition key and returns a valid run config for a particular
    target job.

    Args:
        partition_keys (Sequence[str]): A list of valid partition keys, which serve as the range of
            values that can be provided to the decorated run config function.
        tags_for_partition_fn (Optional[Callable[[str], Mapping[str, str]]]): (deprecated) A function that
            accepts a partition key and returns a dictionary of tags to attach to runs for that
            partition.
        tags_for_partition_key_fn (Optional[Callable[[str], Mapping[str, str]]]): A function that
            accepts a partition key and returns a dictionary of tags to attach to runs for that
            partition.

    Returns:
        PartitionedConfig
    """
    check.sequence_param(partition_keys, "partition_keys", str)

    tags_for_partition_key_fn = canonicalize_backcompat_args(
        tags_for_partition_key_fn,
        "tags_for_partition_key_fn",
        tags_for_partition_fn,
        "tags_for_partition_fn",
        "2.0",
    )

    def inner(
        fn: Callable[[str], Mapping[str, Any]]
    ) -> PartitionedConfig[StaticPartitionsDefinition]:
        return PartitionedConfig(
            partitions_def=StaticPartitionsDefinition(partition_keys),
            run_config_for_partition_key_fn=fn,
            decorated_fn=fn,
            tags_for_partition_key_fn=tags_for_partition_key_fn,
        )

    return inner


def dynamic_partitioned_config(
    partition_fn: Callable[[Optional[datetime]], Sequence[str]],
    tags_for_partition_fn: Optional[Callable[[str], Mapping[str, str]]] = None,
    tags_for_partition_key_fn: Optional[Callable[[str], Mapping[str, str]]] = None,
) -> Callable[[Callable[[str], Mapping[str, Any]]], PartitionedConfig]:
    """Creates a dynamic partitioned config for a job.

    The provided partition_fn returns a list of strings identifying the set of partitions, given
    an optional datetime argument (representing the current time).  The list of partitions returned
    may change over time.

    The decorated function takes in a partition key and returns a valid run config for a particular
    target job.

    Args:
        partition_fn (Callable[[datetime.datetime], Sequence[str]]): A function that generates a
            list of valid partition keys, which serve as the range of values that can be provided
            to the decorated run config function.
        tags_for_partition_fn (Optional[Callable[[str], Mapping[str, str]]]): A function that
            accepts a partition key and returns a dictionary of tags to attach to runs for that
            partition.

    Returns:
        PartitionedConfig
    """
    check.callable_param(partition_fn, "partition_fn")

    tags_for_partition_key_fn = canonicalize_backcompat_args(
        tags_for_partition_key_fn,
        "tags_for_partition_key_fn",
        tags_for_partition_fn,
        "tags_for_partition_fn",
        "2.0",
    )

    def inner(fn: Callable[[str], Mapping[str, Any]]) -> PartitionedConfig:
        return PartitionedConfig(
            partitions_def=DynamicPartitionsDefinition(partition_fn),
            run_config_for_partition_key_fn=fn,
            decorated_fn=fn,
            tags_for_partition_key_fn=tags_for_partition_key_fn,
        )

    return inner


def cron_schedule_from_schedule_type_and_offsets(
    schedule_type: ScheduleType,
    minute_offset: int,
    hour_offset: int,
    day_offset: Optional[int],
) -> str:
    if schedule_type is ScheduleType.HOURLY:
        return f"{minute_offset} * * * *"
    elif schedule_type is ScheduleType.DAILY:
        return f"{minute_offset} {hour_offset} * * *"
    elif schedule_type is ScheduleType.WEEKLY:
        return f"{minute_offset} {hour_offset} * * {day_offset if day_offset is not None else 0}"
    elif schedule_type is ScheduleType.MONTHLY:
        return f"{minute_offset} {hour_offset} {day_offset if day_offset is not None else 1} * *"
    else:
        check.assert_never(schedule_type)


class PartitionsSubset(ABC, Generic[T_str]):
    """Represents a subset of the partitions within a PartitionsDefinition."""

    @abstractmethod
    def get_partition_keys_not_in_subset(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Iterable[T_str]:
        ...

    @abstractmethod
    @public
    def get_partition_keys(self, current_time: Optional[datetime] = None) -> Iterable[T_str]:
        ...

    @abstractmethod
    def get_partition_key_ranges(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Sequence[PartitionKeyRange]:
        ...

    @abstractmethod
    def with_partition_keys(self, partition_keys: Iterable[str]) -> "PartitionsSubset[T_str]":
        ...

    def with_partition_key_range(
        self,
        partition_key_range: PartitionKeyRange,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> "PartitionsSubset[T_str]":
        return self.with_partition_keys(
            self.partitions_def.get_partition_keys_in_range(
                partition_key_range, dynamic_partitions_store=dynamic_partitions_store
            )
        )

    def __or__(self, other: "PartitionsSubset") -> "PartitionsSubset[T_str]":
        if self is other:
            return self
        return self.with_partition_keys(other.get_partition_keys())

    @abstractmethod
    def serialize(self) -> str:
        ...

    @classmethod
    @abstractmethod
    def from_serialized(
        cls, partitions_def: PartitionsDefinition[T_str], serialized: str
    ) -> "PartitionsSubset[T_str]":
        ...

    @classmethod
    @abstractmethod
    def can_deserialize(
        cls,
        partitions_def: PartitionsDefinition,
        serialized: str,
        serialized_partitions_def_unique_id: Optional[str],
        serialized_partitions_def_class_name: Optional[str],
    ) -> bool:
        ...

    @property
    @abstractmethod
    def partitions_def(self) -> PartitionsDefinition[T_str]:
        ...

    @abstractmethod
    def __len__(self) -> int:
        ...

    @abstractmethod
    def __contains__(self, value) -> bool:
        ...

    @classmethod
    @abstractmethod
    def empty_subset(cls, partitions_def: PartitionsDefinition[T_str]) -> "PartitionsSubset[T_str]":
        ...


@whitelist_for_serdes
class SerializedPartitionsSubset(NamedTuple):
    serialized_subset: str
    serialized_partitions_def_unique_id: str
    serialized_partitions_def_class_name: str

    @classmethod
    def from_subset(
        cls,
        subset: PartitionsSubset,
        partitions_def: PartitionsDefinition,
        dynamic_partitions_store: DynamicPartitionsStore,
    ):
        return cls(
            serialized_subset=subset.serialize(),
            serialized_partitions_def_unique_id=partitions_def.get_serializable_unique_identifier(
                dynamic_partitions_store
            ),
            serialized_partitions_def_class_name=partitions_def.__class__.__name__,
        )

    def can_deserialize(self, partitions_def: Optional[PartitionsDefinition]) -> bool:
        if not partitions_def:
            # Asset had a partitions definition at storage time, but no longer does
            return False

        return partitions_def.can_deserialize_subset(
            self.serialized_subset,
            serialized_partitions_def_unique_id=self.serialized_partitions_def_unique_id,
            serialized_partitions_def_class_name=self.serialized_partitions_def_class_name,
        )

    def deserialize(self, partitions_def: PartitionsDefinition) -> PartitionsSubset:
        return partitions_def.deserialize_subset(self.serialized_subset)


class DefaultPartitionsSubset(PartitionsSubset[T_str]):
    # Every time we change the serialization format, we should increment the version number.
    # This will ensure that we can gracefully degrade when deserializing old data.
    SERIALIZATION_VERSION = 1

    def __init__(
        self, partitions_def: PartitionsDefinition[T_str], subset: Optional[Set[T_str]] = None
    ):
        check.opt_set_param(subset, "subset")
        self._partitions_def = partitions_def
        self._subset = subset or set()

    def get_partition_keys_not_in_subset(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Iterable[str]:
        return (
            set(
                self._partitions_def.get_partition_keys(
                    current_time=current_time, dynamic_partitions_store=dynamic_partitions_store
                )
            )
            - self._subset
        )

    def get_partition_keys(self, current_time: Optional[datetime] = None) -> Iterable[str]:
        return self._subset

    def get_partition_key_ranges(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Sequence[PartitionKeyRange]:
        partition_keys = self._partitions_def.get_partition_keys(
            current_time, dynamic_partitions_store=dynamic_partitions_store
        )
        cur_range_start = None
        cur_range_end = None
        result = []
        for partition_key in partition_keys:
            if partition_key in self._subset:
                if cur_range_start is None:
                    cur_range_start = partition_key
                cur_range_end = partition_key
            else:
                if cur_range_start is not None and cur_range_end is not None:
                    result.append(PartitionKeyRange(cur_range_start, cur_range_end))
                cur_range_start = cur_range_end = None

        if cur_range_start is not None and cur_range_end is not None:
            result.append(PartitionKeyRange(cur_range_start, cur_range_end))

        return result

    def with_partition_keys(
        self, partition_keys: Iterable[T_str]
    ) -> "DefaultPartitionsSubset[T_str]":
        return DefaultPartitionsSubset(
            self._partitions_def,
            self._subset | set(partition_keys),
        )

    def serialize(self) -> str:
        # Serialize version number, so attempting to deserialize old versions can be handled gracefully.
        # Any time the serialization format changes, we should increment the version number.
        return json.dumps({"version": self.SERIALIZATION_VERSION, "subset": list(self._subset)})

    @classmethod
    def from_serialized(
        cls, partitions_def: PartitionsDefinition[T_str], serialized: str
    ) -> "PartitionsSubset[T_str]":
        # Check the version number, so only valid versions can be deserialized.
        data = json.loads(serialized)

        if isinstance(data, list):
            # backwards compatibility
            return cls(subset=set(data), partitions_def=partitions_def)
        else:
            if data.get("version") != cls.SERIALIZATION_VERSION:
                raise DagsterInvalidDeserializationVersionError(
                    f"Attempted to deserialize partition subset with version {data.get('version')},"
                    f" but only version {cls.SERIALIZATION_VERSION} is supported."
                )
            return cls(subset=set(data.get("subset")), partitions_def=partitions_def)

    @classmethod
    def can_deserialize(
        cls,
        partitions_def: PartitionsDefinition[T_str],
        serialized: str,
        serialized_partitions_def_unique_id: Optional[str],
        serialized_partitions_def_class_name: Optional[str],
    ) -> bool:
        if serialized_partitions_def_class_name is not None:
            return serialized_partitions_def_class_name == partitions_def.__class__.__name__

        data = json.loads(serialized)
        return isinstance(data, list) or (
            data.get("subset") is not None and data.get("version") == cls.SERIALIZATION_VERSION
        )

    @property
    def partitions_def(self) -> PartitionsDefinition[T_str]:
        return self._partitions_def

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, DefaultPartitionsSubset)
            and self._partitions_def == other._partitions_def
            and self._subset == other._subset
        )

    def __len__(self) -> int:
        return len(self._subset)

    def __contains__(self, value) -> bool:
        return value in self._subset

    def __repr__(self) -> str:
        return (
            f"DefaultPartitionsSubset(subset={self._subset}, partitions_def={self._partitions_def})"
        )

    @classmethod
    def empty_subset(cls, partitions_def: PartitionsDefinition[T_str]) -> "PartitionsSubset[T_str]":
        return cls(partitions_def=partitions_def)
