from itertools import chain
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, Set, Union

from dagster import (
    AssetKey,
    AssetOut,
    AssetsDefinition,
    AutoMaterializePolicy,
    DagsterInvalidDefinitionError,
    FreshnessPolicy,
    MetadataValue,
    SourceAsset,
    TableSchema,
    _check as check,
    multi_asset,
)
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster._utils.warnings import suppress_dagster_warnings


@suppress_dagster_warnings
def airbyte_assets(
    *,
    connection_id: str,
    destination_tables: Sequence[str],
    asset_key_prefix: Optional[Sequence[str]] = None,
    group_name: Optional[str] = None,
    normalization_tables: Optional[Mapping[str, Set[str]]] = None,
    deps: Optional[Iterable[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]] = None,
    upstream_assets: Optional[Set[AssetKey]] = None,
    schema_by_table_name: Optional[Mapping[str, TableSchema]] = None,
    freshness_policy: Optional[FreshnessPolicy] = None,
    stream_to_asset_map: Optional[Mapping[str, str]] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    if upstream_assets is not None and deps is not None:
        raise DagsterInvalidDefinitionError(
            "Cannot specify both deps and upstream_assets to build_airbyte_assets. Use only deps"
            " instead."
        )

    asset_key_prefix = check.opt_sequence_param(asset_key_prefix, "asset_key_prefix", of_type=str)

    # Generate a list of outputs, the set of destination tables plus any affiliated
    # normalization tables
    tables = chain.from_iterable(
        chain([destination_tables], normalization_tables.values() if normalization_tables else [])
    )

    metadata = {
        "connection_id": connection_id,
        "destination_tables": destination_tables,
        "normalization_tables": normalization_tables,
    }

    outputs = {
        table: AssetOut(
            key=AssetKey([*asset_key_prefix, table]),
            metadata=(
                {
                    **metadata,
                    "table_schema": MetadataValue.table_schema(schema_by_table_name[table]),
                }
                if schema_by_table_name
                else metadata
            ),
            freshness_policy=freshness_policy,
            auto_materialize_policy=auto_materialize_policy,
        )
        for table in tables
    }

    internal_deps = {}

    # If normalization tables are specified, we need to add a dependency from the destination table
    # to the affilitated normalization table
    if normalization_tables:
        for base_table, derived_tables in normalization_tables.items():
            for derived_table in derived_tables:
                internal_deps[derived_table] = {AssetKey([*asset_key_prefix, base_table])}

    upstream_deps = deps
    if upstream_assets is not None:
        upstream_deps = list(upstream_assets)

    # All non-normalization tables depend on any user-provided upstream assets
    for table in destination_tables:
        internal_deps[table] = set(upstream_deps) if upstream_deps else set()

    return multi_asset(
        name=f"airbyte_sync_{connection_id[:5]}",
        deps=upstream_deps,
        outs=outputs,
        internal_asset_deps=internal_deps,
        compute_kind="airbyte",
        group_name=group_name,
    )
