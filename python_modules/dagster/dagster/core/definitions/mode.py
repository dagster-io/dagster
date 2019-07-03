from dagster import check
from dagster.loggers import default_loggers

from .logger import LoggerDefinition
from .resource import ResourceDefinition


DEFAULT_MODE_NAME = 'default'


class ModeDefinition:
    '''Defines a "mode" in which a pipeline can operate.
    A mode provides a set of resource implementations as well as configuration for logging.

    Args:
        name (Optional[str]): The name of the mode, defaults to 'default'.
        resources (Optional[List[ResourceDefinition]]): The set of resources for this mode.
        loggers (Optional[List[LoggerDefinition]]): The set of loggers to use in this mode.
        system_storage_defs (Optional[List[SystemStorageDefinition]]): The set of system storage
            options available when executing in this mode. Defaults to 'in_memory' and 'filesystem'.
        description (Optional[str])
    '''

    def __init__(
        self,
        name=DEFAULT_MODE_NAME,
        resource_defs=None,
        logger_defs=None,
        system_storage_defs=None,
        description=None,
    ):
        from .system_storage import SystemStorageDefinition, mem_system_storage, fs_system_storage

        self.name = check.str_param(name, 'name')
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
            system_storage_defs if system_storage_defs else [mem_system_storage, fs_system_storage],
            'system_storage_def',
            of_type=SystemStorageDefinition,
        )
        self.description = check.opt_str_param(description, 'description')

    def get_system_storage_def(self, name):
        check.str_param(name, 'name')
        for system_storage_def in self.system_storage_defs:
            if system_storage_def.name == name:
                return system_storage_def

        check.failed('{} storage definition not found'.format(name))
