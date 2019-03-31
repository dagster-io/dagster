from dagster import check

from dagster.core.types import Field, String
from dagster.core.types.field_utils import check_user_facing_opt_field_param


class ResourceDefinition(object):
    def __init__(self, resource_fn, config_field=None, description=None):
        self.resource_fn = check.callable_param(resource_fn, 'resource_fn')
        self.config_field = check_user_facing_opt_field_param(
            config_field, 'config_field', 'ResourceDefinition or @resource'
        )
        self.description = check.opt_str_param(description, 'description')

    @staticmethod
    def none_resource(description=None):
        return ResourceDefinition(resource_fn=lambda _init_context: None, description=description)

    @staticmethod
    def string_resource(description=None):
        return ResourceDefinition(
            resource_fn=lambda init_context: init_context.resource_config,
            config_field=Field(String),
            description=description,
        )


def resource(config_field=None, description=None):
    # This case is for when decorator is used bare, without arguments.
    # E.g. @resource versus @resource()
    if callable(config_field):
        return ResourceDefinition(resource_fn=config_field)

    def _wrap(resource_fn):
        return ResourceDefinition(resource_fn, config_field, description)

    return _wrap
