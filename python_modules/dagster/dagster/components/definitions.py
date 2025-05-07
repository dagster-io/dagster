import inspect
from typing import Callable, Generic, Literal, Optional, TypeVar, Union, overload

from dagster._annotations import preview, public
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
    """An object that can be invoked to load a set of definitions. Useful in tests when you want to regenerate the same definitions in multiple contexts."""

    load_fn: Callable[..., T_Defs]
    has_context_arg: bool

    def __call__(self, context: Optional[ComponentLoadContext] = None) -> T_Defs:
        """Load a set of definitions using the load_fn provided at construction time.

        Args:
            context (Optional[ComponentLoadContext]): Optional context for loading definitions.

        Returns:
            Union[Definitions, RepositoryDefinition]: The loaded definitions.
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
                "DefinitionsLoader must return a Definitions or RepositoryDefinition object"
            )
        return result


@overload
def definitions(fn: Callable[[], T_Defs]) -> LazyDefinitions[T_Defs]: ...


@overload
def definitions(
    *, has_context_arg: Literal[True]
) -> Callable[[Callable[[ComponentLoadContext], T_Defs]], LazyDefinitions[T_Defs]]: ...


@public
@preview(emit_runtime_warning=False)
def definitions(
    fn: Optional[Callable[..., T_Defs]] = None, *, has_context_arg: bool = False
) -> Union[LazyDefinitions[T_Defs], Callable[[Callable[..., T_Defs]], LazyDefinitions[T_Defs]]]:
    """Marks a function as an entry point for loading a set of Dagster definitions. Useful as a test
    utility to define definitions that you wish to load multiple times with different contexts.

    Args:
        has_context_arg (bool): Whether the decorated function accepts a ComponentLoadContext parameter.
            Defaults to False. If True, the function must accept a ComponentLoadContext parameter.
            If False, the function must not accept any parameters.

    Returns:
        LazyDefinitions: A callable that will load a set of definitions when invoked.

    Examples:
        .. code-block:: python

            from dagster import (
                AssetSpec,
                Definitions,
                DefinitionsLoadContext,
                DefinitionsLoadType,
                asset,
                definitions,
                external_assets_from_specs,
            )

            WORKSPACE_ID = "my_workspace"
            FOO_METADATA_KEY_PREFIX = "foo"


            # Simple model of an external service foo
            def fetch_foo_defs_metadata(workspace_id: str):
                if workspace_id == WORKSPACE_ID:
                    return [{"id": "alpha"}, {"id": "beta"}]
                else:
                    raise Exception("Unknown workspace")


            def get_foo_defs(context: DefinitionsLoadContext, workspace_id: str) -> Definitions:
                metadata_key = f"{FOO_METADATA_KEY_PREFIX}/{workspace_id}"
                if (
                    context.load_type == DefinitionsLoadType.RECONSTRUCTION
                    and metadata_key in context.reconstruction_metadata
                ):
                    payload = context.reconstruction_metadata[metadata_key]
                else:
                    payload = fetch_foo_defs_metadata(workspace_id)
                asset_specs = [AssetSpec(item["id"]) for item in payload]
                assets = external_assets_from_specs(asset_specs)
                return Definitions(
                    assets=assets,
                ).with_reconstruction_metadata({metadata_key: payload})


            # Example with context parameter
            @definitions(has_context_arg=True)
            def defs_with_context(context: ComponentLoadContext):
                @asset
                def regular_asset(): ...

                return Definitions.merge(
                    get_foo_defs(context, WORKSPACE_ID),
                    Definitions(assets=[regular_asset]),
                )

            # Example without context parameter (default behavior)
            @definitions
            def defs_without_context():
                @asset
                def regular_asset(): ...

                context = DefinitionsLoadContext.get()

                return Definitions.merge(
                    get_foo_defs(context, WORKSPACE_ID),
                    Definitions(assets=[regular_asset]),
                )

    """

    def decorator(fn: Callable[..., T_Defs]) -> LazyDefinitions[T_Defs]:
        if has_context_arg:
            # Type check that the function accepts a ComponentLoadContext parameter
            sig = inspect.signature(fn)
            if len(sig.parameters) != 1:
                raise DagsterInvariantViolationError(
                    "Function must accept exactly one ComponentLoadContext parameter when has_context_arg=True"
                )
            first_param = next(iter(sig.parameters.values()))
            if first_param.annotation != ComponentLoadContext:
                raise DagsterInvariantViolationError(
                    "Function must accept a ComponentLoadContext parameter when has_context_arg=True"
                )
        else:
            # Type check that the function accepts no parameters
            sig = inspect.signature(fn)
            if len(sig.parameters) != 0:
                raise DagsterInvariantViolationError(
                    "Function must accept no parameters when has_context_arg=False"
                )
        return LazyDefinitions(load_fn=fn, has_context_arg=has_context_arg)

    if fn is not None:
        return decorator(fn)
    return decorator
