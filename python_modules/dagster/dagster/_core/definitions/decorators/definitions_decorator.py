from typing import Callable, overload

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_loader import (
    DefinitionsLoadContext,
    DefinitionsLoader,
    DefinitionsLoadFn,
)

# We type this with Callable instead of DefinitionsLoader because we are treating DefinitionsLoader
# as an internal implementation detail.


@overload
def definitions(
    fn: Callable[[DefinitionsLoadContext], Definitions],
) -> Callable[[DefinitionsLoadContext], Definitions]: ...


@overload
def definitions(fn: Callable[[], Definitions]) -> Callable[[], Definitions]: ...


def definitions(fn: DefinitionsLoadFn) -> DefinitionsLoadFn:
    """Marks a function as an entry point for loading a set of Dagster definitions.

    A `@definitions`-decorated function can perform arbitrary computation to produce a set of
    Definitions. It is executed during startup of a Dagster process, and optionally receives
    a DefinitionsLoadContext object as argument.

    The DefinitionsLoadContext is useful when reconstructing the Definitions in worker processes
    spawned from a parent code server process. The standard pattern is to perform expensive
    computations (such as making an external API request) a single time at code server
    initialization and to cache the result by calling `with_reconstruction_metadata` on the returned
    Definitions object. This metadata is then made available on
    `DefinitionsLoadContext.reconstruction_metadata` in child processes.

    As with plain `Definitions` objects, there can be only one `@definitions`-decorated function per
    module if that module is being loaded as a Dagster code location.

    Returns:
        Union[Callable[[DefinitionsLoadContext], Definitions], Callable[[], Definitions]]: A
            callable with the same signature as the decorated function.

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
            def defs(context: DefinitionsLoadContext):
                @asset
                def regular_asset(): ...

                return Definitions.merge(
                    get_foo_defs(context, WORKSPACE_ID),
                    Definitions(assets=[regular_asset]),
                )

    """
    return DefinitionsLoader(load_fn=fn)
