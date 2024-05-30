from typing import Any, Dict

import pytest
from dagster import (
    AssetExecutionContext,
)
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.core.resources_v2 import DbtCliResource

pytestmark: pytest.MarkDecorator = pytest.mark.derived_metadata


def test_storage_address(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
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

    # spot check a few storage addresses
    assert (
        storage_address_metas["customers"].relation_identifier == "master_jaffle_shop.dev.customers"
    )
    assert (
        storage_address_metas["raw_customers"].relation_identifier
        == "master_jaffle_shop.dev.raw_customers"
    )
    assert (
        storage_address_metas["stg_orders"].relation_identifier
        == "master_jaffle_shop.dev.stg_orders"
    )
