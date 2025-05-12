# ruff: noqa: F841 TID252

# ruff: noqa: F841 TID252
import importlib
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Any, Callable, Optional

import pytest
import yaml
from dagster import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster._utils import alter_sys_path
from dagster.components import ComponentLoadContext
from dagster.components.core.context import use_component_load_context
from dagster_dg.utils import ensure_dagster_dg_tests_import
from dagster_powerbi import PowerBIWorkspaceComponent

ensure_dagster_tests_import()
from dagster_tests.components_tests.utils import get_underlying_component

ensure_dagster_tests_import()
ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import ProxyRunner, isolated_example_project_foo_bar


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
    component_body: dict[str, Any],
) -> Iterator[tuple[PowerBIWorkspaceComponent, Definitions]]:
    """Sets up a components project with a powerbi component based on provided params."""
    with setup_powerbi_ready_project():
        defs_path = Path.cwd() / "src" / "foo_bar" / "defs"
        component_path = defs_path / "ingest"
        component_path.mkdir(parents=True, exist_ok=True)

        (component_path / "component.yaml").write_text(yaml.safe_dump(component_body))

        defs_root = importlib.import_module("foo_bar.defs.ingest")
        project_root = Path.cwd()

        context = ComponentLoadContext.for_module(defs_root, project_root)
        with use_component_load_context(context):
            component = get_underlying_component(context)
            assert isinstance(component, PowerBIWorkspaceComponent)
            yield component, component.build_defs(context)


def test_basic_component_load(workspace_data_api_mocks, workspace_id: str) -> None:
    with (
        setup_powerbi_component(
            component_body={
                "type": "dagster_powerbi.PowerBIWorkspaceComponent",
                "attributes": {
                    "credentials": {
                        "token": uuid.uuid4().hex,
                    },
                    "workspace_id": workspace_id,
                    "use_workspace_scan": False,
                },
            }
        ) as (
            component,
            defs,
        ),
    ):
        assert defs.get_asset_graph().get_all_asset_keys() == {
            AssetKey(["semantic_model", "Sales_Returns_Sample_v201912"]),
            AssetKey(["dashboard", "Sales_Returns_Sample_v201912"]),
            AssetKey(["data_27_09_2019_xlsx"]),
            AssetKey(["sales_marketing_datas_xlsx"]),
            AssetKey(["report", "Sales_Returns_Sample_v201912"]),
        }


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
                "credentials": {
                    "token": uuid.uuid4().hex,
                },
                "workspace_id": workspace_id,
                "use_workspace_scan": False,
            },
        }
        body["attributes"]["translation"] = attributes
        with (
            setup_powerbi_component(
                component_body=body,
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
        "type": "dagster_powerbi.PowerBiWorkspaceComponent",
        "attributes": {
            "credentials": {
                "token": uuid.uuid4().hex,
            },
            "workspace_id": workspace_id,
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
            },
        },
    }
    with (
        setup_powerbi_component(
            component_body=body,
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
