import inspect
from typing import Callable, Generic, Optional, TypeVar, Union, cast

from dagster._annotations import public
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._record import record
from dagster.components.core.context import ComponentLoadContext

T_Defs = TypeVar("T_Defs", Definitions, RepositoryDefinition)


@record
class LazyDefinitions(Generic[T_Defs]):
    """An object that can be invoked to load a set of definitions."""

    load_fn: Callable[..., T_Defs]
    has_context_arg: bool

    def __call__(self, context: Optional[ComponentLoadContext] = None) -> T_Defs:
        """Load a set of definitions using the load_fn provided at construction time.

        Args:
            context (Optional[ComponentLoadContext]): Optional context for loading definitions.

        Returns:
            T_Defs: The loaded definitions.
        """
        if self.has_context_arg:
            if context is None:
                raise DagsterInvariantViolationError(
                    "Function requires a ComponentLoadContext but none was provided"
                )
            result = self.load_fn(context)
        else:
            result = self.load_fn()

        if not isinstance(result, (Definitions, RepositoryDefinition)):
            raise DagsterInvariantViolationError(
                "Function must return a Definitions or RepositoryDefinition object"
            )
        return result


@public
def definitions(
    fn: Union[Callable[[], Definitions], Callable[[ComponentLoadContext], Definitions]],
) -> Callable[..., Definitions]:
    """Decorator that marks a function as an entry point for loading Dagster definitions.

    This decorator provides a lazy loading mechanism for Definitions objects, which is the
    preferred approach over directly instantiating Definitions at module import time. It
    enables Dagster's tools to discover and load definitions on-demand without executing
    the definition creation logic during module imports. The user can also import this
    function and import it for test cases.

    The decorated function must return a Definitions object and can optionally accept a
    ComponentLoadContext parameter, populated when loaded in the context of
    autoloaded defs folders in the dg project layout.

    Args:
        fn: A function that returns a Definitions object. The function can either:
            - Accept no parameters: ``() -> Definitions``
            - Accept a ComponentLoadContext: ``(ComponentLoadContext) -> Definitions``

    Returns:
        A callable that will invoke the original function and return its
        Definitions object when called by Dagster's loading mechanisms or directly
        by the user.

    Raises:
        DagsterInvariantViolationError: If the function signature doesn't match the expected
            patterns (no parameters or exactly one ComponentLoadContext parameter).

    Examples:
        Basic usage without context:

        .. code-block:: python

            import dagster as dg

            @dg.definitions
            def my_definitions():
                @dg.asset
                def sales_data():
                    return [1, 2, 3]

                return dg.Definitions(assets=[sales_data])

        Usage with ComponentLoadContext for autoloaded definitions:

        .. code-block:: python

            import dagster as dg

            @dg.definitions
            def my_definitions(context: dg.ComponentLoadContext):
                @dg.asset
                def sales_data():
                    # Can use context for environment-specific logic
                    return load_data_from(context.path)

                return dg.Definitions(assets=[sales_data])

        The decorated function can be imported and used by Dagster tools:

        .. code-block:: python

            # my_definitions.py
            @dg.definitions
            def defs():
                return dg.Definitions(assets=[my_asset])

            # dg dev -f my_definitions.py

    Note:
        When used in autoloaded defs folders, the ComponentLoadContext provides access to
        environment variables and other contextual information for dynamic definition loading.

    See Also:
        - :py:class:`dagster.Definitions`: The object that should be returned by the decorated function
        - :py:class:`dagster.ComponentLoadContext`: Context object for autoloaded definitions
    """
    sig = inspect.signature(fn)
    has_context_arg = False

    if len(sig.parameters) > 0:
        first_param = next(iter(sig.parameters.values()))
        if first_param.annotation == ComponentLoadContext:
            has_context_arg = True
            if len(sig.parameters) > 1:
                raise DagsterInvariantViolationError(
                    "Function must accept either no parameters or exactly one ComponentLoadContext parameter"
                )
        else:
            raise DagsterInvariantViolationError(
                "Function must accept either no parameters or exactly one ComponentLoadContext parameter"
            )

    lazy_defs = LazyDefinitions[Definitions](load_fn=fn, has_context_arg=has_context_arg)
    return cast("Callable[..., Definitions]", lazy_defs)


# For backwards compatibility with existing test cases
def lazy_repository(fn: Callable[[], RepositoryDefinition]) -> Callable[[], RepositoryDefinition]:
    lazy_defs = LazyDefinitions[RepositoryDefinition](load_fn=fn, has_context_arg=False)
    return cast("Callable[[], RepositoryDefinition]", lazy_defs)
