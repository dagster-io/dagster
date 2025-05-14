from collections.abc import Mapping
from typing import Any, Optional

import pytest
import responses
from dagster import AssetKey
from dagster_dbt.asset_utils import build_dbt_specs
from dagster_dbt.cloud_v2.asset_decorator import dbt_cloud_assets
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_shared.check.functions import ParameterCheckError

from dagster_dbt_tests.cloud_v2.conftest import get_sample_manifest_json


def test_asset_defs(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    @dbt_cloud_assets(workspace=workspace)
    def my_dbt_cloud_assets(): ...

    assert len(fetch_workspace_data_api_mocks.calls) == 8

    assets_def_specs = list(my_dbt_cloud_assets.specs)
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
    def my_dbt_cloud_assets(): ...

    assets_def_specs = list(my_dbt_cloud_assets.specs)
    asset_spec = next(iter(assets_def_specs))
    assert "custom" in asset_spec.metadata
    assert asset_spec.metadata["custom"] == "metadata"

    # Clearing cache for other tests
    workspace.load_specs.cache_clear()


@pytest.mark.parametrize(
    ["select", "exclude", "selector", "expected_dbt_resource_names"],
    [
        (
            None,
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
            None,
            {
                "raw_customers",
                "stg_customers",
            },
        ),
        (
            "raw_customers+",
            None,
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
            None,
            {
                "stg_customers",
                "customers",
            },
        ),
        (
            None,
            "orders",
            None,
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
            None,
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
            None,
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
            None,
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
            },
        ),
        (
            None,
            "tag:does-not-exist",
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
            "",
            None,
            "raw_customer_child_models",
            {
                "stg_customers",
                "customers",
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
        "--selector raw_customer_child_models",
    ],
)
def test_selections(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    select: Optional[str],
    exclude: Optional[str],
    selector: Optional[str],
    expected_dbt_resource_names: set[str],
) -> None:
    select = select or "fqn:*"
    exclude = exclude or ""
    selector = selector or ""

    expected_asset_keys = {AssetKey(key) for key in expected_dbt_resource_names}
    expected_specs, _ = build_dbt_specs(
        manifest=get_sample_manifest_json(),
        translator=DagsterDbtTranslator(),
        select=select,
        exclude=exclude,
        selector=selector,
        io_manager_key=None,
        project=None,
    )

    @dbt_cloud_assets(
        workspace=workspace,
        select=select,
        exclude=exclude,
        selector=selector,
    )
    def my_dbt_assets(): ...

    assert len(my_dbt_assets.keys) == len(expected_specs)
    assert my_dbt_assets.keys == {spec.key for spec in expected_specs}
    assert my_dbt_assets.keys == expected_asset_keys
    assert my_dbt_assets.op.tags.get("dagster_dbt/select") == select
    assert my_dbt_assets.op.tags.get("dagster_dbt/exclude") == exclude
    assert my_dbt_assets.op.tags.get("dagster_dbt/selector") == selector


def test_dbt_cloud_asset_selection_selector_invalid(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with pytest.raises(ParameterCheckError):

        @dbt_cloud_assets(
            workspace=workspace,
            select="stg_customers",
            selector="raw_customer_child_models",
        )
        def selected_dbt_assets(): ...

    with pytest.raises(ParameterCheckError):

        @dbt_cloud_assets(
            workspace=workspace,
            exclude="stg_customers",
            selector="raw_customer_child_models",
        )
        def selected_dbt_assets(): ...

    with pytest.raises(ValueError):

        @dbt_cloud_assets(
            workspace=workspace,
            selector="fake_selector_does_not_exist",
        )
        def selected_dbt_assets(): ...
