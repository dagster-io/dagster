from collections.abc import Mapping
from typing import Any, Optional, Union

import pytest
import responses
from dagster import AssetExecutionContext, AssetKey, AssetSpec, OpExecutionContext
from dagster._core.errors import DagsterInvariantViolationError
from dagster_dbt import DbtProject
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


class MyCustomTranslatorWithGroupName(DagsterDbtTranslator):
    def get_asset_spec(
        self,
        manifest: Mapping[str, Any],
        unique_id: str,
        project: Optional[DbtProject],
    ) -> AssetSpec:
        default_spec = super().get_asset_spec(
            manifest=manifest, unique_id=unique_id, project=project
        )
        return default_spec.replace_attributes(group_name="my_group_name")


def test_translator_invariant_group_name_with_asset_decorator(
    workspace: DbtCloudWorkspace,
    asset_decorator_group_name_api_mocks: responses.RequestsMock,
) -> None:
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Cannot set group_name parameter on dbt_cloud_assets",
    ):

        @dbt_cloud_assets(
            workspace=workspace,
            group_name="my_asset_decorator_group_name",
            dagster_dbt_translator=MyCustomTranslatorWithGroupName(),
        )
        def my_dbt_cloud_assets(): ...


@pytest.mark.parametrize(
    "context_type",
    [
        OpExecutionContext,
        AssetExecutionContext,
    ],
    ids=[
        "dbt_cloud_cli_selection_with_op_execution_context",
        "dbt_cloud_cli_selection_with_asset_execution_context",
    ],
)
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
    context_type: Union[type[AssetExecutionContext], type[OpExecutionContext]],
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
    def my_dbt_assets(context: context_type): ...  # pyright: ignore

    assert len(my_dbt_assets.keys) == len(expected_specs)
    assert my_dbt_assets.keys == {spec.key for spec in expected_specs}
    assert my_dbt_assets.keys == expected_asset_keys
    assert my_dbt_assets.op.tags.get("dagster_dbt/select") == select
    assert my_dbt_assets.op.tags.get("dagster_dbt/exclude") == exclude
    assert my_dbt_assets.op.tags.get("dagster_dbt/selector") == selector


def test_asset_checks_excluded_by_tag_unit_test() -> None:
    """Verifies that dbt tests tagged with 'unit-test' are excluded from the resulting
    AssetCheckSpecs when calling build_dbt_specs with exclude='tag:unit-test'.

    This allows @dbt_assets to exclude EqualExperts/dbt_unit_testing tests.
    """
    select = "fqn:*"
    exclude = "tag:unit-test"
    manifest = get_sample_manifest_json()

    # Manually edited a node here because it is complicated to cleanly edit
    # the existing manifest.json to add a real dbt_unit_testing test
    test_node_uid = "test.jaffle_shop.unique_customers_customer_id.c5af1ff4b1"
    test_nodes = [
        (uid, node) for uid, node in manifest["nodes"].items() if node["resource_type"] == "test"
    ]
    for uid, node in test_nodes:
        if uid == test_node_uid:
            node["tags"] = ["unit-test"]
            break

    _, checks = build_dbt_specs(
        manifest=manifest,
        translator=DagsterDbtTranslator(),
        select=select,
        exclude=exclude,
        selector="",
        io_manager_key=None,
        project=None,
    )

    found_ids = {c.metadata["dagster_dbt/unique_id"] for c in checks}
    assert test_node_uid not in found_ids, f"{test_node_uid} should have been excluded"


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
