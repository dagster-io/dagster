from itertools import chain
from typing import List, Mapping, Optional, Set

from dagster_airbyte.utils import generate_materializations

from dagster import AssetKey, AssetOut, Output
from dagster import _check as check
from dagster._annotations import experimental
from dagster._core.definitions import AssetsDefinition, multi_asset


@experimental
def build_airbyte_assets(
    connection_id: str,
    destination_tables: List[str],
    asset_key_prefix: Optional[List[str]] = None,
    normalization_tables: Optional[Mapping[str, Set[str]]] = None,
    upstream_assets: Optional[Set[AssetKey]] = None,
) -> List[AssetsDefinition]:
    """
    Builds a set of assets representing the tables created by an Airbyte sync operation.

    Args:
        connection_id (str): The Airbyte Connection ID that this op will sync. You can retrieve this
            value from the "Connections" tab of a given connector in the Airbyte UI.
        destination_tables (List[str]): The names of the tables that you want to be represented
            in the Dagster asset graph for this sync. This will generally map to the name of the
            stream in Airbyte, unless a stream prefix has been specified in Airbyte.
        normalization_tables (Optional[Mapping[str, List[str]]]): If you are using Airbyte's
            normalization feature, you may specify a mapping of destination table to a list of
            derived tables that will be created by the normalization process.
        asset_key_prefix (Optional[List[str]]): A prefix for the asset keys inside this asset.
            If left blank, assets will have a key of `AssetKey([table_name])`.
        upstream_assets (Optional[Set[AssetKey]]): A list of assets to add as sources.
    """

    asset_key_prefix = check.opt_list_param(asset_key_prefix, "asset_key_prefix", of_type=str)

    # Generate a list of outputs, the set of destination tables plus any affiliated
    # normalization tables
    tables = chain.from_iterable(
        chain([destination_tables], normalization_tables.values() if normalization_tables else [])
    )
    outputs = {table: AssetOut(key=AssetKey(asset_key_prefix + [table])) for table in tables}

    internal_deps = {}

    # If normalization tables are specified, we need to add a dependency from the destination table
    # to the affilitated normalization table
    if normalization_tables:
        for base_table, derived_tables in normalization_tables.items():
            for derived_table in derived_tables:
                internal_deps[derived_table] = {AssetKey(asset_key_prefix + [base_table])}

    # All non-normalization tables depend on any user-provided upstream assets
    for table in destination_tables:
        internal_deps[table] = upstream_assets or set()

    @multi_asset(
        name=f"airbyte_sync_{connection_id[:5]}",
        non_argument_deps=upstream_assets or set(),
        outs=outputs,
        internal_asset_deps=internal_deps,
        required_resource_keys={"airbyte"},
        compute_kind="airbyte",
    )
    def _assets(context):
        ab_output = context.resources.airbyte.sync_and_poll(connection_id=connection_id)
        for materialization in generate_materializations(ab_output, asset_key_prefix):
            table_name = materialization.asset_key.path[-1]
            if table_name in destination_tables:
                yield Output(
                    value=None,
                    output_name=table_name,
                    metadata={
                        entry.label: entry.entry_data for entry in materialization.metadata_entries
                    },
                )
                # Also materialize any normalization tables affiliated with this destination
                # e.g. nested objects, lists etc
                if normalization_tables:
                    for dependent_table in normalization_tables.get(table_name, set()):
                        yield Output(
                            value=None,
                            output_name=dependent_table,
                        )
            else:
                yield materialization

    return [_assets]
