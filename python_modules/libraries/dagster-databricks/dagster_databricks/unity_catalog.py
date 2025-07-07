from typing import TYPE_CHECKING, Optional

import requests
from dagster import AssetKey, AssetsDefinition, TableColumn, TableSchema
from dagster._annotations import preview
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.external_asset import external_asset_from_spec

if TYPE_CHECKING:
    from collections.abc import Sequence

    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.catalog import TableInfo


@preview
def unity_catalog_assets(
    client: "WorkspaceClient",
    *,
    catalog: str,
    schema: Optional[str] = None,
    include_views: bool = True,
    with_lineage: bool = True,
    # Need to decide whether or not to keep the asset_key_prefix parameter.
    asset_key_prefix: "Sequence[str]" = (),
    group_name: Optional[str] = None,
) -> list[AssetsDefinition]:
    """Return Dagster assets representing Unity Catalog tables and views."""
    assets: list[AssetsDefinition] = []

    if schema is None:
        raise ValueError("schema parameter is required when listing Unity Catalog tables")

    tables = client.tables.list(catalog_name=catalog, schema_name=schema)

    for table in tables:
        # No API to exclude views, so we do this!
        # Import TableType locally to avoid circular import
        from databricks.sdk.service.catalog import TableType

        if not include_views and table.table_type == TableType.VIEW:
            continue

        key_parts = [*asset_key_prefix, catalog]
        if table.schema_name:
            key_parts.append(table.schema_name)
        if table.name:
            key_parts.append(table.name)
        key = AssetKey(key_parts)
        upstream_keys: list[AssetKey] = []

        if with_lineage and schema and table.name:
            upstream_keys = _get_lineage_for_table(
                catalog=catalog, schema=schema, table=table.name, client=client
            )
        columns = _get_schema_for_table(table)
        spec = AssetSpec(
            key=key,
            deps=upstream_keys,
            owners=[table.owner] if table.owner else None,
            description=table.comment,
            kinds={"Databricks"},
            group_name=group_name,
            metadata={"dagster/column_schema": TableSchema(columns)},
        )
        assets.append(external_asset_from_spec(spec))

    return assets


def _get_lineage_for_table(
    catalog: str, schema: str, table: str, client: "WorkspaceClient"
) -> list[AssetKey]:
    try:
        response = requests.get(
            f"{client.config.host}/api/2.0/lineage-tracking/table-lineage",
            headers={
                "Authorization": f"Bearer {client.config.token}",
                "Content-Type": "application/json",
            },
            params={"table_name": f"{catalog}.{schema}.{table}", "include_entity_lineage": "true"},
        )
        response.raise_for_status()
        upstreams = response.json().get("upstreams", [])
        return [
            AssetKey(
                [
                    src["tableInfo"]["catalog_name"],
                    src["tableInfo"]["schema_name"],
                    src["tableInfo"]["name"],
                ]
            )
            for src in upstreams
            if "tableInfo" in src
        ]
    except Exception:
        return []


def _get_schema_for_table(table: "TableInfo") -> list:
    columns = []
    if table.columns:
        for column in table.columns:
            if column.name and column.type_name:
                columns.append(
                    TableColumn(column.name, column.type_name.name, description=column.comment)
                )
    return columns
