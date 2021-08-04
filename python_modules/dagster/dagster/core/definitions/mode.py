from typing import TYPE_CHECKING, Dict, List, NamedTuple, Optional

from dagster import check
from dagster.core.definitions.executor import ExecutorDefinition, default_executors
from dagster.loggers import default_loggers
from dagster.utils.backcompat import experimental_arg_warning
from dagster.utils.merger import merge_dicts

from .config import ConfigMapping
from .logger import LoggerDefinition
from .resource import ResourceDefinition
from .utils import check_valid_name

DEFAULT_MODE_NAME = "default"

if TYPE_CHECKING:
    from .intermediate_storage import IntermediateStorageDefinition
    from .partition import PartitionedConfig, PartitionSetDefinition


class ModeDefinition(
    NamedTuple(
        "_ModeDefinition",
        [
            ("name", str),
            ("resource_defs", Dict[str, ResourceDefinition]),
            ("loggers", Dict[str, LoggerDefinition]),
            ("executor_defs", List[ExecutorDefinition]),
            ("description", Optional[str]),
            ("intermediate_storage_defs", List["IntermediateStorageDefinition"]),
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
        resource_defs (Optional[Dict[str, ResourceDefinition]]): A dictionary of string resource
            keys to their implementations. Individual solids may require resources to be present by
            these keys.
        logger_defs (Optional[Dict[str, LoggerDefinition]]): A dictionary of string logger
            identifiers to their implementations.
        executor_defs (Optional[List[ExecutorDefinition]]): The set of executors available when
            executing in this mode. By default, this will be the 'in_process' and 'multiprocess'
            executors (:py:data:`~dagster.default_executors`).
        description (Optional[str]): A human-readable description of the mode.
        intermediate_storage_defs (Optional[List[IntermediateStorageDefinition]]): The set of intermediate storage
            options available when executing in this mode. By default, this will be the 'in_memory'
            and 'filesystem' system storages.
        _config_mapping (Optional[ConfigMapping]): Experimental
        _partitions (Optional[PartitionedConfig]): Experimental
    """

    def __new__(
        cls,
        name: Optional[str] = None,
        resource_defs: Optional[Dict[str, ResourceDefinition]] = None,
        logger_defs: Optional[Dict[str, LoggerDefinition]] = None,
        executor_defs: Optional[List[ExecutorDefinition]] = None,
        description: Optional[str] = None,
        intermediate_storage_defs: Optional[List["IntermediateStorageDefinition"]] = None,
        _config_mapping: Optional[ConfigMapping] = None,
        _partitioned_config: Optional["PartitionedConfig"] = None,
    ):
        from dagster.core.storage.system_storage import default_intermediate_storage_defs

        from .intermediate_storage import IntermediateStorageDefinition
        from .partition import PartitionedConfig

        resource_defs = check.opt_dict_param(
            resource_defs, "resource_defs", key_type=str, value_type=ResourceDefinition
        )

        for key in resource_defs:
            if not key.isidentifier():
                check.failed(f"Resource key '{key}' must be a valid Python identifier.")

        if resource_defs and "io_manager" in resource_defs:
            resource_defs_with_defaults = resource_defs
        else:
            from dagster.core.storage.mem_io_manager import mem_io_manager

            resource_defs_with_defaults = merge_dicts(
                {"io_manager": mem_io_manager}, resource_defs or {}
            )

        if _config_mapping:
            experimental_arg_warning("_config_mapping", "ModeDefinition.__new__")

        if _partitioned_config:
            experimental_arg_warning("_partitioned_config", "ModeDefinition.__new__")

        return super(ModeDefinition, cls).__new__(
            cls,
            name=check_valid_name(name) if name else DEFAULT_MODE_NAME,
            resource_defs=resource_defs_with_defaults,
            loggers=(
                check.opt_dict_param(
                    logger_defs, "logger_defs", key_type=str, value_type=LoggerDefinition
                )
                or default_loggers()
            ),
            intermediate_storage_defs=check.list_param(
                intermediate_storage_defs
                if intermediate_storage_defs
                else default_intermediate_storage_defs,
                "intermediate_storage_defs",
                of_type=IntermediateStorageDefinition,
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

    def get_intermediate_storage_def(self, name):
        check.str_param(name, "name")
        for intermediate_storage_def in self.intermediate_storage_defs:
            if intermediate_storage_def.name == name:
                return intermediate_storage_def

        check.failed("{} storage definition not found".format(name))

    def get_partition_set_def(self, pipeline_name: str) -> Optional["PartitionSetDefinition"]:
        from dagster.core.definitions.partition import PartitionSetDefinition

        if not self.partitioned_config:
            return None

        return PartitionSetDefinition(
            pipeline_name=pipeline_name,
            name=pipeline_name + "_" + self.name + "_partition_set",
            partitions_def=self.partitioned_config.partitions_def,
            run_config_fn_for_partition=self.partitioned_config.run_config_for_partition_fn,
            mode=self.name,
        )

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
