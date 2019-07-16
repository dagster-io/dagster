from collections import namedtuple

from dagster import check

from dagster.core.types import Field, String
from dagster.core.types.field_utils import check_user_facing_opt_field_param
from .config import resolve_config_field


class ResourceDefinition(object):
    '''Resources are pipeline-scoped ways to make external resources (like database connections)
    available to solids during pipeline execution and clean up after execution resolves.

    Args:
        resource_fn (Callable[[InitResourceContext], Any]):
            User provided function to instantiate the resource. This resource will be available to
            solids via ``context.resources``
        config_field (Field):
            The type for the configuration data for this resource, passed to ``resource_fn`` via
            ``init_context.resource_config``
        description (str)
    '''

    def __init__(self, resource_fn, config_field=None, description=None):
        self._resource_fn = check.callable_param(resource_fn, 'resource_fn')
        self._config_field = check_user_facing_opt_field_param(
            config_field, 'config_field', 'of a ResourceDefinition or @resource'
        )
        self._description = check.opt_str_param(description, 'description')

    @property
    def resource_fn(self):
        return self._resource_fn

    @property
    def config_field(self):
        return self._config_field

    @property
    def description(self):
        return self._description

    @staticmethod
    def none_resource(description=None):
        return ResourceDefinition.hardcoded_resource(value=None, description=description)

    @staticmethod
    def hardcoded_resource(value, description=None):
        return ResourceDefinition(resource_fn=lambda _init_context: value, description=description)

    @staticmethod
    def string_resource(description=None):
        return ResourceDefinition(
            resource_fn=lambda init_context: init_context.resource_config,
            config_field=Field(String),
            description=description,
        )


def resource(config=None, config_field=None, description=None):
    '''A decorator for creating a resource. The decorated function will be used as the
    resource_fn in a ResourceDefinition.

    Args:
        config (Dict[str, Field]):
            The schema for the configuration data to be made available to the resource_fn
        config_field (Field):
            Used in the rare case of a top level config type other than a dictionary.

            Only one of config or config_field can be provided.
        description(str)
    '''

    # This case is for when decorator is used bare, without arguments.
    # E.g. @resource versus @resource()
    if callable(config):
        return ResourceDefinition(resource_fn=config)

    def _wrap(resource_fn):
        return ResourceDefinition(
            resource_fn, resolve_config_field(config_field, config, '@resource'), description
        )

    return _wrap


class ScopedResourcesBuilder(namedtuple('ScopedResourcesBuilder', 'resource_instance_dict')):
    '''There are concepts in the codebase (e.g. solids, system storage) that receive
    only the resources that they have specified in required_resource_keys.
    ScopedResourcesBuilder is responsible for dynamically building a class with
    only those required resources and returning an instance of that class.'''

    def __new__(cls, resource_instance_dict=None):
        return super(ScopedResourcesBuilder, cls).__new__(
            cls,
            resource_instance_dict=check.opt_dict_param(
                resource_instance_dict, 'resource_instance_dict', key_type=str
            ),
        )

    def build(self, mapper_fn=None, required_resource_keys=None):
        '''We dynamically create a type that has the resource keys as properties, to enable dotting into
        the resources from a context.

        For example, given:

        resources = {'foo': <some resource>, 'bar': <some other resource>}

        then this will create the type Resource(namedtuple('foo bar'))

        and then binds the specified resources into an instance of this object, which can be consumed
        as, e.g., context.resources.foo.
        '''
        resource_instance_dict = (
            mapper_fn(self.resource_instance_dict, required_resource_keys)
            if (mapper_fn and required_resource_keys)
            else self.resource_instance_dict
        )

        resource_type = namedtuple('Resources', list(resource_instance_dict.keys()))
        return resource_type(**resource_instance_dict)
