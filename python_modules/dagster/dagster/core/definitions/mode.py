from dagster import check

from dagster.core.loggers import default_loggers

from .logger import LoggerDefinition
from .resource import ResourceDefinition


DEFAULT_MODE_NAME = 'default'


class ModeDefinition:
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
