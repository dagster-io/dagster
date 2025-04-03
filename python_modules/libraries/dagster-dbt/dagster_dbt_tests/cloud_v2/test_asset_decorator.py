from collections.abc import Mapping
from typing import Any, Optional

import pytest
import responses
from dagster import AssetKey
from dagster_dbt.asset_utils import build_dbt_specs
from dagster_dbt.cloud_v2.asset_decorator import dbt_cloud_assets
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

from dagster_dbt_tests.cloud_v2.conftest import get_sample_manifest_json


def test_asset_defs(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    @dbt_cloud_assets(workspace=workspace)
    def my_fivetran_assets(): ...

    assert len(fetch_workspace_data_api_mocks.calls) == 7

    assets_def_specs = list(my_fivetran_assets.specs)
    all_assets_keys = [asset.key for asset in assets_def_specs]

    # 8 dbt models
    assert len(assets_def_specs) == 8
    assert len(all_assets_keys) == 8

    # Sanity check outputs
    first_asset_key = next(key for key in sorted(all_assets_keys))
    assert first_asset_key.path == ["customers"]
    first_asset_kinds = next(spec.kinds for spec in sorted(assets_def_specs))
    assert "dbtcloud" in first_asset_kinds
    assert "dbt" not in first_asset_kinds

    # Clearing cache for other tests
    workspace.load_specs.cache_clear()


class MyCustomTranslator(DagsterDbtTranslator):
    # DagsterDbtTranslator doesn't have a `get_asset_spec` method yet.
    def get_metadata(self, dbt_resource_props: Mapping[str, Any]) -> Mapping[str, Any]:
        default_metadata = super().get_metadata(dbt_resource_props)
        return {**default_metadata, "custom": "metadata"}


def test_asset_defs_with_custom_metadata(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    @dbt_cloud_assets(workspace=workspace, dagster_dbt_translator=MyCustomTranslator())
    def my_fivetran_assets(): ...

    assets_def_specs = list(my_fivetran_assets.specs)
    asset_spec = next(iter(assets_def_specs))
    assert "custom" in asset_spec.metadata
    assert asset_spec.metadata["custom"] == "metadata"

    # Clearing cache for other tests
    workspace.load_specs.cache_clear()


@pytest.mark.parametrize(
    ["select", "exclude", "expected_dbt_resource_names"],
    [
        (
            None,
            None,
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
        (
            "raw_customers stg_customers",
            None,
            {
                "raw_customers",
                "stg_customers",
            },
        ),
        (
            "raw_customers+",
            None,
            {
                "raw_customers",
                "stg_customers",
                "customers",
            },
        ),
        (
            "resource_type:model",
            None,
            {
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
        (
            "raw_customers+,resource_type:model",
            None,
            {
                "stg_customers",
                "customers",
            },
        ),
        (
            None,
            "orders",
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
            },
        ),
        (
            None,
            "raw_customers+",
            {
                "raw_orders",
                "raw_payments",
                "stg_orders",
                "stg_payments",
                "orders",
            },
        ),
        (
            None,
            "raw_customers stg_customers",
            {
                "raw_orders",
                "raw_payments",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
        (
            None,
            "resource_type:model",
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
            },
        ),
        (
            None,
            "tag:does-not-exist",
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
    ],
    ids=[
        "--select fqn:*",
        "--select raw_customers stg_customers",
        "--select raw_customers+",
        "--select resource_type:model",
        "--select raw_customers+,resource_type:model",
        "--exclude orders",
        "--exclude raw_customers+",
        "--exclude raw_customers stg_customers",
        "--exclude resource_type:model",
        "--exclude tag:does-not-exist",
    ],
)
def test_selections(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    select: Optional[str],
    exclude: Optional[str],
    expected_dbt_resource_names: set[str],
) -> None:
    select = select or "fqn:*"
    exclude = exclude or ""

    expected_asset_keys = {AssetKey(key) for key in expected_dbt_resource_names}
    expected_specs, _ = build_dbt_specs(
        manifest=get_sample_manifest_json(),
        translator=DagsterDbtTranslator(),
        select=select,
        exclude=exclude,
        io_manager_key=None,
        project=None,
    )

    @dbt_cloud_assets(
        workspace=workspace,
        select=select,
        exclude=exclude,
    )
    def my_dbt_assets(): ...

    assert len(my_dbt_assets.keys) == len(expected_specs)
    assert my_dbt_assets.keys == {spec.key for spec in expected_specs}
    assert my_dbt_assets.keys == expected_asset_keys
    assert my_dbt_assets.op.tags.get("dagster_dbt/select") == select
    assert my_dbt_assets.op.tags.get("dagster_dbt/exclude") == exclude
