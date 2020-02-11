from collections import namedtuple
from functools import update_wrapper

from dagster import check
from dagster.config.field_utils import check_user_facing_opt_config_param
from dagster.core.definitions.config import is_callable_valid_config_arg
from dagster.core.errors import DagsterUnknownResourceError


class ResourceDefinition(object):
    '''Core class for defining resources.

    Resources are scoped ways to make external resources (like database connections) available to
    solids during pipeline execution and to clean up after execution resolves.

    If resource_fn yields once rather than returning (in the manner of functions decorable with
    :py:func:`@contextlib.contextmanager <python:contextlib.contextmanager>`) then the body of the
    function after the yield will be run after execution resolves, allowing users to write their
    own teardown/cleanup logic.

    Depending on your executor, resources may be instantiated and cleaned up more than once in a
    pipeline execution.

    Args:
        resource_fn (Callable[[InitResourceContext], Any]): User-provided function to instantiate
            the resource, which will be made available to solid executions keyed on the
            ``context.resources`` object.
        config (Optional[Any]): The schema for the config. Configuration data available in
            `init_context.resource_config`.

            This value can be:

            1. A Python primitive type that resolve to dagster config
               types: int, float, bool, str.

            2. A dagster config type: Int, Float, Bool,
               :py:class:`Array`, :py:class:`Noneable`, :py:class:`Selector`,
               :py:class:`Shape`, :py:class:`Permissive`, etc

            3. A bare python dictionary, which is wrapped in :py:class:`Shape`. Any
               values in the dictionary get resolved by the same rules, recursively.

            4. A bare python list of length one which itself is config type.
               Becomes :py:class:`Array` with list element as an argument.

            5. A instance of :py:class:`Field`.

        description (Optional[str]): A human-readable description of the resource.
    '''

    def __init__(self, resource_fn, config=None, description=None):
        self._resource_fn = check.callable_param(resource_fn, 'resource_fn')
        self._config_field = check_user_facing_opt_config_param(config, 'config')
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
            config=str,
            description=description,
        )


class _ResourceDecoratorCallable(object):
    def __init__(self, config=None, description=None):
        self.config = check_user_facing_opt_config_param(config, 'config')
        self.description = check.opt_str_param(description, 'description')

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        resource_def = ResourceDefinition(
            resource_fn=fn, config=self.config, description=self.description,
        )

        update_wrapper(resource_def, wrapped=fn)

        return resource_def


def resource(config=None, description=None):
    '''Define a resource.

    The decorated function should accept an :py:class:`InitResourceContext` and return an instance of
    the resource. This function will become the ``resource_fn`` of an underlying
    :py:class:`ResourceDefinition`.

    If the decorated function yields once rather than returning (in the manner of functions
    decorable with :py:func:`@contextlib.contextmanager <python:contextlib.contextmanager>`) then
    the body of the function after the yield will be run after execution resolves, allowing users
    to write their own teardown/cleanup logic.

    Args:
        config (Optional[Any]): The schema for the config. Configuration data available in
            `init_context.resource_config`.

            1. A Python primitive type that resolve to dagster config
               types: int, float, bool, str.

            2. A dagster config type: Int, Float, Bool,
               :py:class:`Array`, :py:class:`Noneable`, :py:class:`Selector`,
               :py:class:`Shape`, :py:class:`Permissive`, etc

            3. A bare python dictionary, which is wrapped in :py:class:`Shape`. Any
               values in the dictionary get resolved by the same rules, recursively.

            4. A bare python list of length one which itself is config type.
               Becomes :py:class:`Array` with list element as an argument.

            5. A instance of :py:class:`Field`.

        description(Optional[str]): A human-readable description of the resource.
    '''

    # This case is for when decorator is used bare, without arguments.
    # E.g. @resource versus @resource()
    if callable(config) and not is_callable_valid_config_arg(config):
        return _ResourceDecoratorCallable()(config)

    def _wrap(resource_fn):
        return _ResourceDecoratorCallable(config=config, description=description)(resource_fn)

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

    def build(self, required_resource_keys):

        '''We dynamically create a type that has the resource keys as properties, to enable dotting into
        the resources from a context.

        For example, given:

        resources = {'foo': <some resource>, 'bar': <some other resource>}

        then this will create the type Resource(namedtuple('foo bar'))

        and then binds the specified resources into an instance of this object, which can be consumed
        as, e.g., context.resources.foo.
        '''
        required_resource_keys = check.opt_set_param(
            required_resource_keys, 'required_resource_keys', of_type=str
        )
        # it is possible that the surrounding context does NOT have the required resource keys
        # because we are building a context for steps that we are not going to execute (e.g. in the
        # resume/retry case, in order to generate copy intermediates events)
        resource_instance_dict = {
            key: self.resource_instance_dict[key]
            for key in required_resource_keys
            if key in self.resource_instance_dict
        }

        class ScopedResources(namedtuple('Resources', list(resource_instance_dict.keys()))):
            def __getattr__(self, attr):
                raise DagsterUnknownResourceError(attr)

        return ScopedResources(**resource_instance_dict)
