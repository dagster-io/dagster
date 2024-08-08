from functools import partial
from itertools import chain
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Union,
    cast,
)

from dagster import (
    AssetDep,
    AssetKey,
    AssetOut,
    AssetsDefinition,
    AutoMaterializePolicy,
    DagsterInvalidDefinitionError,
    FreshnessPolicy,
    Nothing,
    SourceAsset,
    TableSchema,
    _check as check,
    multi_asset,
)
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster._core.definitions.metadata import MetadataValue, TableSchemaMetadataValue
from dagster._utils.warnings import suppress_dagster_warnings

from dagster_airbyte.airbyte_project import AirbyteProject
from dagster_airbyte.dagster_airbyte_translator import DagsterAirbyteTranslator
from dagster_airbyte.utils import get_schema_by_table_name, table_to_output_name_fn


# TODO: pass all connections, then add connection filter or selection
# TODO: add bool to materialize normalization table
# TODO: add DagsterAirbyteTranslator
@suppress_dagster_warnings
def airbyte_single_connection_asset(
    *,
    connection_id: str,
    destination_tables: Sequence[str],
    asset_key_prefix: Optional[Sequence[str]] = None,
    group_name: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    normalization_tables: Optional[Mapping[str, Set[str]]] = None,
    deps: Optional[Iterable[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]] = None,
    upstream_assets: Optional[Set[AssetKey]] = None,
    schema_by_table_name: Optional[Mapping[str, TableSchema]] = None,
    freshness_policy: Optional[FreshnessPolicy] = None,
    stream_to_asset_map: Optional[Mapping[str, str]] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
    dagster_airbyte_translator: Optional[DagsterAirbyteTranslator] = None,
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
        io_manager_key=io_manager_key,
    )


@suppress_dagster_warnings
def airbyte_assets(
    *,
    name: Optional[str] = None,
    project: AirbyteProject,
    dagster_airbyte_translator: Optional[DagsterAirbyteTranslator] = None,
    create_assets_for_normalization_tables: bool = True,
    required_resource_keys: Optional[Set[str]] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    if not dagster_airbyte_translator:
        dagster_airbyte_translator = DagsterAirbyteTranslator()

    # TODO: update to assets specs
    (
        deps,
        outs,
        internal_asset_deps,
    ) = build_airbyte_multi_asset_args(
        project=project,
        translator=dagster_airbyte_translator,
        create_assets_for_normalization_tables=create_assets_for_normalization_tables,
    )

    return multi_asset(
        name=name,
        deps=deps,
        outs=outs,
        internal_asset_deps=internal_asset_deps,
        compute_kind="airbyte",
        required_resource_keys=required_resource_keys,
    )


def build_airbyte_multi_asset_args(
    project: AirbyteProject,
    translator: DagsterAirbyteTranslator,
    create_assets_for_normalization_tables: bool,
):
    # TODO: support AssetKey prefix

    deps: List[AssetDep] = []
    outs: Dict[str, AssetOut] = {}
    internal_asset_deps: Dict[str, Set[AssetKey]] = {}

    for connection_id, connection_metadata in project.connections_metadata:
        stream_table_metadata = connection_metadata.parse_stream_tables(
            create_assets_for_normalization_tables
        )
        schema_by_table_name = get_schema_by_table_name(stream_table_metadata)

        table_to_asset_key = partial(translator.get_asset_key, connection_metadata)

        destination_tables = list(stream_table_metadata.keys())
        normalization_tables = {
            table: set(metadata.normalization_tables.keys())
            for table, metadata in stream_table_metadata.items()
        }
        group_name = translator.get_group_name_from_connection_metadata(connection_metadata)
        io_manager_key = translator.get_io_manager_key(connection_metadata.name)
        # schema_by_table_name = schema_by_table_name
        table_to_asset_key_fn = table_to_asset_key
        freshness_policy = translator.get_freshness_policy(connection_metadata)
        auto_materialize_policy = translator.get_auto_materialize_policy(connection_metadata)
        asset_key_prefix = translator.get_asset_key_prefix(connection_metadata)

        # Generate a list of outputs, the set of destination tables plus any affiliated
        # normalization tables
        tables = list(
            chain.from_iterable(
                chain(
                    [destination_tables],
                    normalization_tables.values() if normalization_tables else [],
                )
            )
        )

        # TODO: manage collisions with group_name
        outputs = {
            table_to_output_name_fn(table): AssetKey(
                [*asset_key_prefix, *table_to_asset_key_fn(table).path]
            )
            for table in tables
        }

        internal_deps: Dict[str, Set[AssetKey]] = {}

        metadata_encodable_normalization_tables = (
            {k: list(v) for k, v in normalization_tables.items()} if normalization_tables else {}
        )

        # If normalization tables are specified, we need to add a dependency from the destination table
        # to the affiliated normalization table
        if len(metadata_encodable_normalization_tables) > 0:
            for base_table, derived_tables in metadata_encodable_normalization_tables.items():
                for derived_table in derived_tables:
                    # TODO: manage collisions with group_name
                    internal_deps[derived_table] = {
                        AssetKey([*asset_key_prefix, *table_to_asset_key_fn(base_table).path])
                    }

        # upstream_assets is None by default in the original code, meaning there were no deps.
        # TODO: Confirm deps and upstream_assets are None by default
        keys_by_input_name = {}

        keys_by_output_name = outputs
        internal_asset_deps = internal_deps
        # group_name = group_name

        # TODO: not used?
        # key_prefix = asset_key_prefix
        # can_subset = False

        metadata_by_output_name = (
            {
                table: {"table_schema": MetadataValue.table_schema(schema_by_table_name[table])}
                for table in tables
            }
            if schema_by_table_name
            else None
        )
        freshness_policies_by_output_name = (
            {output: freshness_policy for output in outputs} if freshness_policy else None
        )
        auto_materialize_policies_by_output_name = (
            {output: auto_materialize_policy for output in outputs}
            if auto_materialize_policy
            else None
        )

        # TODO: Add to asset out
        extra_metadata = {
            "connection_id": connection_id,
            "group_name": group_name,
            "destination_tables": destination_tables,
            "normalization_tables": metadata_encodable_normalization_tables,
            "io_manager_key": io_manager_key,
        }

        metadata = cast(Mapping[str, Any], extra_metadata)
        group_name = cast(Optional[str], metadata["group_name"])
        io_manager_key = cast(Optional[str], metadata["io_manager_key"])

        # TODO: should be added to metadata of asset out
        # connection_id = cast(str, metadata["connection_id"])
        # destination_tables = cast(List[str], metadata["destination_tables"])
        # normalization_tables = cast(Mapping[str, List[str]], metadata["normalization_tables"])

        # TODO: collisions?
        deps.append(*list((keys_by_input_name or {}).values()))

        # TODO: Update will work if collisions are handled
        # TODO: update extra metadata after cleaning code
        # TODO: update to asset specs
        outs.update(
            {
                k: AssetOut(
                    key=v,
                    metadata=(
                        {
                            **extra_metadata,
                            **{
                                k: cast(TableSchemaMetadataValue, v)
                                for k, v in metadata_by_output_name.get(k, {}).items()
                            },
                        }
                        if metadata_by_output_name
                        else extra_metadata
                    ),
                    io_manager_key=io_manager_key,
                    freshness_policy=(
                        freshness_policies_by_output_name.get(k)
                        if freshness_policies_by_output_name
                        else None
                    ),
                    dagster_type=Nothing,
                    auto_materialize_policy=auto_materialize_policies_by_output_name.get(k, None)
                    if auto_materialize_policies_by_output_name
                    else None,
                    group_name=group_name,
                )
                for k, v in (keys_by_output_name or {}).items()
            }
        )

        # TODO: Same as above, update will work if collisions are handled
        internal_asset_deps.update({k: set(v) for k, v in (internal_asset_deps or {}).items()})

    return deps, outs, internal_asset_deps
