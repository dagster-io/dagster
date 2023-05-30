from typing import Callable, Optional

from dagster import AssetsDefinition, PartitionsDefinition, multi_asset
from dagster._annotations import experimental

from .asset_utils import get_dbt_multi_asset_args, get_deps
from .cli.resources_v2 import DbtManifest
from .utils import ASSET_RESOURCE_TYPES, select_unique_ids_from_manifest


@experimental
def dbt_assets(
    *,
    manifest: DbtManifest,
    select: str = "fqn:*",
    exclude: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
) -> Callable[..., AssetsDefinition]:
    """Create a definition for how to compute a set of dbt resources, described by a manifest.json.

    Args:
        manifest (DbtManifest): The wrapper of a dbt manifest.json.
        select (Optional[str]): A dbt selection string for the models in a project that you want
            to include. Defaults to "*".
        exclude (Optional[str]): A dbt selection string for the models in a project that you want
            to exclude. Defaults to "".
        io_manager_key (Optional[str]): The IO manager key that will be set on each of the returned
            assets. When other ops are downstream of the loaded assets, the IOManager specified
            here determines how the inputs to those ops are loaded. Defaults to "io_manager".
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the dbt assets.

    Examples:
        .. code-block:: python

            @dbt_multi_asset(manifest=manifest)
            def my_dbt_assets(dbt: ResourceParam["DbtCliClient"]):
                yield from dbt.cli(["run"])
    """
    unique_ids = select_unique_ids_from_manifest(
        select=select, exclude=exclude or "", manifest_json=manifest.raw_manifest
    )
    deps = get_deps(
        dbt_nodes=manifest.node_info_by_dbt_unique_id,
        selected_unique_ids=unique_ids,
        asset_resource_types=ASSET_RESOURCE_TYPES,
    )
    (
        non_argument_deps,
        outs,
        internal_asset_deps,
    ) = get_dbt_multi_asset_args(
        dbt_nodes=manifest.node_info_by_dbt_unique_id,
        deps=deps,
        io_manager_key=io_manager_key,
    )

    def inner(fn) -> AssetsDefinition:
        asset_definition = multi_asset(
            outs=outs,
            internal_asset_deps=internal_asset_deps,
            non_argument_deps=non_argument_deps,
            compute_kind="dbt",
            partitions_def=partitions_def,
            can_subset=True,
            op_tags={
                **({"dagster-dbt/select": select} if select else {}),
                **({"dagster-dbt/exclude": exclude} if exclude else {}),
            },
        )(fn)

        return asset_definition.with_attributes(
            input_asset_key_replacements=manifest.asset_key_replacements,
            output_asset_key_replacements=manifest.asset_key_replacements,
        )

    return inner
