from collections.abc import Iterator
from dataclasses import dataclass
from typing import Callable, Optional

from dagster_pipes.transforms.transform import (
    BoundTransformGraph,
    InMemoryStorageIO,
    StorageIOPlugin,
    TransformResult,
    get_transform_metadata,
    get_upstream_metadata,
    mount_transform_graph,
)

from dagster import MaterializeResult, multi_asset
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.context import PipesExecutionResult


def build_inprocess_transform_defs(
    transform_fns: list[Callable[..., TransformResult]],
    storage_io: Optional[StorageIOPlugin] = None,
) -> Definitions:
    storage_io = storage_io or InMemoryStorageIO()

    specs = build_specs_from_transform_fns(transform_fns)
    # Create dictionary mapping asset keys to transform functions
    transform_fn_by_asset = {}
    for transform_fn in transform_fns:
        metadata = get_transform_metadata(transform_fn)
        for asset_key in metadata.assets:
            transform_fn_by_asset[asset_key] = transform_fn

    # must pass in toposort order for now

    # Sort transforms in topological order
    # from toposort import toposort_flatten

    # # Build dependency graph
    # deps = {}
    # for spec in specs:
    #     deps[spec.key] = set(spec.deps)

    # # Get sorted asset keys
    # sorted_keys = toposort_flatten(deps)

    # # Sort transform functions to match asset order
    # sorted_transforms = []
    # for key in sorted_keys:
    #     for transform_fn in transform_fns:
    #         metadata = get_transform_metadata(transform_fn)
    #         if key in metadata.assets:
    #             sorted_transforms.append(transform_fn)
    #             break

    # transform_fns = sorted_transforms

    # sys.stdout.flush()
    # raise Exception(f"specs: {specs}")
    # import code

    # code.interact(local=dict(globals(), **locals()))

    # Create multi_asset from specs
    # @multi_asset(specs=specs)
    # def transform_assets(context):
    #     # Mount transform graph
    #     with mount_transform_graph(transform_fns, storage_io) as graph:
    #         # Execute each transform
    #         for transform_fn in transform_fns:
    #             result = graph.execute_transform(transform_fn)
    #             # Yield each asset
    #             for asset_key, data in result.assets.items():
    #                 yield MaterializeResult(asset_key=AssetKey.from_user_string(asset_key))

    def invoke_fn(
        context: AssetExecutionContext, op_name: str, spec: AssetSpec
    ) -> Iterator[PipesExecutionResult]:
        with mount_transform_graph(transform_fns, storage_io) as graph:
            result = graph.execute_asset_key(spec.key.to_user_string())
            assert result
            yield MaterializeResult(asset_key=spec.key)

    return build_transform_defs(
        transform_specs=[
            TransformSpec(
                op_name="the_transform",
                assets=specs,
            )
            for transform_fn in transform_fns
        ],
        invoke_fn=invoke_fn,
    )


def build_specs_from_transform_fns(transform_fns):
    specs = []

    for transform_fn in transform_fns:
        metadata = get_transform_metadata(transform_fn)
        deps = []

        # Get dependencies from function annotations
        for param_name in transform_fn.__annotations__.keys():
            if param_name != "return" and param_name != "context":
                upstream = get_upstream_metadata(transform_fn, param_name)
                deps.append(AssetKey.from_user_string(upstream.asset))

        # Create asset spec for each output asset
        for asset_key in metadata.assets:
            spec = AssetSpec(
                key=AssetKey.from_user_string(asset_key),
                deps=deps,
                description=f"Generated from transform {transform_fn.__name__}",
            )
            specs.append(spec)
    return specs


InvocationFn = Callable[[AssetExecutionContext, str, AssetSpec], Iterator[PipesExecutionResult]]


def build_assets_def(
    *,
    spec: AssetSpec,
    invoke_fn: InvocationFn,
    op_name: str,
) -> AssetsDefinition:
    @multi_asset(name=op_name, specs=[spec])
    def transform_assets(context) -> Iterator[PipesExecutionResult]:
        yield from invoke_fn(context, op_name, spec)

    return transform_assets


@dataclass
class TransformSpec:
    op_name: str
    assets: list[AssetSpec]


def build_transform_defs(
    transform_specs: list[TransformSpec], invoke_fn: InvocationFn
) -> Definitions:
    assets = []
    for transform_spec in transform_specs:
        assert len(transform_spec.assets) == 1
        assets.append(
            build_assets_def(
                spec=transform_spec.assets[0],
                invoke_fn=invoke_fn,
                op_name=transform_spec.op_name,
            )
        )

    return Definitions(assets=assets)


class InProcessInvocation:
    def __init__(self, graph: BoundTransformGraph, transform_fn: Callable[..., TransformResult]):
        self.graph = graph
        self.transform_fn = transform_fn

    def execute(self):
        self.graph.execute_transform(self.transform_fn)


def build_invocation(graph: BoundTransformGraph, transform_fn: Callable[..., TransformResult]):
    return InProcessInvocation(graph, transform_fn)
