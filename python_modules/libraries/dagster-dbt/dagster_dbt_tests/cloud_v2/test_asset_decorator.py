from collections.abc import Mapping
from typing import Any

import responses
from dagster_dbt.cloud_v2.asset_decorator import dbt_cloud_assets
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator


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
