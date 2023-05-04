from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, Mapping, Optional

from dagster import AssetsDefinition, OpExecutionContext, multi_asset
from dagster._core.definitions.events import AssetKey

from .asset_utils import default_asset_key_fn, get_dbt_multi_asset_args, get_deps
from .utils import ASSET_RESOURCE_TYPES, output_name_fn, select_unique_ids_from_manifest


@dataclass
class DbtManifest:
    """Helper class for dbt manifest operations."""

    manifest: dict

    @cached_property
    def dbt_unique_id_to_nodes(self) -> Mapping[str, dict]:
        """A mapping of a dbt node's unique id to the node's dictionary representation in the manifest.
        """
        return {
            **self.manifest["nodes"],
            **self.manifest["sources"],
            **self.manifest["exposures"],
            **self.manifest["metrics"],
        }

    @cached_property
    def asset_key_to_nodes(self) -> Mapping[AssetKey, dict]:
        """A mapping of the default asset key for a dbt node to the node's dictionary representation in the manifest.
        """
        return {default_asset_key_fn(node): node for node in self.dbt_unique_id_to_nodes.values()}

    @cached_property
    def output_name_to_nodes(self) -> Mapping[str, dict]:
        """A mapping of the default output name for a dbt node to the node's dictionary representation in the manifest.
        """
        return {output_name_fn(node): node for node in self.dbt_unique_id_to_nodes.values()}

    def get_node_by_output_name(self, output_name: str) -> dict:
        """Get a dbt node's dictionary representation in the manifest by its Dagster output name."""
        return self.output_name_to_nodes[output_name]

    def get_node_by_asset_key(self, asset_key: AssetKey) -> dict:
        """Get a dbt node's dictionary representation in the manifest by its Dagster output name."""
        return self.asset_key_to_nodes[asset_key]


def construct_subset_kwargs_from_manifest(
    context: OpExecutionContext,
    manifest: dict,
    select: str = "*",
    exclude: Optional[str] = None,
):
    kwargs: Dict[str, Any] = {}

    # in the case that we're running everything, opt for the cleaner selection string
    if len(context.selected_output_names) == len(context.assets_def.node_keys_by_output_name):
        kwargs["select"] = select
        kwargs["exclude"] = exclude
    else:
        # for each output that we want to emit, translate to a dbt select string by converting
        # the out to its corresponding fqn
        selected_dbt_models = []
        for output_name in context.selected_output_names:
            node_info = DbtManifest(manifest).get_node_by_output_name(output_name)
            fqn = ".".join(node_info["fqn"])
            selected_dbt_model = f"fqn:{fqn}"

            selected_dbt_models.append(selected_dbt_model)

        kwargs["select"] = selected_dbt_models

    return kwargs


def dbt_multi_asset(
    *,
    manifest: dict,
    select: str = "*",
    exclude: Optional[str] = None,
) -> Callable[..., AssetsDefinition]:
    unique_ids = select_unique_ids_from_manifest(
        select=select, exclude=exclude or "", manifest_json=manifest
    )
    dbt_nodes = DbtManifest(manifest).dbt_unique_id_to_nodes

    deps = get_deps(
        dbt_nodes,
        selected_unique_ids=unique_ids,
        asset_resource_types=ASSET_RESOURCE_TYPES,
    )
    (
        non_argument_deps,
        outs,
        internal_asset_deps,
    ) = get_dbt_multi_asset_args(
        dbt_nodes=dbt_nodes,
        deps=deps,
    )

    def inner(fn) -> AssetsDefinition:
        asset_definition = multi_asset(
            outs=outs,
            internal_asset_deps=internal_asset_deps,
            non_argument_deps=non_argument_deps,
            compute_kind="dbt",
            can_subset=True,
        )(fn)

        return asset_definition

    return inner
