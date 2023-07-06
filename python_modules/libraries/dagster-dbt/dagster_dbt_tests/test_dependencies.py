from pathlib import Path

import pytest
from dagster import (
    AssetKey,
    asset,
)
from dagster._core.errors import DagsterInvalidInvocationError
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.core.resources_v2 import DbtManifest

test_dagster_metadata_manifest = DbtManifest.read(
    path=Path(__file__).parent.joinpath("dbt_projects", "test_dagster_metadata", "manifest.json")
)


def test_get_asset_key_for_dbt_unique_id() -> None:
    assert test_dagster_metadata_manifest.get_asset_key_for_dbt_unique_id(
        "source.test_dagster_metadata.jaffle_shop.raw_events"
    ) == AssetKey(["jaffle_shop", "raw_events"])


def test_get_explicit_asset_key_for_dbt_unique_id_() -> None:
    assert test_dagster_metadata_manifest.get_asset_key_for_dbt_unique_id(
        "source.test_dagster_metadata.jaffle_shop.raw_customers"
    ) == AssetKey(["customized", "source", "jaffle_shop", "main", "raw_customers"])


def test_asset_downstream_of_dbt_asset() -> None:
    upstream_asset_key = AssetKey(["orders"])

    @dbt_assets(manifest=test_dagster_metadata_manifest)
    def my_dbt_assets():
        ...

    @asset(non_argument_deps={test_dagster_metadata_manifest.get_asset_key_for_model("orders")})
    def downstream_python_asset():
        ...

    assert upstream_asset_key in my_dbt_assets.keys_by_output_name.values()
    assert set(downstream_python_asset.keys_by_input_name.values()) == {upstream_asset_key}


def test_nonexistent_dbt_unique_id() -> None:
    with pytest.raises(DagsterInvalidInvocationError):
        test_dagster_metadata_manifest.get_asset_key_for_dbt_unique_id(unique_id="nonexistent")


def test_get_asset_keys_by_output_name_for_source() -> None:
    assert test_dagster_metadata_manifest.get_asset_keys_by_output_name_for_source(
        "jaffle_shop"
    ) == {
        "raw_customers": AssetKey(["customized", "source", "jaffle_shop", "main", "raw_customers"]),
        "raw_events": AssetKey(["jaffle_shop", "raw_events"]),
    }

    with pytest.raises(
        DagsterInvalidInvocationError, match="Could not find a dbt source with name"
    ):
        test_dagster_metadata_manifest.get_asset_keys_by_output_name_for_source("nonexistent")


def test_get_asset_keys_for_model() -> None:
    assert test_dagster_metadata_manifest.get_asset_key_for_model("stg_customers") == AssetKey(
        ["customized", "staging", "customers"]
    )

    assert test_dagster_metadata_manifest.get_asset_key_for_model("customers") == AssetKey(
        ["customers"]
    )

    with pytest.raises(DagsterInvalidInvocationError, match="Could not find a dbt model with name"):
        test_dagster_metadata_manifest.get_asset_key_for_model("nonexistent")
