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
    AssetsDefinition,
    Nothing,
    PartitionsDefinition,
    multi_asset,
)

from .asset_utils import (
    DAGSTER_DBT_TRANSLATOR_METADATA_KEY,
    MANIFEST_METADATA_KEY,
    default_auto_materialize_policy_fn,
    default_code_version_fn,
    default_freshness_policy_fn,
    get_deps,
)
from .dagster_dbt_translator import DagsterDbtTranslator
from .utils import (
    ASSET_RESOURCE_TYPES,
    get_node_info_by_dbt_unique_id_from_manifest,
    output_name_fn,
    select_unique_ids_from_manifest,
)


def dbt_assets(
    *,
    manifest: Union[Mapping[str, Any], Path],
    select: str = "fqn:*",
    exclude: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    dagster_dbt_translator: DagsterDbtTranslator = DagsterDbtTranslator(),
) -> Callable[..., AssetsDefinition]:
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
            from dagster_dbt import DbtCliResource, dbt_assets

            @dbt_assets(manifest=Path("target", "manifest.json"))
            def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
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
        manifest=manifest,
        dagster_dbt_translator=dagster_dbt_translator,
    )

    def inner(fn) -> AssetsDefinition:
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

        return asset_definition

    return inner


def get_dbt_multi_asset_args(
    dbt_nodes: Mapping[str, Any],
    deps: Mapping[str, FrozenSet[str]],
    io_manager_key: Optional[str],
    manifest: Mapping[str, Any],
    dagster_dbt_translator: DagsterDbtTranslator,
) -> Tuple[Sequence[AssetKey], Dict[str, AssetOut], Dict[str, Set[AssetKey]]]:
    non_argument_deps: Set[AssetKey] = set()
    outs: Dict[str, AssetOut] = {}
    internal_asset_deps: Dict[str, Set[AssetKey]] = {}

    for unique_id, parent_unique_ids in deps.items():
        node_info = dbt_nodes[unique_id]

        output_name = output_name_fn(node_info)
        asset_key = dagster_dbt_translator.get_asset_key(node_info)

        outs[output_name] = AssetOut(
            key=asset_key,
            dagster_type=Nothing,
            io_manager_key=io_manager_key,
            description=dagster_dbt_translator.get_description(node_info),
            is_required=False,
            metadata={  # type: ignore
                **dagster_dbt_translator.get_metadata(node_info),
                MANIFEST_METADATA_KEY: manifest,
                DAGSTER_DBT_TRANSLATOR_METADATA_KEY: dagster_dbt_translator,
            },
            group_name=dagster_dbt_translator.get_group_name(node_info),
            code_version=default_code_version_fn(node_info),
            freshness_policy=default_freshness_policy_fn(node_info),
            auto_materialize_policy=default_auto_materialize_policy_fn(node_info),
        )

        # Translate parent unique ids to internal asset deps and non argument dep
        output_internal_deps = internal_asset_deps.setdefault(output_name, set())
        for parent_unique_id in parent_unique_ids:
            parent_node_info = dbt_nodes[parent_unique_id]
            parent_asset_key = dagster_dbt_translator.get_asset_key(parent_node_info)

            # Add this parent as an internal dependency
            output_internal_deps.add(parent_asset_key)

            # Mark this parent as an input if it has no dependencies
            if parent_unique_id not in deps:
                non_argument_deps.add(parent_asset_key)

    return list(non_argument_deps), outs, internal_asset_deps
