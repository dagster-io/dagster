from collections import namedtuple
from functools import update_wrapper

from dagster import check
from dagster.core.definitions.config import is_callable_valid_config_arg
from dagster.core.definitions.configurable import AnonymousConfigurableDefinition
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterUnknownResourceError
from dagster.utils.backcompat import experimental_arg_warning

from ..decorator_utils import split_function_parameters, validate_decorated_fn_positionals
from .definition_config_schema import convert_user_facing_definition_config_schema


class ResourceDefinition(AnonymousConfigurableDefinition):
    """Core class for defining resources.

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
        config_schema (Optional[ConfigSchema]): The schema for the config. Configuration data
            available in `init_context.resource_config`.
        description (Optional[str]): A human-readable description of the resource.
        required_resource_keys: (Optional[Set[str]]) Keys for the resources required by this
            resource. A DagsterInvariantViolationError will be raised during initialization if
            dependencies are cyclic.
        version (Optional[str]): (Experimental) The version of the resource's definition fn. Two
            wrapped resource functions should only have the same version if they produce the same
            resource definition when provided with the same inputs.
    """

    def __init__(
        self,
        resource_fn=None,
        config_schema=None,
        description=None,
        required_resource_keys=None,
        version=None,
    ):
        EXPECTED_POSITIONALS = ["*"]
        fn_positionals, _ = split_function_parameters(resource_fn, EXPECTED_POSITIONALS)
        missing_positional = validate_decorated_fn_positionals(fn_positionals, EXPECTED_POSITIONALS)

        if missing_positional:
            raise DagsterInvalidDefinitionError(
                "@resource '{resource_name}' decorated function does not have required "
                "positional parameter '{missing_param}'. Resource functions should only have keyword "
                "arguments that match input names and a first positional parameter.".format(
                    resource_name=resource_fn.__name__, missing_param=missing_positional
                )
            )

        self._resource_fn = check.opt_callable_param(resource_fn, "resource_fn")
        self._config_schema = convert_user_facing_definition_config_schema(config_schema)
        self._description = check.opt_str_param(description, "description")
        self._required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys"
        )
        self._version = check.opt_str_param(version, "version")
        if version:
            experimental_arg_warning("version", "ResourceDefinition.__init__")

    @property
    def resource_fn(self):
        return self._resource_fn

    @property
    def config_schema(self):
        return self._config_schema

    @property
    def description(self):
        return self._description

    @property
    def version(self):
        return self._version

    @property
    def required_resource_keys(self):
        return self._required_resource_keys

    @staticmethod
    def none_resource(description=None):
        """A helper function that returns a none resource.

        Args:
            description ([Optional[str]]): The description of the resource. Defaults to None.

        Returns:
            [ResourceDefinition]: A resource that does nothing.
        """
        return ResourceDefinition.hardcoded_resource(value=None, description=description)

    @staticmethod
    def hardcoded_resource(value, description=None):
        """A helper function that creates a ``ResourceDefinition`` with a hardcoded object.

        Args:
            value (Any): A hardcoded object which helps mock the resource.
            description ([Optional[str]]): The description of the resource. Defaults to None.

        Returns:
            [ResourceDefinition]: A hardcoded resource.
        """
        return ResourceDefinition(resource_fn=lambda _init_context: value, description=description)

    @staticmethod
    def mock_resource(description=None):
        """A helper function that creates a ``ResourceDefinition`` which wraps a ``mock.MagicMock``.

        Args:
            description ([Optional[str]]): The description of the resource. Defaults to None.

        Returns:
            [ResourceDefinition]: A resource that creates the magic methods automatically and helps
                you mock existing resources.
        """
        from unittest import mock

        return ResourceDefinition.hardcoded_resource(
            value=mock.MagicMock(), description=description
        )

    @staticmethod
    def string_resource(description=None):
        return ResourceDefinition(
            resource_fn=lambda init_context: init_context.resource_config,
            config_schema=str,
            description=description,
        )

    def copy_for_configured(self, description, config_schema, _):
        return ResourceDefinition(
            config_schema=config_schema,
            description=description or self.description,
            resource_fn=self.resource_fn,
            required_resource_keys=self.required_resource_keys,
        )


class _ResourceDecoratorCallable:
    def __init__(
        self,
        config_schema=None,
        description=None,
        required_resource_keys=None,
        version=None,
    ):
        self.config_schema = config_schema  # checked by underlying definition
        self.description = check.opt_str_param(description, "description")
        self.version = check.opt_str_param(version, "version")
        self.required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys"
        )

    def __call__(self, fn):
        check.callable_param(fn, "fn")

        resource_def = ResourceDefinition(
            resource_fn=fn,
            config_schema=self.config_schema,
            description=self.description,
            version=self.version,
            required_resource_keys=self.required_resource_keys,
        )

        update_wrapper(resource_def, wrapped=fn)

        return resource_def


def resource(config_schema=None, description=None, required_resource_keys=None, version=None):
    """Define a resource.

    The decorated function should accept an :py:class:`InitResourceContext` and return an instance of
    the resource. This function will become the ``resource_fn`` of an underlying
    :py:class:`ResourceDefinition`.

    If the decorated function yields once rather than returning (in the manner of functions
    decorable with :py:func:`@contextlib.contextmanager <python:contextlib.contextmanager>`) then
    the body of the function after the yield will be run after execution resolves, allowing users
    to write their own teardown/cleanup logic.

    Args:
        config_schema (Optional[ConfigSchema]): The schema for the config. Configuration data available in
            `init_context.resource_config`.
        description(Optional[str]): A human-readable description of the resource.
        version (Optional[str]): (Experimental) The version of a resource function. Two wrapped
            resource functions should only have the same version if they produce the same resource
            definition when provided with the same inputs.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by this resource.
    """

    # This case is for when decorator is used bare, without arguments.
    # E.g. @resource versus @resource()
    if callable(config_schema) and not is_callable_valid_config_arg(config_schema):
        return _ResourceDecoratorCallable()(config_schema)

    def _wrap(resource_fn):
        return _ResourceDecoratorCallable(
            config_schema=config_schema,
            description=description,
            required_resource_keys=required_resource_keys,
            version=version,
        )(resource_fn)

    return _wrap


class ScopedResourcesBuilder(namedtuple("ScopedResourcesBuilder", "resource_instance_dict")):
    """There are concepts in the codebase (e.g. solids, system storage) that receive
    only the resources that they have specified in required_resource_keys.
    ScopedResourcesBuilder is responsible for dynamically building a class with
    only those required resources and returning an instance of that class."""

    def __new__(cls, resource_instance_dict=None):
        return super(ScopedResourcesBuilder, cls).__new__(
            cls,
            resource_instance_dict=check.opt_dict_param(
                resource_instance_dict, "resource_instance_dict", key_type=str
            ),
        )

    def build(self, required_resource_keys):

        """We dynamically create a type that has the resource keys as properties, to enable dotting into
        the resources from a context.

        For example, given:

        resources = {'foo': <some resource>, 'bar': <some other resource>}

        then this will create the type Resource(namedtuple('foo bar'))

        and then binds the specified resources into an instance of this object, which can be consumed
        as, e.g., context.resources.foo.
        """
        required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys", of_type=str
        )
        # it is possible that the surrounding context does NOT have the required resource keys
        # because we are building a context for steps that we are not going to execute (e.g. in the
        # resume/retry case, in order to generate copy intermediates events)
        resource_instance_dict = {
            key: self.resource_instance_dict[key]
            for key in required_resource_keys
            if key in self.resource_instance_dict
        }

        class ScopedResources(namedtuple("Resources", list(resource_instance_dict.keys()))):
            def __getattr__(self, attr):
                raise DagsterUnknownResourceError(attr)

        return ScopedResources(**resource_instance_dict)
