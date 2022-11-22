from typing import TYPE_CHECKING, Mapping, NamedTuple, Optional, Sequence

import dagster._check as check
from dagster._core.definitions.executor_definition import ExecutorDefinition, default_executors
from dagster._loggers import default_loggers
from dagster._utils.merger import merge_dicts

from .config import ConfigMapping
from .logger_definition import LoggerDefinition
from .resource_definition import ResourceDefinition
from .utils import DEFAULT_IO_MANAGER_KEY, check_valid_name

DEFAULT_MODE_NAME = "default"

if TYPE_CHECKING:
    from .partition import PartitionedConfig


class ModeDefinition(
    NamedTuple(
        "_ModeDefinition",
        [
            ("name", str),
            ("resource_defs", Mapping[str, ResourceDefinition]),
            ("loggers", Mapping[str, LoggerDefinition]),
            ("executor_defs", Sequence[ExecutorDefinition]),
            ("description", Optional[str]),
            ("config_mapping", Optional[ConfigMapping]),
            ("partitioned_config", Optional["PartitionedConfig"]),
        ],
    )
):
    """Define a mode in which a pipeline can operate.

    A mode provides pipelines with a set of resource implementations, loggers, system storages,
    and executors.

    Args:
        name (Optional[str]): The name of the mode. Must be unique within the
            :py:class:`PipelineDefinition` to which the mode is attached. (default: "default").
        resource_defs (Optional[Mapping [str, ResourceDefinition]]): A dictionary of string resource
            keys to their implementations. Individual solids may require resources to be present by
            these keys.
        logger_defs (Optional[Dict[str, LoggerDefinition]]): A dictionary of string logger
            identifiers to their implementations.
        executor_defs (Optional[List[ExecutorDefinition]]): The set of executors available when
            executing in this mode. By default, this will be the 'in_process' and 'multiprocess'
            executors (:py:data:`~dagster.default_executors`).
        description (Optional[str]): A human-readable description of the mode.
        _config_mapping (Optional[ConfigMapping]): Only for internal use.
        _partitions (Optional[PartitionedConfig]): Only for internal use.
    """

    def __new__(
        cls,
        name: Optional[str] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
        executor_defs: Optional[Sequence[ExecutorDefinition]] = None,
        description: Optional[str] = None,
        _config_mapping: Optional[ConfigMapping] = None,
        _partitioned_config: Optional["PartitionedConfig"] = None,
    ):

        from .partition import PartitionedConfig

        resource_defs = check.opt_mapping_param(
            resource_defs, "resource_defs", key_type=str, value_type=ResourceDefinition
        )

        for key in resource_defs:
            if not key.isidentifier():
                check.failed(f"Resource key '{key}' must be a valid Python identifier.")

        if resource_defs and DEFAULT_IO_MANAGER_KEY in resource_defs:
            resource_defs_with_defaults = resource_defs
        else:
            from dagster._core.storage.mem_io_manager import mem_io_manager

            resource_defs_with_defaults = merge_dicts(
                {DEFAULT_IO_MANAGER_KEY: mem_io_manager}, resource_defs or {}
            )

        return super(ModeDefinition, cls).__new__(
            cls,
            name=check_valid_name(name) if name else DEFAULT_MODE_NAME,
            resource_defs=resource_defs_with_defaults,
            loggers=(
                check.opt_mapping_param(
                    logger_defs, "logger_defs", key_type=str, value_type=LoggerDefinition
                )
                or default_loggers()
            ),
            executor_defs=check.list_param(
                executor_defs if executor_defs else default_executors,
                "executor_defs",
                of_type=ExecutorDefinition,
            ),
            description=check.opt_str_param(description, "description"),
            config_mapping=check.opt_inst_param(_config_mapping, "_config_mapping", ConfigMapping),
            partitioned_config=check.opt_inst_param(
                _partitioned_config, "_partitioned_config", PartitionedConfig
            ),
        )

    @property
    def resource_key_set(self):
        return frozenset(self.resource_defs.keys())

    @staticmethod
    def from_resources(resources, name=None):
        check.dict_param(resources, "resources", key_type=str)

        return ModeDefinition(
            name=name,
            resource_defs={
                resource_name: ResourceDefinition.hardcoded_resource(resource)
                for resource_name, resource in resources.items()
            },
        )
