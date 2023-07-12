from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Union

import dagster._check as check
from dagster import AssetsDefinition, PartitionsDefinition, multi_asset
from dagster._annotations import experimental

from .asset_utils import get_dbt_multi_asset_args, get_deps
from .core.resources_v2 import DbtManifest
from .utils import ASSET_RESOURCE_TYPES, select_unique_ids_from_manifest


@experimental
def dbt_assets(
    *,
    manifest: Union[Mapping[str, Any], DbtManifest, Path],
    select: str = "fqn:*",
    exclude: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
) -> Callable[..., AssetsDefinition]:
    """Create a definition for how to compute a set of dbt resources, described by a manifest.json.

    Args:
        manifest (Union[Mapping[str, Any], DbtManifest, Path]): The contents of a manifest.json file
            or the path to a manifest.json file. A manifest.json contains a representation of a
            dbt project (models, tests, macros, etc). We use this representation to create
            corresponding Dagster assets.
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

            from pathlib import Path

            from dagster import OpExecutionContext
            from dagster_dbt import DbtCli, dbt_assets

            @dbt_assets(manifest=Path("target", "manifest.json"))
            def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
                yield from dbt.cli(["build"], context=context).stream()
    """
    check.inst_param(manifest, "manifest", (Path, dict, DbtManifest))
    if isinstance(manifest, Path):
        manifest = DbtManifest.read(path=manifest)
    elif isinstance(manifest, Mapping):
        manifest = DbtManifest(manifest)

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
        manifest=manifest,
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
            descriptions_by_key=manifest.descriptions_by_asset_key,
            metadata_by_key=manifest.metadata_by_asset_key,
        )

    return inner
