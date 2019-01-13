from dagster import check

from dagster.core.types import Field, String
from dagster.core.types.field_utils import check_opt_field_param


class ResourceDefinition(object):
    def __init__(self, resource_fn, config_field=None, description=None):
        self.resource_fn = check.callable_param(resource_fn, 'resource_fn')
        self.config_field = check_opt_field_param(config_field, 'config_field')
        self.description = check.opt_str_param(description, 'description')

    @staticmethod
    def none_resource(description=None):
        return ResourceDefinition(resource_fn=lambda _info: None, description=description)

    @staticmethod
    def string_resource(description=None):
        return ResourceDefinition(
            resource_fn=lambda info: info.config,
            config_field=Field(String),
            description=description,
        )
