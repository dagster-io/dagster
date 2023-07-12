import json
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)

import dagster._check as check
from dagster import (
    AssetKey,
    AssetOut,
    Nothing,
    PartitionsDefinition,
    multi_asset,
)
from dagster._annotations import experimental

from .asset_utils import (
    MANIFEST_METADATA_KEY,
    default_asset_key_fn,
    default_auto_materialize_policy_fn,
    default_code_version_fn,
    default_description_fn,
    default_freshness_policy_fn,
    default_group_fn,
    default_metadata_fn,
    get_deps,
    output_name_fn,
)
from .dagster_dbt_translator import DagsterDbtTranslator
from .dbt_assets_definition import DbtAssetsDefinition
from .utils import (
    ASSET_RESOURCE_TYPES,
    get_node_info_by_dbt_unique_id_from_manifest,
    output_name_fn,
    select_unique_ids_from_manifest,
)


@experimental
def dbt_assets(
    *,
    manifest: Union[Mapping[str, Any], Path],
    select: str = "fqn:*",
    exclude: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    dagster_dbt_translator: DagsterDbtTranslator = DagsterDbtTranslator(),
) -> Callable[..., DbtAssetsDefinition]:
    """Create a definition for how to compute a set of dbt resources, described by a manifest.json.

    Args:
        manifest (Union[Mapping[str, Any], Path]): The contents of a manifest.json file
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
    check.inst_param(manifest, "manifest", (Path, dict))
    if isinstance(manifest, Path):
        with manifest.open("r") as handle:
            manifest = cast(Mapping[str, Any], json.load(handle))

    unique_ids = select_unique_ids_from_manifest(
        select=select, exclude=exclude or "", manifest_json=manifest
    )
    node_info_by_dbt_unique_id = get_node_info_by_dbt_unique_id_from_manifest(manifest)
    deps = get_deps(
        dbt_nodes=node_info_by_dbt_unique_id,
        selected_unique_ids=unique_ids,
        asset_resource_types=ASSET_RESOURCE_TYPES,
    )
    (
        non_argument_deps,
        outs,
        internal_asset_deps,
    ) = get_dbt_multi_asset_args(
        dbt_nodes=node_info_by_dbt_unique_id,
        deps=deps,
        io_manager_key=io_manager_key,
        dagster_dbt_translator=dagster_dbt_translator,
    )

    def inner(fn) -> DbtAssetsDefinition:
        asset_definition = multi_asset(
            outs=outs,
            internal_asset_deps=internal_asset_deps,
            deps=non_argument_deps,
            compute_kind="dbt",
            partitions_def=partitions_def,
            can_subset=True,
            op_tags={
                **({"dagster-dbt/select": select} if select else {}),
                **({"dagster-dbt/exclude": exclude} if exclude else {}),
            },
        )(fn)

        return DbtAssetsDefinition.from_assets_def(
            asset_definition,
            manifest=manifest,
            dagster_dbt_translator=dagster_dbt_translator,
        )

    return inner


def get_dbt_multi_asset_args(
    dbt_nodes: Mapping[str, Any],
    deps: Mapping[str, FrozenSet[str]],
    io_manager_key: Optional[str],
    manifest: "DbtManifest",
) -> Tuple[Sequence[AssetKey], Dict[str, AssetOut], Dict[str, Set[AssetKey]]]:
    """Use the standard defaults for dbt to construct the arguments for a dbt multi asset."""
    non_argument_deps: Set[AssetKey] = set()
    outs: Dict[str, AssetOut] = {}
    internal_asset_deps: Dict[str, Set[AssetKey]] = {}

    for unique_id, parent_unique_ids in deps.items():
        node_info = dbt_nodes[unique_id]

        output_name = output_name_fn(node_info)
        asset_key = default_asset_key_fn(node_info)

        outs[output_name] = AssetOut(
            key=asset_key,
            dagster_type=Nothing,
            io_manager_key=io_manager_key,
            description=default_description_fn(node_info, display_raw_sql=False),
            is_required=False,
            metadata={  # type: ignore
                **default_metadata_fn(node_info),
                MANIFEST_METADATA_KEY: manifest,
            },
            group_name=default_group_fn(node_info),
            code_version=default_code_version_fn(node_info),
            freshness_policy=default_freshness_policy_fn(node_info),
            auto_materialize_policy=default_auto_materialize_policy_fn(node_info),
        )

        # Translate parent unique ids to internal asset deps and non argument dep
        output_internal_deps = internal_asset_deps.setdefault(output_name, set())
        for parent_unique_id in parent_unique_ids:
            parent_node_info = dbt_nodes[parent_unique_id]
            parent_asset_key = default_asset_key_fn(parent_node_info)

            # Add this parent as an internal dependency
            output_internal_deps.add(parent_asset_key)

            # Mark this parent as an input if it has no dependencies
            if parent_unique_id not in deps:
                non_argument_deps.add(parent_asset_key)

    return list(non_argument_deps), outs, internal_asset_deps
