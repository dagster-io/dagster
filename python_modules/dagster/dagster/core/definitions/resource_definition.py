from functools import update_wrapper
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union,
    cast,
    overload,
)

import dagster._check as check
from dagster.config.config_schema import ConfigSchemaType
from dagster.core.decorator_utils import format_docstring_for_description
from dagster.core.definitions.config import is_callable_valid_config_arg
from dagster.core.definitions.configurable import AnonymousConfigurableDefinition
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvalidInvocationError
from dagster.seven import funcsigs
from dagster.utils.backcompat import experimental_arg_warning

from ..decorator_utils import (
    get_function_params,
    is_required_param,
    positional_arg_name_list,
    validate_expected_params,
)
from .definition_config_schema import (
    IDefinitionConfigSchema,
    convert_user_facing_definition_config_schema,
)
from .resource_invocation import resource_invocation_result

# pylint: disable=unused-import
from .scoped_resources_builder import (  # type: ignore
    IContainsGenerator,
    Resources,
    ScopedResourcesBuilder,
)

if TYPE_CHECKING:
    from dagster.core.execution.resources_init import InitResourceContext


def is_context_provided(params: List[funcsigs.Parameter]) -> bool:
    return len(params) >= 1


class ResourceDefinition(AnonymousConfigurableDefinition):
    """Core class for defining resources.

    Resources are scoped ways to make external resources (like database connections) available to
    during job execution and to clean up after execution resolves.

    If resource_fn yields once rather than returning (in the manner of functions decorable with
    :py:func:`@contextlib.contextmanager <python:contextlib.contextmanager>`) then the body of the
    function after the yield will be run after execution resolves, allowing users to write their
    own teardown/cleanup logic.

    Depending on your executor, resources may be instantiated and cleaned up more than once in a
    job execution.

    Args:
        resource_fn (Callable[[InitResourceContext], Any]): User-provided function to instantiate
            the resource, which will be made available to executions keyed on the
            ``context.resources`` object.
        config_schema (Optional[ConfigSchema): The schema for the config. If set, Dagster will check
            that config provided for the resource matches this schema and fail if it does not. If
            not set, Dagster will accept any config provided for the resource.
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
        resource_fn: Callable[["InitResourceContext"], Any],
        config_schema: Optional[Union[Any, ConfigSchemaType]] = None,
        description: Optional[str] = None,
        required_resource_keys: Optional[AbstractSet[str]] = None,
        version: Optional[str] = None,
    ):
        self._resource_fn = check.callable_param(resource_fn, "resource_fn")
        self._config_schema = convert_user_facing_definition_config_schema(config_schema)
        self._description = check.opt_str_param(description, "description")
        self._required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys"
        )
        self._version = check.opt_str_param(version, "version")
        if version:
            experimental_arg_warning("version", "ResourceDefinition.__init__")

    @property
    def resource_fn(self) -> Callable[..., Any]:
        return self._resource_fn

    @property
    def config_schema(self) -> IDefinitionConfigSchema:
        return self._config_schema

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def version(self) -> Optional[str]:
        return self._version

    @property
    def required_resource_keys(self) -> AbstractSet[str]:
        return self._required_resource_keys

    @staticmethod
    def none_resource(description: Optional[str] = None) -> "ResourceDefinition":
        """A helper function that returns a none resource.

        Args:
            description ([Optional[str]]): The description of the resource. Defaults to None.

        Returns:
            [ResourceDefinition]: A resource that does nothing.
        """
        return ResourceDefinition.hardcoded_resource(value=None, description=description)

    @staticmethod
    def hardcoded_resource(value: Any, description: Optional[str] = None) -> "ResourceDefinition":
        """A helper function that creates a ``ResourceDefinition`` with a hardcoded object.

        Args:
            value (Any): The value that will be accessible via context.resources.resource_name.
            description ([Optional[str]]): The description of the resource. Defaults to None.

        Returns:
            [ResourceDefinition]: A hardcoded resource.
        """
        return ResourceDefinition(resource_fn=lambda _init_context: value, description=description)

    @staticmethod
    def mock_resource(description: Optional[str] = None) -> "ResourceDefinition":
        """A helper function that creates a ``ResourceDefinition`` which wraps a ``mock.MagicMock``.

        Args:
            description ([Optional[str]]): The description of the resource. Defaults to None.

        Returns:
            [ResourceDefinition]: A resource that creates the magic methods automatically and helps
                you mock existing resources.
        """
        from unittest import mock

        return ResourceDefinition(
            resource_fn=lambda _init_context: mock.MagicMock(), description=description
        )

    @staticmethod
    def string_resource(description: Optional[str] = None) -> "ResourceDefinition":
        return ResourceDefinition(
            resource_fn=lambda init_context: init_context.resource_config,
            config_schema=str,
            description=description,
        )

    def copy_for_configured(
        self, description: Optional[str], config_schema: IDefinitionConfigSchema, _
    ) -> "ResourceDefinition":
        return ResourceDefinition(
            config_schema=config_schema,
            description=description or self.description,
            resource_fn=self.resource_fn,
            required_resource_keys=self.required_resource_keys,
            version=self.version,
        )

    def __call__(self, *args, **kwargs):
        from dagster.core.execution.resources_init import InitResourceContext

        context_provided = is_context_provided(get_function_params(self.resource_fn))

        if context_provided:
            if len(args) + len(kwargs) == 0:
                raise DagsterInvalidInvocationError(
                    "Resource initialization function has context argument, but no context was provided "
                    "when invoking."
                )
            if len(args) + len(kwargs) > 1:
                raise DagsterInvalidInvocationError(
                    "Initialization of resource received multiple arguments. Only a first "
                    "positional context parameter should be provided when invoking."
                )

            context_param_name = get_function_params(self.resource_fn)[0].name

            if args:
                check.opt_inst_param(args[0], context_param_name, InitResourceContext)
                return resource_invocation_result(self, args[0])
            else:
                if context_param_name not in kwargs:
                    raise DagsterInvalidInvocationError(
                        f"Resource initialization expected argument '{context_param_name}'."
                    )
                check.opt_inst_param(
                    kwargs[context_param_name], context_param_name, InitResourceContext
                )

                return resource_invocation_result(self, kwargs[context_param_name])
        else:
            return resource_invocation_result(self, None)


class _ResourceDecoratorCallable:
    def __init__(
        self,
        config_schema: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        required_resource_keys: Optional[AbstractSet[str]] = None,
        version: Optional[str] = None,
    ):
        self.config_schema = config_schema  # checked by underlying definition
        self.description = check.opt_str_param(description, "description")
        self.version = check.opt_str_param(version, "version")
        self.required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys"
        )

    def __call__(self, resource_fn: Callable[["InitResourceContext"], Any]):
        check.callable_param(resource_fn, "resource_fn")

        any_name = ["*"] if is_context_provided(get_function_params(resource_fn)) else []

        params = get_function_params(resource_fn)

        missing_positional = validate_expected_params(params, any_name)
        if missing_positional:
            raise DagsterInvalidDefinitionError(
                f"@resource decorated function '{resource_fn.__name__}' expects a single "
                "positional argument."
            )

        extras = params[len(any_name) :]

        required_extras = list(filter(is_required_param, extras))
        if required_extras:
            raise DagsterInvalidDefinitionError(
                f"@resource decorated function '{resource_fn.__name__}' expects only a single positional required argument. "
                f"Got required extra params {', '.join(positional_arg_name_list(required_extras))}"
            )

        resource_def = ResourceDefinition(
            resource_fn=resource_fn,
            config_schema=self.config_schema,
            description=self.description or format_docstring_for_description(resource_fn),
            version=self.version,
            required_resource_keys=self.required_resource_keys,
        )

        update_wrapper(resource_def, wrapped=resource_fn)

        return resource_def


@overload
def resource(config_schema=Callable[["InitResourceContext"], Any]) -> ResourceDefinition:
    ...


@overload
def resource(
    config_schema: Optional[ConfigSchemaType] = ...,
    description: Optional[str] = ...,
    required_resource_keys: Optional[AbstractSet[str]] = ...,
    version: Optional[str] = ...,
) -> Callable[[Callable[["InitResourceContext"], Any]], "ResourceDefinition"]:
    ...


def resource(
    config_schema: Union[Callable[["InitResourceContext"], Any], Optional[ConfigSchemaType]] = None,
    description: Optional[str] = None,
    required_resource_keys: Optional[AbstractSet[str]] = None,
    version: Optional[str] = None,
) -> Union[
    Callable[[Callable[["InitResourceContext"], Any]], "ResourceDefinition"], "ResourceDefinition"
]:
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
            `init_context.resource_config`. If not set, Dagster will accept any config provided.
        description(Optional[str]): A human-readable description of the resource.
        version (Optional[str]): (Experimental) The version of a resource function. Two wrapped
            resource functions should only have the same version if they produce the same resource
            definition when provided with the same inputs.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by this resource.
    """

    # This case is for when decorator is used bare, without arguments.
    # E.g. @resource versus @resource()
    if callable(config_schema) and not is_callable_valid_config_arg(config_schema):
        return _ResourceDecoratorCallable()(config_schema)  # type: ignore

    def _wrap(resource_fn: Callable[["InitResourceContext"], Any]) -> "ResourceDefinition":
        return _ResourceDecoratorCallable(
            config_schema=cast(Optional[Dict[str, Any]], config_schema),
            description=description,
            required_resource_keys=required_resource_keys,
            version=version,
        )(resource_fn)

    return _wrap


def make_values_resource(**kwargs: Any) -> ResourceDefinition:
    """A helper function that creates a ``ResourceDefinition`` to take in user-defined values.

        This is useful for sharing values between ops.

    Args:
        **kwargs: Arbitrary keyword arguments that will be passed to the config schema of the
            returned resource definition. If not set, Dagster will accept any config provided for
            the resource.

    For example:

    .. code-block:: python

        @op(required_resource_keys={"globals"})
        def my_op(context):
            print(context.resources.globals["my_str_var"])

        @job(resource_defs={"globals": make_values_resource(my_str_var=str, my_int_var=int)})
        def my_job():
            my_op()

    Returns:
        ResourceDefinition: A resource that passes in user-defined values.
    """

    return ResourceDefinition(
        resource_fn=lambda init_context: init_context.resource_config,
        config_schema=kwargs or Any,
    )
