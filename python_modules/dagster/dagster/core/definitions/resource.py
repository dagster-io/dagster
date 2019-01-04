from dagster import check

from dagster.core import types


class ResourceDefinition(object):
    def __init__(self, resource_fn, config_field=None, description=None):
        self.resource_fn = check.callable_param(resource_fn, 'resource_fn')
        self.config_field = check.opt_inst_param(config_field, 'config_field', types.Field)
        self.description = check.opt_str_param(description, 'description')

    @staticmethod
    def null_resource():
        return ResourceDefinition(resource_fn=lambda _info: None)

    @staticmethod
    def string_resource(description=None):
        return ResourceDefinition(
            resource_fn=lambda info: info.config,
            config_field=types.Field(types.String),
            description=description,
        )
