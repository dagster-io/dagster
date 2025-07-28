from abc import abstractmethod
from functools import update_wrapper
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Optional,
    Union,
    cast,
    overload,
)

from typing_extensions import TypeAlias, TypeGuard

import dagster._check as check
from dagster._annotations import public
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.config import is_callable_valid_config_arg
from dagster._core.definitions.definition_config_schema import (
    CoercableToConfigSchema,
    IDefinitionConfigSchema,
    convert_user_facing_definition_config_schema,
)
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.storage.input_manager import IInputManagerDefinition, InputManager
from dagster._core.storage.output_manager import IOutputManagerDefinition, OutputManager

if TYPE_CHECKING:
    from dagster._config import UserConfigSchema
    from dagster._core.execution.context.init import InitResourceContext
    from dagster._core.execution.context.input import InputContext
    from dagster._core.execution.context.output import OutputContext

IOManagerFunctionWithContext = Callable[["InitResourceContext"], "IOManager"]
IOManagerFunction: TypeAlias = Union[
    IOManagerFunctionWithContext,
    Callable[[], "IOManager"],
]


def is_io_manager_context_provided(
    fn: IOManagerFunction,
) -> TypeGuard[IOManagerFunctionWithContext]:
    return len(get_function_params(fn)) >= 1


@public
class IOManagerDefinition(ResourceDefinition, IInputManagerDefinition, IOutputManagerDefinition):
    """Definition of an IO manager resource.

    IOManagers are used to store op outputs and load them as inputs to downstream ops.

    An IOManagerDefinition is a :py:class:`ResourceDefinition` whose `resource_fn` returns an
    :py:class:`IOManager`.

    The easiest way to create an IOManagerDefnition is with the :py:func:`@io_manager <io_manager>`
    decorator.
    """

    def __init__(
        self,
        resource_fn: IOManagerFunction,
        config_schema: CoercableToConfigSchema = None,
        description: Optional[str] = None,
        required_resource_keys: Optional[AbstractSet[str]] = None,
        version: Optional[str] = None,
        input_config_schema: CoercableToConfigSchema = None,
        output_config_schema: CoercableToConfigSchema = None,
    ):
        self._input_config_schema = convert_user_facing_definition_config_schema(
            input_config_schema
        )
        # Unlike other configurable objects, whose config schemas default to Any,
        # output_config_schema defaults to None. This the because IOManager input / output config
        # shares config namespace with dagster type loaders.
        self._output_config_schema = (
            convert_user_facing_definition_config_schema(output_config_schema)
            if output_config_schema is not None
            else None
        )
        super().__init__(
            resource_fn=resource_fn,
            config_schema=config_schema,
            description=description,
            required_resource_keys=required_resource_keys,
            version=version,
        )

    @property
    def input_config_schema(self) -> IDefinitionConfigSchema:
        return self._input_config_schema

    @property
    def output_config_schema(self) -> Optional[IDefinitionConfigSchema]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return self._output_config_schema

    def copy_for_configured(
        self,
        description: Optional[str],
        config_schema: CoercableToConfigSchema,
    ) -> "IOManagerDefinition":
        io_def = IOManagerDefinition(
            config_schema=config_schema,
            description=description or self.description,
            resource_fn=self.resource_fn,
            required_resource_keys=self.required_resource_keys,
            input_config_schema=self.input_config_schema,
            output_config_schema=self.output_config_schema,
        )

        io_def._dagster_maintained = self._is_dagster_maintained()

        return io_def

    @public
    @staticmethod
    def hardcoded_io_manager(
        value: "IOManager", description: Optional[str] = None
    ) -> "IOManagerDefinition":
        """A helper function that creates an ``IOManagerDefinition`` with a hardcoded IOManager.

        Args:
            value (IOManager): A hardcoded IO Manager which helps mock the definition.
            description ([Optional[str]]): The description of the IO Manager. Defaults to None.

        Returns:
            [IOManagerDefinition]: A hardcoded resource.
        """
        check.inst_param(value, "value", IOManager)
        return IOManagerDefinition(resource_fn=lambda _init_context: value, description=description)


@public
class IOManager(InputManager, OutputManager):
    """Base class for user-provided IO managers.

    IOManagers are used to store op outputs and load them as inputs to downstream ops.

    Extend this class to handle how objects are loaded and stored. Users should implement
    ``handle_output`` to store an object and ``load_input`` to retrieve an object.
    """

    @public
    @abstractmethod
    def load_input(self, context: "InputContext") -> Any:
        """User-defined method that loads an input to an op.

        Args:
            context (InputContext): The input context, which describes the input that's being loaded
                and the upstream output that's being loaded from.

        Returns:
            Any: The data object.
        """

    @public
    @abstractmethod
    def handle_output(self, context: "OutputContext", obj: Any) -> None:
        """User-defined method that stores an output of an op.

        Args:
            context (OutputContext): The context of the step output that produces this object.
            obj (Any): The object, returned by the op, to be stored.
        """


@overload
def io_manager(config_schema: IOManagerFunction) -> IOManagerDefinition: ...


@overload
def io_manager(
    config_schema: CoercableToConfigSchema = None,
    description: Optional[str] = None,
    output_config_schema: CoercableToConfigSchema = None,
    input_config_schema: CoercableToConfigSchema = None,
    required_resource_keys: Optional[set[str]] = None,
    version: Optional[str] = None,
) -> Callable[[IOManagerFunction], IOManagerDefinition]: ...


@public
def io_manager(
    config_schema: Union[IOManagerFunction, CoercableToConfigSchema] = None,
    description: Optional[str] = None,
    output_config_schema: CoercableToConfigSchema = None,
    input_config_schema: CoercableToConfigSchema = None,
    required_resource_keys: Optional[set[str]] = None,
    version: Optional[str] = None,
) -> Union[
    IOManagerDefinition,
    Callable[[IOManagerFunction], IOManagerDefinition],
]:
    """Define an IO manager.

    IOManagers are used to store op outputs and load them as inputs to downstream ops.

    The decorated function should accept an :py:class:`InitResourceContext` and return an
    :py:class:`IOManager`.

    Args:
        config_schema (Optional[ConfigSchema]): The schema for the resource config. Configuration
            data available in `init_context.resource_config`. If not set, Dagster will accept any
            config provided.
        description(Optional[str]): A human-readable description of the resource.
        output_config_schema (Optional[ConfigSchema]): The schema for per-output config. If not set,
            no per-output configuration will be allowed.
        input_config_schema (Optional[ConfigSchema]): The schema for per-input config. If not set,
            Dagster will accept any config provided.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the object
            manager.
        version (Optional[str]): The version of a resource function. Two wrapped
            resource functions should only have the same version if they produce the same resource
            definition when provided with the same inputs.

    **Examples:**

    .. code-block:: python

        class MyIOManager(IOManager):
            def handle_output(self, context, obj):
                write_csv("some/path")

            def load_input(self, context):
                return read_csv("some/path")

        @io_manager
        def my_io_manager(init_context):
            return MyIOManager()

        @op(out=Out(io_manager_key="my_io_manager_key"))
        def my_op(_):
            return do_stuff()

        @job(resource_defs={"my_io_manager_key": my_io_manager})
        def my_job():
            my_op()

    """
    if callable(config_schema) and not is_callable_valid_config_arg(config_schema):
        config_schema = cast("IOManagerFunction", config_schema)
        return _IOManagerDecoratorCallable()(config_schema)

    def _wrap(resource_fn: IOManagerFunction) -> IOManagerDefinition:
        return _IOManagerDecoratorCallable(
            config_schema=cast("Optional[UserConfigSchema]", config_schema),
            description=description,
            required_resource_keys=required_resource_keys,
            version=version,
            output_config_schema=output_config_schema,
            input_config_schema=input_config_schema,
        )(resource_fn)

    return _wrap


def dagster_maintained_io_manager(io_manager_def: IOManagerDefinition) -> IOManagerDefinition:
    io_manager_def._dagster_maintained = True  # noqa: SLF001
    return io_manager_def


class _IOManagerDecoratorCallable:
    def __init__(
        self,
        config_schema: CoercableToConfigSchema = None,
        description: Optional[str] = None,
        output_config_schema: CoercableToConfigSchema = None,
        input_config_schema: CoercableToConfigSchema = None,
        required_resource_keys: Optional[set[str]] = None,
        version: Optional[str] = None,
    ):
        # type validation happens in IOManagerDefinition
        self.config_schema = config_schema
        self.description = description
        self.required_resource_keys = required_resource_keys
        self.version = version
        self.output_config_schema = output_config_schema
        self.input_config_schema = input_config_schema

    def __call__(self, fn: IOManagerFunction) -> IOManagerDefinition:
        check.callable_param(fn, "fn")

        io_manager_def = IOManagerDefinition(
            resource_fn=fn,
            config_schema=self.config_schema,
            description=self.description,
            required_resource_keys=self.required_resource_keys,
            version=self.version,
            output_config_schema=self.output_config_schema,
            input_config_schema=self.input_config_schema,
        )

        # `update_wrapper` typing cannot currently handle a Union of Callables correctly
        update_wrapper(io_manager_def, wrapped=fn)  # type: ignore

        return io_manager_def
