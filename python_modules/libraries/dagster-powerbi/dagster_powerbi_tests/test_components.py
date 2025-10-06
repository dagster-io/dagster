import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Any, Callable, Optional, Union

import pytest
from dagster import AssetKey
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster._utils import alter_sys_path
from dagster.components.testing import create_defs_folder_sandbox
from dagster_powerbi import PowerBIWorkspaceComponent

ensure_dagster_tests_import()

from dagster_test.dg_utils.utils import ProxyRunner, isolated_example_project_foo_bar


@contextmanager
def setup_powerbi_ready_project() -> Iterator[None]:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
        alter_sys_path(to_add=[str(Path.cwd() / "src")], to_remove=[]),
    ):
        yield


@contextmanager
def setup_powerbi_component(
    defs_yaml_contents: dict[str, Any],
) -> Iterator[tuple[PowerBIWorkspaceComponent, Definitions]]:
    """Sets up a components project with a powerbi component based on provided params."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=PowerBIWorkspaceComponent,
            defs_yaml_contents=defs_yaml_contents,
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, PowerBIWorkspaceComponent)
            yield component, defs


@pytest.mark.parametrize(
    "enable_semantic_model_refresh, should_be_executable",
    [
        (True, True),
        (False, False),
        (["Sales & Returns Sample v201912"], True),
        (["Sales & Returns Sample v201911", "Sales & Returns Sample v201912"], True),
        (["Does not exist"], False),
    ],
)
def test_basic_component_load(
    workspace_data_api_mocks,
    workspace_id: str,
    enable_semantic_model_refresh: Union[bool, list[str]],
    should_be_executable: bool,
) -> None:
    with (
        setup_powerbi_component(
            defs_yaml_contents={
                "type": "dagster_powerbi.PowerBIWorkspaceComponent",
                "attributes": {
                    "workspace": {
                        "credentials": {
                            "token": uuid.uuid4().hex,
                        },
                        "workspace_id": workspace_id,
                    },
                    "use_workspace_scan": False,
                    "enable_semantic_model_refresh": enable_semantic_model_refresh,
                },
            }
        ) as (
            component,
            defs,
        ),
    ):
        assert defs.resolve_asset_graph().get_all_asset_keys() == {
            AssetKey(["semantic_model", "Sales_Returns_Sample_v201912"]),
            AssetKey(["dashboard", "Sales_Returns_Sample_v201912"]),
            AssetKey(["data_27_09_2019_xlsx"]),
            AssetKey(["sales_marketing_datas_xlsx"]),
            AssetKey(["report", "Sales_Returns_Sample_v201912"]),
        }

        assert (
            defs.get_assets_def(
                AssetKey(["semantic_model", "Sales_Returns_Sample_v201912"])
            ).is_executable
            == should_be_executable
        )


@pytest.mark.parametrize(
    "attributes, assertion, should_error",
    [
        ({"group_name": "group"}, lambda asset_spec: asset_spec.group_name == "group", False),
        (
            {"owners": ["team:analytics"]},
            lambda asset_spec: asset_spec.owners == ["team:analytics"],
            False,
        ),
        ({"tags": {"foo": "bar"}}, lambda asset_spec: asset_spec.tags.get("foo") == "bar", False),
        (
            {"kinds": ["snowflake", "dbt"]},
            lambda asset_spec: "snowflake" in asset_spec.kinds and "dbt" in asset_spec.kinds,
            False,
        ),
        (
            {"tags": {"foo": "bar"}, "kinds": ["snowflake", "dbt"]},
            lambda asset_spec: "snowflake" in asset_spec.kinds
            and "dbt" in asset_spec.kinds
            and asset_spec.tags.get("foo") == "bar",
            False,
        ),
        ({"code_version": "1"}, lambda asset_spec: asset_spec.code_version == "1", False),
        (
            {"description": "some description"},
            lambda asset_spec: asset_spec.description == "some description",
            False,
        ),
        (
            {"metadata": {"foo": "bar"}},
            lambda asset_spec: asset_spec.metadata.get("foo") == "bar",
            False,
        ),
        (
            {"deps": ["customers"]},
            lambda asset_spec: len(asset_spec.deps) == 1
            and asset_spec.deps[0].asset_key == AssetKey("customers"),
            False,
        ),
        (
            {"automation_condition": "{{ automation_condition.eager() }}"},
            lambda asset_spec: asset_spec.automation_condition is not None,
            False,
        ),
        (
            {"key": "{{ spec.key.to_user_string() + '_suffix' }}"},
            lambda asset_spec: asset_spec.key
            == AssetKey(["semantic_model", "Sales_Returns_Sample_v201912_suffix"]),
            False,
        ),
        (
            {"key_prefix": "cool_prefix"},
            lambda asset_spec: asset_spec.key.has_prefix(["cool_prefix"]),
            False,
        ),
    ],
    ids=[
        "group_name",
        "owners",
        "tags",
        "kinds",
        "tags-and-kinds",
        "code-version",
        "description",
        "metadata",
        "deps",
        "automation_condition",
        "key",
        "key_prefix",
    ],
)
def test_translation(
    attributes: Mapping[str, Any],
    assertion: Optional[Callable[[AssetSpec], bool]],
    should_error: bool,
    workspace_id: str,
    workspace_data_api_mocks,
) -> None:
    wrapper = pytest.raises(Exception) if should_error else nullcontext()
    with wrapper:
        body = {
            "type": "dagster_powerbi.PowerBIWorkspaceComponent",
            "attributes": {
                "workspace": {
                    "credentials": {
                        "token": uuid.uuid4().hex,
                    },
                    "workspace_id": workspace_id,
                },
                "use_workspace_scan": False,
            },
        }
        body["attributes"]["translation"] = attributes
        with (
            setup_powerbi_component(
                defs_yaml_contents=body,
            ) as (
                component,
                defs,
            ),
        ):
            if "key" in attributes:
                key = AssetKey(["semantic_model", "Sales_Returns_Sample_v201912_suffix"])
            elif "key_prefix" in attributes:
                key = AssetKey(["cool_prefix", "semantic_model", "Sales_Returns_Sample_v201912"])
            else:
                key = AssetKey(["semantic_model", "Sales_Returns_Sample_v201912"])

            assets_def = defs.get_assets_def(key)
            if assertion:
                assert assertion(assets_def.get_asset_spec(key))


def test_per_content_type_translation(
    workspace_id: str,
    workspace_data_api_mocks,
) -> None:
    body = {
        "type": "dagster_powerbi.PowerBIWorkspaceComponent",
        "attributes": {
            "workspace": {
                "credentials": {
                    "token": uuid.uuid4().hex,
                },
                "workspace_id": workspace_id,
            },
            "use_workspace_scan": False,
            "translation": {
                "tags": {"custom_tag": "custom_value"},
                "for_semantic_model": {
                    "tags": {"is_semantic_model": "true"},
                },
                "for_dashboard": {
                    "tags": {"is_dashboard": "true"},
                    "metadata": {"id": "{{ data.properties.id }}"},
                },
                "for_report": {
                    "tags": {"is_report": "true"},
                    "metadata": {"base_key": "{{ spec.key.to_user_string() }}"},
                },
                "for_data_source": {
                    "key_prefix": "data_source",
                },
            },
        },
    }
    with (
        setup_powerbi_component(
            defs_yaml_contents=body,
        ) as (
            component,
            defs,
        ),
    ):
        semantic_model_spec = defs.get_assets_def(
            AssetKey(["semantic_model", "Sales_Returns_Sample_v201912"])
        ).get_asset_spec(AssetKey(["semantic_model", "Sales_Returns_Sample_v201912"]))
        assert semantic_model_spec.tags.get("custom_tag") == "custom_value"
        assert semantic_model_spec.tags.get("is_semantic_model") == "true"

        dashboard_spec = defs.get_assets_def(
            AssetKey(["dashboard", "Sales_Returns_Sample_v201912"])
        ).get_asset_spec(AssetKey(["dashboard", "Sales_Returns_Sample_v201912"]))
        assert dashboard_spec.tags.get("custom_tag") == "custom_value"
        assert dashboard_spec.tags.get("is_dashboard") == "true"
        assert dashboard_spec.metadata.get("id") == "efee0b80-4511-42e1-8ee0-2544fd44e122"

        report_spec = defs.get_assets_def(
            AssetKey(["report", "Sales_Returns_Sample_v201912"])
        ).get_asset_spec(AssetKey(["report", "Sales_Returns_Sample_v201912"]))
        assert report_spec.tags.get("custom_tag") == "custom_value"
        assert report_spec.tags.get("is_report") == "true"
        assert report_spec.metadata.get("base_key") == "report/Sales_Returns_Sample_v201912"

        data_source_def = defs.get_assets_def(
            AssetKey(["data_source", "sales_marketing_datas_xlsx"])
        )
        assert data_source_def


def test_subclass_override_get_asset_spec(
    workspace_id: str,
    workspace_data_api_mocks,
) -> None:
    """Test that subclasses of PowerBIWorkspaceComponent can override get_asset_spec method."""
    from dagster.components.core.component_tree import ComponentTree
    from dagster_powerbi.resource import PowerBIServicePrincipal, PowerBIWorkspace

    class CustomPowerBIWorkspaceComponent(PowerBIWorkspaceComponent):
        def get_asset_spec(self, data) -> AssetSpec:
            # Override to add custom metadata and tags
            base_spec = super().get_asset_spec(data)
            return base_spec.replace_attributes(
                metadata={**base_spec.metadata, "custom_override": "test_value"},
                tags={**base_spec.tags, "custom_tag": "override_test"},
            )

    defs = CustomPowerBIWorkspaceComponent(
        workspace=PowerBIWorkspace(
            credentials=PowerBIServicePrincipal(
                client_id="test_client_id",
                client_secret="test_client_secret",
                tenant_id="test_tenant_id",
            ),
            workspace_id=workspace_id,
        ),
        use_workspace_scan=False,
    ).build_defs(ComponentTree.for_test().load_context)

    # Verify that the custom get_asset_spec method is being used
    assets_def = defs.get_assets_def(AssetKey(["semantic_model", "Sales_Returns_Sample_v201912"]))
    asset_spec = assets_def.get_asset_spec(
        AssetKey(["semantic_model", "Sales_Returns_Sample_v201912"])
    )

    # Check that our custom metadata and tags are present
    assert asset_spec.metadata["custom_override"] == "test_value"
    assert asset_spec.tags["custom_tag"] == "override_test"

    # Verify that the asset keys are still correct
    assert defs.resolve_asset_graph().get_all_asset_keys() == {
        AssetKey(["semantic_model", "Sales_Returns_Sample_v201912"]),
        AssetKey(["dashboard", "Sales_Returns_Sample_v201912"]),
        AssetKey(["data_27_09_2019_xlsx"]),
        AssetKey(["sales_marketing_datas_xlsx"]),
        AssetKey(["report", "Sales_Returns_Sample_v201912"]),
    }
