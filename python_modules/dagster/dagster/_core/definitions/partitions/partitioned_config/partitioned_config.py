import copy
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Generic, Optional, Union, cast

from typing_extensions import TypeAlias, TypeVar

import dagster._check as check
from dagster._annotations import deprecated, deprecated_param, public
from dagster._core.definitions.config import ConfigMapping
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.partition import Partition
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.storage.tags import PARTITION_SET_TAG
from dagster._utils import xor
from dagster._utils.tags import normalize_tags

if TYPE_CHECKING:
    from dagster._core.definitions.run_config import RunConfig

PartitionConfigFn: TypeAlias = "Callable[[str], Union[RunConfig, Mapping[str, Any]]]"
T_PartitionsDefinition = TypeVar(
    "T_PartitionsDefinition",
    bound="PartitionsDefinition",
    default="PartitionsDefinition",
    covariant=True,
)


@public
@deprecated_param(
    param="run_config_for_partition_fn",
    breaking_version="2.0",
    additional_warn_text="Use `run_config_for_partition_key_fn` instead.",
)
@deprecated_param(
    param="tags_for_partition_fn",
    breaking_version="2.0",
    additional_warn_text="Use `tags_for_partition_key_fn` instead.",
)
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
        decorated_fn: Optional[Callable[..., Union["RunConfig", Mapping[str, Any]]]] = None,
        tags_for_partition_fn: Optional[Callable[[Partition[Any]], Mapping[str, str]]] = None,
        run_config_for_partition_key_fn: Optional[PartitionConfigFn] = None,
        tags_for_partition_key_fn: Optional[Callable[[str], Mapping[str, str]]] = None,
    ):
        self._partitions = check.inst_param(partitions_def, "partitions_def", PartitionsDefinition)
        self._decorated_fn = decorated_fn

        check.invariant(
            xor(run_config_for_partition_fn, run_config_for_partition_key_fn),
            "Must provide exactly one of run_config_for_partition_fn or"
            " run_config_for_partition_key_fn",
        )
        check.invariant(
            not (tags_for_partition_fn and tags_for_partition_key_fn),
            "Cannot provide both of tags_for_partition_fn or tags_for_partition_key_fn",
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
        """T_PartitionsDefinition: The partitions definition associated with this PartitionedConfig."""
        return self._partitions

    @deprecated(
        breaking_version="2.0",
        additional_warn_text="Use `run_config_for_partition_key_fn` instead.",
    )
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
    ) -> Optional[PartitionConfigFn]:
        """Optional[Callable[[str], Union[RunConfig, Mapping[str, Any]]]]: A function that accepts a partition key
        and returns a dictionary representing the config to attach to runs for that partition.
        """
        return self._run_config_for_partition_key_fn

    @deprecated(
        breaking_version="2.0", additional_warn_text="Use `tags_for_partition_key_fn` instead."
    )
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
        from dagster._core.definitions.run_config import convert_config_input

        # _run_config_for_partition_fn is deprecated, we can remove this branching logic in 2.0
        if self._run_config_for_partition_fn:
            run_config = self._run_config_for_partition_fn(Partition(partition_key))
        elif self._run_config_for_partition_key_fn:
            run_config = self._run_config_for_partition_key_fn(partition_key)
        else:
            check.failed("Unreachable.")  # one of the above funcs always defined
        normalized_run_config = convert_config_input(
            run_config
        )  # convert any RunConfig to plain dict
        return copy.deepcopy(normalized_run_config)

    # Assumes partition key already validated
    def get_tags_for_partition_key(
        self,
        partition_key: str,
        job_name: Optional[str] = None,
    ) -> Mapping[str, str]:
        from dagster._core.remote_representation.external_data import (
            partition_set_snap_name_for_job_name,
        )

        # _tags_for_partition_fn is deprecated, we can remove this branching logic in 2.0
        if self._tags_for_partition_fn:
            user_tags = self._tags_for_partition_fn(Partition(partition_key))
        elif self._tags_for_partition_key_fn:
            user_tags = self._tags_for_partition_key_fn(partition_key)
        else:
            user_tags = {}
        user_tags = normalize_tags(user_tags, allow_private_system_tags=False)

        system_tags = {
            **self.partitions_def.get_tags_for_partition_key(partition_key),
            # `PartitionSetDefinition` has been deleted but we still need to attach this special tag in
            # order for reexecution against partitions to work properly.
            **(
                {PARTITION_SET_TAG: partition_set_snap_name_for_job_name(job_name)}
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
                "Can't supply a PartitionedConfig for 'config' with a different "
                "PartitionsDefinition than supplied for 'partitions_def'.",
            )
            return config
        else:
            hardcoded_config = config if config else {}
            return cls(
                partitions_def,  # type: ignore # ignored for update, fix me!
                run_config_for_partition_key_fn=lambda _: cast("Mapping", hardcoded_config),
            )

    def __call__(self, *args, **kwargs):
        if self._decorated_fn is None:
            raise DagsterInvalidInvocationError(
                "Only PartitionedConfig objects created using one of the partitioned config "
                "decorators can be directly invoked."
            )
        else:
            return self._decorated_fn(*args, **kwargs)


def partitioned_config(
    partitions_def: PartitionsDefinition,
    tags_for_partition_key_fn: Optional[Callable[[str], Mapping[str, str]]] = None,
) -> Callable[[PartitionConfigFn], PartitionedConfig]:
    """Creates a partitioned config for a job given a PartitionsDefinition.

    The partitions_def provides the set of partitions, which may change over time
        (for example, when using a DynamicPartitionsDefinition).

    The decorated function takes in a partition key and returns a valid run config for a particular
    target job.

    Args:
        partitions_def: (Optional[DynamicPartitionsDefinition]): PartitionsDefinition for the job
        tags_for_partition_key_fn (Optional[Callable[[str], Mapping[str, str]]]): A function that
            accepts a partition key and returns a dictionary of tags to attach to runs for that
            partition.

    Returns:
        PartitionedConfig
    """
    check.opt_callable_param(tags_for_partition_key_fn, "tags_for_partition_key_fn")

    def inner(fn: PartitionConfigFn) -> PartitionedConfig:
        return PartitionedConfig(
            partitions_def=partitions_def,
            run_config_for_partition_key_fn=fn,
            decorated_fn=fn,
            tags_for_partition_key_fn=tags_for_partition_key_fn,
        )

    return inner
