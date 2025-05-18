from typing import Callable

from dagster_pipes.transforms.transform import (
    StorageIO,
    TransformResult,
    get_transform_metadata,
    get_upstream_metadata,
    mount_transform_graph,
)

from dagster import Output, multi_asset
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions


def build_transform_defs(
    transform_fns: list[Callable[..., TransformResult]], storage_io: StorageIO
) -> Definitions:
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

    # Sort transforms in topological order
    from toposort import toposort_flatten

    # Build dependency graph
    deps = {}
    for spec in specs:
        deps[spec.key] = set(spec.deps)

    # Get sorted asset keys
    sorted_keys = toposort_flatten(deps)

    # Sort transform functions to match asset order
    sorted_transforms = []
    for key in sorted_keys:
        for transform_fn in transform_fns:
            metadata = get_transform_metadata(transform_fn)
            if key in metadata.assets:
                sorted_transforms.append(transform_fn)
                break

    transform_fns = sorted_transforms

    # Create multi_asset from specs
    @multi_asset(specs=specs)
    def transform_assets(context):
        # Mount transform graph
        with mount_transform_graph(transform_fns, storage_io) as graph:
            # Execute each transform
            for transform_fn in transform_fns:
                result = graph.execute_transform(transform_fn)
                # Yield each asset
                for asset_key, data in result.assets.items():
                    yield Output(data, asset_key)

    return Definitions(assets=[transform_assets])
