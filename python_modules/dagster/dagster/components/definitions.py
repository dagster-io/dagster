import abc
import inspect
from typing import Callable, Generic, Optional, TypeVar, Union, cast

from dagster_shared import check as check
from typing_extensions import TypeAlias

from dagster._annotations import preview, public
from dagster._core.definitions.asset_selection import AssetSelection, CoercibleToAssetSelection
from dagster._core.definitions.asset_spec import AssetSpec
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
@preview(emit_runtime_warning=False)
def definitions(
    fn: Union[Callable[[], Definitions], Callable[[ComponentLoadContext], Definitions]],
) -> Callable[..., Definitions]:
    """Marks a function as an entry point for loading a set of Dagster definitions. It is an alternative
    to directly instantiating a Definitions object and assigning it to a local variable. This enables
    a user to import a python module that contains a loadable definitions object without having
    to create it at import time.

    The function can optionally accept a ComponentLoadContext parameter. If it does, the context will be
    passed to the function when it is called. If it doesn't, the function will be called without any
    parameters.

    Returns:
        Callable[..., Definitions]: A callable that will load a set of definitions when invoked.
            The callable accepts an optional ComponentLoadContext parameter that defaults to None.

    Examples:
        .. code-block:: python

            import dagster as dg

            # Example with context parameter
            @dg.definitions
            def defs_with_context(context: ComponentLoadContext):
                @asset
                def regular_asset(): ...

                return Definitions(assets=[regular_asset])

            # Example without context parameter
            @dg.definitions
            def defs_without_context():
                @asset
                def regular_asset(): ...

                return Definitions(assets=[regular_asset])

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
    return cast("Callable[[],RepositoryDefinition]", lazy_defs)


T = TypeVar("T", bound="DefinitionsHandle")


class DefinitionsHandle(abc.ABC):
    """Interface which sits on top of a `Definitions` object and allows modification of the contained
    defs, with the restriction that transformations must be map-like. This ensures that the transformations
    are identical in the case that we may subset the input Definitions object.
    """

    @abc.abstractmethod
    def map_asset_specs(
        self: T,
        *,
        func: Callable[[AssetSpec], AssetSpec],
        selection: Optional[CoercibleToAssetSelection] = None,
    ) -> T:
        """Map a function over the included AssetSpecs or AssetsDefinitions in this Definitions object, replacing specs in the sequence
        or specs in an AssetsDefinitions with the result of the function.

        Args:
            func (Callable[[AssetSpec], AssetSpec]): The function to apply to each AssetSpec.
            selection (Optional[Union[str, Sequence[str], Sequence[AssetKey], Sequence[Union[AssetsDefinition, SourceAsset]], AssetSelection]]): An asset selection to narrow down the set of assets to apply the function to. If not provided, applies to all assets.

        Returns:
            DefinitionsHandle: A DefinitionsHandle object where the AssetSpecs have been replaced with the result of the function where the selection applies.

        Examples:
            .. code-block:: python

                defs_handle: DefinitionsHandle = ...

                # Applies to asset1 and asset2
                mapped_def_handle = defs_handle.map_asset_specs(
                    func=lambda s: s.merge_attributes(metadata={"new_key": "new_value"}),
                )

        """
        ...


PostProcessorFn: TypeAlias = Callable[[DefinitionsHandle], DefinitionsHandle]


class ComponentsDefinitionsHandle(DefinitionsHandle):
    """Interface which sits on top of a `Definitions` object and allows modification of the contained
    defs, with the restriction that transformations must be map-like. This ensures that the transformations
    are identical in the case that we may subset the input Definitions object.

    In the future, this class will cache asset selections on the load context so that subsequent loads
    (e.g. in runs, instigators) can reuse the same asset selection without resolving the entire asset graph.
    """

    def __init__(self, defs: Definitions, context: ComponentLoadContext):
        self._defs = defs
        self._context = context

    def map_asset_specs(
        self,
        *,
        func: Callable[[AssetSpec], AssetSpec],
        selection: Optional[CoercibleToAssetSelection] = None,
    ) -> "ComponentsDefinitionsHandle":
        if selection:
            if isinstance(selection, str):
                resolved_selection = AssetSelection.from_string(selection, include_sources=True)
            else:
                resolved_selection = AssetSelection.from_coercible(selection)
        else:
            resolved_selection = None
        return self._map_asset_specs_inner(func, resolved_selection)

    def _map_asset_specs_inner(
        self, func: Callable[[AssetSpec], AssetSpec], selection: Optional[AssetSelection]
    ) -> "ComponentsDefinitionsHandle":
        target_keys = selection.resolve(self._defs.resolve_asset_graph()) if selection else None
        new_func = (
            lambda spec: func(spec) if target_keys is None or spec.key in target_keys else spec
        )
        return ComponentsDefinitionsHandle(self._defs.map_asset_specs(func=new_func), self._context)

    @staticmethod
    def apply_post_processing_fn(
        defs: Definitions,
        context: ComponentLoadContext,
        post_processing_fn: PostProcessorFn,
    ) -> Definitions:
        return check.inst(  # noqa: SLF001
            post_processing_fn(ComponentsDefinitionsHandle(defs, context)),
            ComponentsDefinitionsHandle,
        )._defs
