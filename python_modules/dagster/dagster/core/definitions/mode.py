from dagster import check
from dagster.core.definitions.executor import ExecutorDefinition, default_executors
from dagster.loggers import default_loggers

from .logger import LoggerDefinition
from .resource import ResourceDefinition

DEFAULT_MODE_NAME = 'default'


class ModeDefinition:
    '''Defines a "mode" in which a pipeline can operate.
    A mode provides a set of resource implementations as well as configuration for logging.

    Args:
        name (Optional[str]): The name of the mode, defaults to 'default'.
        resource_defs (Optional[Dict[str, ResourceDefinition]]):
            The set of resources for this mode keyed by unique identifiers.
        logger_defs (Optional[Dict[str, LoggerDefinition]]):
            The set of loggers to use in this mode keyed by unique identifiers.
        system_storage_defs (Optional[List[SystemStorageDefinition]]): The set of system storage
            options available when executing in this mode. Defaults to 'in_memory' and 'filesystem'.
        executor_defs (Optional[List[ExecutorDefinition]]): The set of executors available when
            executing in this mode. Defaults to 'in_process' and 'multiprocess'.
        description (Optional[str])
    '''

    def __init__(
        self,
        name=None,
        resource_defs=None,
        logger_defs=None,
        system_storage_defs=None,
        executor_defs=None,
        description=None,
    ):
        from .system_storage import default_system_storage_defs, SystemStorageDefinition

        self.name = check.opt_str_param(name, 'name', DEFAULT_MODE_NAME)
        self.resource_defs = check.opt_dict_param(
            resource_defs, 'resource_defs', key_type=str, value_type=ResourceDefinition
        )
        self.loggers = (
            check.opt_dict_param(
                logger_defs, 'logger_defs', key_type=str, value_type=LoggerDefinition
            )
            or default_loggers()
        )
        self.system_storage_defs = check.list_param(
            system_storage_defs if system_storage_defs else default_system_storage_defs,
            'system_storage_defs',
            of_type=SystemStorageDefinition,
        )
        self.executor_defs = check.list_param(
            executor_defs if executor_defs else default_executors,
            'executor_defs',
            of_type=ExecutorDefinition,
        )
        self.description = check.opt_str_param(description, 'description')

    def get_system_storage_def(self, name):
        check.str_param(name, 'name')
        for system_storage_def in self.system_storage_defs:
            if system_storage_def.name == name:
                return system_storage_def

        check.failed('{} storage definition not found'.format(name))

    @staticmethod
    def from_resources(resources, name=None):
        check.dict_param(resources, 'resources', key_type=str)

        return ModeDefinition(
            name=name,
            resource_defs={
                resource_name: ResourceDefinition.hardcoded_resource(resource)
                for resource_name, resource in resources.items()
            },
        )
