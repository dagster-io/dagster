from dagster import check

from .resource import ResourceDefinition


class ModeDefinition:
    def __init__(self, name='default', resources=None, description=None):
        self.name = check.str_param(name, 'name')
        self.resource_defs = check.opt_dict_param(
            resources, 'resources', key_type=str, value_type=ResourceDefinition
        )
        self.description = check.opt_str_param(description, 'description')
