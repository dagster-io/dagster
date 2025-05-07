from typing import Callable, Generic, Optional, TypeVar

from dagster._annotations import preview, public
from dagster._core.definitions.asset_selection import AssetSelection, CoercibleToAssetSelection
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._record import record

T_Defs = TypeVar("T_Defs", Definitions, RepositoryDefinition)


@record
class LazyDefinitions(Generic[T_Defs]):
    """An object that can be invoked to load a set of definitions. Useful in tests when you want to regenerate the same definitions in multiple contexts."""

    load_fn: Callable[[], T_Defs]

    def __call__(self) -> T_Defs:
        """Load a set of definitions using the load_fn provided at construction time.

        Returns:
            Union[Definitions, RepositoryDefinition]: The loaded definitions.
        """
        result = self.load_fn()
        if not isinstance(result, (Definitions, RepositoryDefinition)):
            raise DagsterInvariantViolationError(
                "DefinitionsLoader must return a Definitions or RepositoryDefinition object"
            )
        return result


@public
@preview(emit_runtime_warning=False)
def definitions(fn: Callable[[], T_Defs]) -> LazyDefinitions[T_Defs]:
    """Marks a function as an entry point for loading a set of Dagster definitions. Useful as a test
    utility to define definitions that you wish to load multiple times with different contexts.

    As with plain `Definitions` objects, there can be only one `@definitions`-decorated function per
    module if that module is being loaded as a Dagster code location.

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


            @definitions
            def defs():
                @asset
                def regular_asset(): ...

                context = DefinitionsLoadContext.get()

                return Definitions.merge(
                    get_foo_defs(context, WORKSPACE_ID),
                    Definitions(assets=[regular_asset]),
                )

    """
    return LazyDefinitions(load_fn=fn)


class DefinitionsHandle:
    def __init__(self, defs: Definitions):
        self._defs = defs

    def map_asset_specs(
        self,
        *,
        func: Callable[[AssetSpec], AssetSpec],
        selection: Optional[CoercibleToAssetSelection] = None,
    ) -> "DefinitionsHandle":
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
    ) -> "DefinitionsHandle":
        from dagster.components.core.context import ComponentLoadContext, ComponentsLoadType

        if selection:
            context = ComponentLoadContext.current()
            selection_str = selection.to_selection_str()

            if context.load_type == ComponentsLoadType.INITIAL_LOAD:
                target_keys = selection.resolve(self._defs.get_asset_graph())

                serialized_selections = context.get_partial_data_for_current_component() or {}
                serialized_selections[selection_str] = list(target_keys)
                context.record_component_data(serialized_selections)
            else:
                target_keys = context.get_data_for_current_component()[selection_str]
                keys_string = "\n- ".join([str(key) for key in target_keys])
                print(f"RESOLVED CACHED ASSET SELECTION {selection_str} to\n- {keys_string}\n")
            new_func = (
                lambda spec: func(spec)
                if (target_keys is None or spec.key in target_keys)
                else spec
            )
        else:
            new_func = func
        return DefinitionsHandle(self._defs.map_asset_specs(func=new_func))
