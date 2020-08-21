import warnings
from collections import namedtuple

from dagster import check
from dagster.core.definitions.executor import ExecutorDefinition, default_executors
from dagster.loggers import default_loggers

from .logger import LoggerDefinition
from .resource import ResourceDefinition

DEFAULT_MODE_NAME = "default"


class ModeDefinition(
    namedtuple(
        "_ModeDefinition",
        "name resource_defs loggers system_storage_defs executor_defs description intermediate_storage_defs",
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
        system_storage_defs (Optional[List[SystemStorageDefinition]]): The set of system storage
            options available when executing in this mode. By default, this will be the 'in_memory'
            and 'filesystem' system storages.
        executor_defs (Optional[List[ExecutorDefinition]]): The set of executors available when
            executing in this mode. By default, this will be the 'in_process' and 'multiprocess'
            executors (:py:data:`~dagster.default_executors`).
        description (Optional[str]): A human-readable description of the mode.
        intermediate_storage_defs (Optional[List[IntermediateStorageDefinition]]): The set of intermediate storage
            options available when executing in this mode. By default, this will be the 'in_memory'
            and 'filesystem' system storages.
    """

    def __new__(
        cls,
        name=None,
        resource_defs=None,
        logger_defs=None,
        system_storage_defs=None,
        executor_defs=None,
        description=None,
        intermediate_storage_defs=None,
    ):
        from dagster.core.storage.system_storage import (
            default_system_storage_defs,
            default_intermediate_storage_defs,
        )

        from .system_storage import SystemStorageDefinition
        from .intermediate_storage import IntermediateStorageDefinition

        if system_storage_defs is not None and intermediate_storage_defs is None:
            warnings.warn(
                "system_storage_defs are deprecated and will be removed in 0.10.0 "
                "and should be replaced with "
                "intermediate_storage_defs for intermediates and resource_defs for files"
            )

        return super(ModeDefinition, cls).__new__(
            cls,
            name=check.opt_str_param(name, "name", DEFAULT_MODE_NAME),
            resource_defs=check.opt_dict_param(
                resource_defs, "resource_defs", key_type=str, value_type=ResourceDefinition
            ),
            loggers=(
                check.opt_dict_param(
                    logger_defs, "logger_defs", key_type=str, value_type=LoggerDefinition
                )
                or default_loggers()
            ),
            system_storage_defs=check.list_param(
                system_storage_defs if system_storage_defs else default_system_storage_defs,
                "system_storage_defs",
                of_type=SystemStorageDefinition,
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
        )

    @property
    def resource_key_set(self):
        return frozenset(self.resource_defs.keys())

    def get_system_storage_def(self, name):
        check.str_param(name, "name")
        for system_storage_def in self.system_storage_defs:
            if system_storage_def.name == name:
                return system_storage_def

        check.failed("{} storage definition not found".format(name))

    def get_intermediate_storage_def(self, name):
        check.str_param(name, "name")
        for intermediate_storage_def in self.intermediate_storage_defs:
            if intermediate_storage_def.name == name:
                return intermediate_storage_def

        check.failed("{} storage definition not found".format(name))

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
