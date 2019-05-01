from collections import namedtuple
from enum import Enum

from dagster import check

from dagster.core.types import Field, String
from dagster.core.types.field_utils import check_user_facing_opt_field_param


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
        self.resource_fn = check.callable_param(resource_fn, 'resource_fn')
        self.config_field = check_user_facing_opt_field_param(
            config_field, 'config_field', 'of a ResourceDefinition or @resource'
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
    '''A decorator for creating a resource. The decorated function will be used as the
    resource_fn in a ResourceDefinition.
    '''

    # This case is for when decorator is used bare, without arguments.
    # E.g. @resource versus @resource()
    if callable(config_field):
        return ResourceDefinition(resource_fn=config_field)

    def _wrap(resource_fn):
        return ResourceDefinition(resource_fn, config_field, description)

    return _wrap


class ResourcesSource(Enum):
    '''Resources can either be created via a pipeline context definition:

    context=PipelineContextDefinition(resources={'foo': <some resource>})

    --or-- (less commonly) via a custom execution context:

    PipelineContextDefinition(
        context_fn=lambda init_context: ExecutionContext(
            resources=<something>
        ),
    )
    '''

    PIPELINE_CONTEXT_DEF = 'PIPELINE_CONTEXT_DEF'
    CUSTOM_EXECUTION_CONTEXT = 'CUSTOM_EXECUTION_CONTEXT'


class ResourcesBuilder(namedtuple('ResourcesBuilder', 'src resources_type')):
    def __new__(cls, src, resources_type):
        return super(ResourcesBuilder, cls).__new__(cls, src, resources_type)

    def build(self, mapper_fn=None, resource_deps=None):
        '''We dynamically create a type that has the resource keys as properties, to enable dotting into
        the resources from a context.

        For example, given:

        resources = {'foo': <some resource>, 'bar': <some other resource>}

        then this will create the type Resource(namedtuple('foo bar'))

        and then binds the specified resources into an instance of this object, which can be consumed
        as, e.g., context.resources.foo.
        '''
        if self.resources_type == ResourcesSource.PIPELINE_CONTEXT_DEF and self.src is not None:
            src = mapper_fn(self.src, resource_deps) if (mapper_fn and resource_deps) else self.src

            resource_type = namedtuple('Resources', list(src.keys()))
            return resource_type(**src)
        elif self.resources_type == ResourcesSource.CUSTOM_EXECUTION_CONTEXT:
            return self.src
        else:
            return None
