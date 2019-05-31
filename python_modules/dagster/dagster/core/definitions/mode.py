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
        loggers (Optiona[List[LoggerDefinition]]): The set of loggers to use in this mode.
        description (Optional[str])
    '''

    def __init__(self, name=DEFAULT_MODE_NAME, resources=None, loggers=None, description=None):
        self.name = check.str_param(name, 'name')
        self.resource_defs = check.opt_dict_param(
            resources, 'resources', key_type=str, value_type=ResourceDefinition
        )
        self.loggers = (
            check.opt_dict_param(loggers, 'loggers', key_type=str, value_type=LoggerDefinition)
            or default_loggers()
        )
        self.description = check.opt_str_param(description, 'description')
