import os
from typing import Any, Dict

import pytest
from dagster import AssetExecutionContext, AssetKey
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.core.resource import DbtCliResource
from dagster_dbt.metadata_set import DbtMetadataSet

pytestmark: pytest.MarkDecorator = pytest.mark.derived_metadata


def test_materialization_type(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets(): ...

    materialization_types_by_key = {
        spec.key: DbtMetadataSet.extract(spec.metadata).materialization_type
        for spec in my_dbt_assets.specs
    }
    assert materialization_types_by_key == {
        AssetKey(["stg_orders"]): "view",
        AssetKey(["stg_customers"]): "view",
        AssetKey(["orders"]): "table",
        AssetKey(["customers"]): "table",
        AssetKey(["raw_customers"]): "seed",
        AssetKey(["raw_orders"]): "seed",
        AssetKey(["raw_payments"]): "seed",
        AssetKey(["stg_payments"]): "view",
    }


def test_storage_address(
    test_jaffle_shop_manifest: Dict[str, Any],
) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    storage_address_metas = {
        ".".join(key.path): TableMetadataSet.extract(my_dbt_assets.metadata_by_key[key])
        for key in my_dbt_assets.keys_by_output_name.values()
    }

    assert all(
        storage_address_meta.relation_identifier
        for storage_address_meta in storage_address_metas.values()
    )
    jaffle_shop_duckdb_dbfile_name = os.getenv("DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_NAME")
    # spot check a few storage addresses
    assert (
        storage_address_metas["customers"].relation_identifier
        == f"{jaffle_shop_duckdb_dbfile_name}.dev.customers"
    )
    assert (
        storage_address_metas["raw_customers"].relation_identifier
        == f"{jaffle_shop_duckdb_dbfile_name}.dev.raw_customers"
    )
    assert (
        storage_address_metas["stg_orders"].relation_identifier
        == f"{jaffle_shop_duckdb_dbfile_name}.dev.stg_orders"
    )


def test_storage_address_alias(
    test_dbt_alias_manifest: Dict[str, Any],
) -> None:
    @dbt_assets(manifest=test_dbt_alias_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    storage_address_metas = {
        ".".join(key.path): TableMetadataSet.extract(my_dbt_assets.metadata_by_key[key])
        for key in my_dbt_assets.keys_by_output_name.values()
    }

    assert all(
        storage_address_meta.relation_identifier
        for storage_address_meta in storage_address_metas.values()
    )

    jaffle_shop_duckdb_dbfile_name = os.getenv("DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_NAME")
    # test that we can have tables with dots in their names, from
    # user-defined aliases
    assert (
        storage_address_metas["customers"].relation_identifier
        == f"{jaffle_shop_duckdb_dbfile_name}.main.dagster.customers"
    )
    assert (
        storage_address_metas["orders"].relation_identifier
        == f"{jaffle_shop_duckdb_dbfile_name}.main.dagster.orders"
    )
