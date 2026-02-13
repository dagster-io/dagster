"""Tests for Tableau component."""

import asyncio
import copy
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Optional

import pytest
from dagster import AssetKey
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.instance_for_test import instance_for_test
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.testing import create_defs_folder_sandbox
from dagster.components.testing.test_cases import TestTranslation
from dagster_tableau.components import TableauComponent

BASIC_TABLEAU_COMPONENT_BODY = {
    "type": "dagster_tableau.TableauComponent",
    "attributes": {
        "workspace": {
            "connected_app_client_id": "test_client_id",
            "connected_app_secret_id": "test_secret_id",
            "connected_app_secret_value": "test_secret_value",
            "username": "test_username",
            "site_name": "test_site",
            "pod_name": "10ax",
        },
        "enable_embedded_datasource_refresh": True,
        "enable_published_datasource_refresh": True,
    },
}


@contextmanager
def setup_tableau_component(
    defs_yaml_contents: dict[str, Any],
) -> Iterator[tuple[TableauComponent, Definitions]]:
    """Sets up a components project with a tableau component based on provided params."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=TableauComponent,
            defs_yaml_contents=defs_yaml_contents,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, TableauComponent)
            yield component, defs


@pytest.mark.parametrize(
    "defs_state_type",
    ["LOCAL_FILESYSTEM", "VERSIONED_STATE_STORAGE"],
)
def test_component_load_with_defs_state(
    workspace_data_two_workbooks,
    get_workbooks_two_workbooks,
    defs_state_type: str,
) -> None:
    """Test component loading with defs state."""
    body = copy.deepcopy(BASIC_TABLEAU_COMPONENT_BODY)
    body["attributes"]["defs_state"] = {"management_type": defs_state_type}

    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
    ):
        defs_path = sandbox.scaffold_component(
            component_cls=TableauComponent,
            defs_yaml_contents=body,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            # First load, nothing there
            assert len(defs.resolve_asset_graph().get_all_asset_keys()) == 0
            assert isinstance(component, TableauComponent)
            asyncio.run(component.refresh_state(sandbox.project_root))

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            # Second load, should now have assets from both workbooks
            asset_keys = defs.resolve_asset_graph().get_all_asset_keys()
            # Check for sheets from first workbook (with workbook name prefix)
            assert AssetKey(["test_workbook", "sheet", "sales"]) in asset_keys
            assert AssetKey(["test_workbook", "sheet", "account"]) in asset_keys
            assert AssetKey(["test_workbook", "sheet", "hidden"]) in asset_keys
            # Check for dashboards from first workbook
            assert AssetKey(["test_workbook", "dashboard", "dashboard_sales"]) in asset_keys
            # Check for sheets from second workbook
            assert AssetKey(["second_workbook", "sheet", "revenue"]) in asset_keys
            assert AssetKey(["second_workbook", "sheet", "profit"]) in asset_keys
            # Check for dashboards from second workbook
            assert AssetKey(["second_workbook", "dashboard", "dashboard_revenue"]) in asset_keys
            # Check for published data sources (not workbook-specific)
            assert AssetKey(["superstore_datasource"]) in asset_keys
            assert AssetKey(["hidden_sheet_datasource"]) in asset_keys
            # Check for embedded data sources from both workbooks
            assert (
                AssetKey(["test_workbook", "embedded_datasource", "embedded_superstore_datasource"])
                in asset_keys
            )
            assert (
                AssetKey(["second_workbook", "embedded_datasource", "embedded_sales_datasource"])
                in asset_keys
            )


class TestTableauTranslation(TestTranslation):
    """Test translation of asset attributes for Tableau components."""

    def test_translation(
        self,
        workspace_data,
        attributes: Mapping[str, Any],
        assertion: Callable[[AssetSpec], bool],
        key_modifier: Optional[Callable[[AssetKey], AssetKey]],
    ) -> None:
        body = copy.deepcopy(BASIC_TABLEAU_COMPONENT_BODY)
        body["attributes"]["translation"] = attributes
        body["attributes"]["defs_state"] = {"management_type": "LOCAL_FILESYSTEM"}

        with (
            instance_for_test(),
            create_defs_folder_sandbox() as sandbox,
        ):
            defs_path = sandbox.scaffold_component(
                component_cls=TableauComponent,
                defs_yaml_contents=body,
            )
            # First load and populate state
            with (
                scoped_definitions_load_context(),
                sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
            ):
                assert isinstance(component, TableauComponent)
                asyncio.run(component.refresh_state(sandbox.project_root))

            # Second load with populated state
            with (
                scoped_definitions_load_context(),
                sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
            ):
                # Use a sheet asset for testing (with workbook name prefix)
                key = AssetKey(["test_workbook", "sheet", "sales"])
                if key_modifier:
                    key = key_modifier(key)

                assets_def = defs.resolve_assets_def(key)
                assert assertion(assets_def.get_asset_spec(key))


def test_component_workbook_selector_by_id(
    workspace_data_two_workbooks, get_workbooks_two_workbooks
) -> None:
    """Test component with workbook selector filtering by ID."""
    body = copy.deepcopy(BASIC_TABLEAU_COMPONENT_BODY)
    body["attributes"]["defs_state"] = {"management_type": "LOCAL_FILESYSTEM"}
    # Add workbook selector to filter to only TEST_WORKBOOK_ID
    body["attributes"]["workbook_selector"] = {
        "by_id": ["b75fc023-a7ca-4115-857b-4342028640d0"]  # TEST_WORKBOOK_ID
    }

    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
    ):
        defs_path = sandbox.scaffold_component(
            component_cls=TableauComponent,
            defs_yaml_contents=body,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            # First load, nothing there
            assert len(defs.resolve_asset_graph().get_all_asset_keys()) == 0
            assert isinstance(component, TableauComponent)
            asyncio.run(component.refresh_state(sandbox.project_root))

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            # Second load, should have assets from the filtered workbook
            asset_keys = defs.resolve_asset_graph().get_all_asset_keys()

            # Assets from workbook with TEST_WORKBOOK_ID SHOULD be present
            # Check for sheets from workbook with TEST_WORKBOOK_ID
            assert AssetKey(["test_workbook", "sheet", "sales"]) in asset_keys
            assert AssetKey(["test_workbook", "sheet", "account"]) in asset_keys
            # Hidden sheets from selected workbook SHOULD be present
            assert AssetKey(["test_workbook", "sheet", "hidden"]) in asset_keys
            # Check for dashboards from workbook with TEST_WORKBOOK_ID
            assert AssetKey(["test_workbook", "dashboard", "dashboard_sales"]) in asset_keys
            # Embedded datasources from selected workbook SHOULD be present
            assert (
                AssetKey(["test_workbook", "embedded_datasource", "embedded_superstore_datasource"])
                in asset_keys
            )

            # Published data sources (not workbook-specific) SHOULD be present
            assert AssetKey(["superstore_datasource"]) in asset_keys
            assert AssetKey(["hidden_sheet_datasource"]) in asset_keys

            # Assets from workbook with TEST_SECOND_WORKBOOK_ID should NOT be present
            assert AssetKey(["second_workbook", "sheet", "revenue"]) not in asset_keys
            assert AssetKey(["second_workbook", "sheet", "profit"]) not in asset_keys
            assert AssetKey(["second_workbook", "dashboard", "dashboard_revenue"]) not in asset_keys
            assert (
                AssetKey(["second_workbook", "embedded_datasource", "embedded_sales_datasource"])
                not in asset_keys
            )

            # Check total number of assets
            assert len(asset_keys) == 7


def test_component_workbook_selector_with_multiple_ids(
    workspace_data_two_workbooks, get_workbooks_two_workbooks
) -> None:
    """Test that workbook selector works with multiple IDs and filters correctly."""
    body = copy.deepcopy(BASIC_TABLEAU_COMPONENT_BODY)
    body["attributes"]["defs_state"] = {"management_type": "LOCAL_FILESYSTEM"}
    # Add workbook selector with multiple IDs (only one will match our test data)
    body["attributes"]["workbook_selector"] = {
        "by_id": ["b75fc023-a7ca-4115-857b-4342028640d0", "non-existent-id"]
    }

    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
    ):
        defs_path = sandbox.scaffold_component(
            component_cls=TableauComponent,
            defs_yaml_contents=body,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, TableauComponent)
            asyncio.run(component.refresh_state(sandbox.project_root))

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            # Should have assets from workbook with TEST_WORKBOOK_ID
            asset_keys = defs.resolve_asset_graph().get_all_asset_keys()

            # Assets from workbook with TEST_WORKBOOK_ID SHOULD be present
            assert AssetKey(["test_workbook", "sheet", "sales"]) in asset_keys
            assert AssetKey(["test_workbook", "sheet", "account"]) in asset_keys
            # Hidden sheets from selected workbook SHOULD be present
            assert AssetKey(["test_workbook", "sheet", "hidden"]) in asset_keys
            # Check for dashboards from workbook with TEST_WORKBOOK_ID
            assert AssetKey(["test_workbook", "dashboard", "dashboard_sales"]) in asset_keys
            # Embedded datasources from selected workbook SHOULD be present
            assert (
                AssetKey(["test_workbook", "embedded_datasource", "embedded_superstore_datasource"])
                in asset_keys
            )

            # Published data sources (not workbook-specific) SHOULD be present
            assert AssetKey(["superstore_datasource"]) in asset_keys
            assert AssetKey(["hidden_sheet_datasource"]) in asset_keys

            # Assets from workbook with TEST_SECOND_WORKBOOK_ID should NOT be present
            assert AssetKey(["second_workbook", "sheet", "revenue"]) not in asset_keys
            assert AssetKey(["second_workbook", "sheet", "profit"]) not in asset_keys
            assert AssetKey(["second_workbook", "dashboard", "dashboard_revenue"]) not in asset_keys
            assert (
                AssetKey(["second_workbook", "embedded_datasource", "embedded_sales_datasource"])
                not in asset_keys
            )

            # Check total number of assets
            assert len(asset_keys) == 7


def test_component_workbook_selector_by_project_id(
    workspace_data_two_workbooks, get_workbooks_two_workbooks
) -> None:
    """Test component with workbook selector filtering by project ID."""
    body = copy.deepcopy(BASIC_TABLEAU_COMPONENT_BODY)
    body["attributes"]["defs_state"] = {"management_type": "LOCAL_FILESYSTEM"}
    # Add workbook selector to filter by project ID
    body["attributes"]["workbook_selector"] = {
        "by_project_id": ["test_project_id"]  # TEST_PROJECT_ID from conftest
    }

    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
    ):
        defs_path = sandbox.scaffold_component(
            component_cls=TableauComponent,
            defs_yaml_contents=body,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            # First load, nothing there
            assert len(defs.resolve_asset_graph().get_all_asset_keys()) == 0
            assert isinstance(component, TableauComponent)
            asyncio.run(component.refresh_state(sandbox.project_root))

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            # Second load, should have assets from workbooks in the selected project
            asset_keys = defs.resolve_asset_graph().get_all_asset_keys()

            # Assets from workbook with TEST_WORKBOOK_ID (project TEST_PROJECT_ID) SHOULD be present
            # Check for sheets from workbook with TEST_WORKBOOK_ID
            assert AssetKey(["test_workbook", "sheet", "sales"]) in asset_keys
            assert AssetKey(["test_workbook", "sheet", "account"]) in asset_keys
            # Hidden sheets from selected workbook SHOULD be present
            assert AssetKey(["test_workbook", "sheet", "hidden"]) in asset_keys
            # Check for dashboards from workbook with TEST_WORKBOOK_ID
            assert AssetKey(["test_workbook", "dashboard", "dashboard_sales"]) in asset_keys
            # Embedded datasources from selected workbook SHOULD be present
            assert (
                AssetKey(["test_workbook", "embedded_datasource", "embedded_superstore_datasource"])
                in asset_keys
            )

            # Published data sources (not workbook-specific) SHOULD be present
            assert AssetKey(["superstore_datasource"]) in asset_keys
            assert AssetKey(["hidden_sheet_datasource"]) in asset_keys

            # Assets from workbook with TEST_SECOND_WORKBOOK_ID (project TEST_SECOND_PROJECT_ID) should NOT be present
            assert AssetKey(["second_workbook", "sheet", "revenue"]) not in asset_keys
            assert AssetKey(["second_workbook", "sheet", "profit"]) not in asset_keys
            assert AssetKey(["second_workbook", "dashboard", "dashboard_revenue"]) not in asset_keys
            assert (
                AssetKey(["second_workbook", "embedded_datasource", "embedded_sales_datasource"])
                not in asset_keys
            )

            # Check total number of assets
            assert len(asset_keys) == 7


def test_component_workbook_selector_by_project_id_with_multiple_ids(
    workspace_data_two_workbooks, get_workbooks_two_workbooks
) -> None:
    """Test that workbook selector works with multiple project IDs and filters correctly."""
    body = copy.deepcopy(BASIC_TABLEAU_COMPONENT_BODY)
    body["attributes"]["defs_state"] = {"management_type": "LOCAL_FILESYSTEM"}
    # Add workbook selector with multiple project IDs (only one will match our test data)
    body["attributes"]["workbook_selector"] = {
        "by_project_id": ["test_project_id", "non-existent-project-id"]
    }

    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
    ):
        defs_path = sandbox.scaffold_component(
            component_cls=TableauComponent,
            defs_yaml_contents=body,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, TableauComponent)
            asyncio.run(component.refresh_state(sandbox.project_root))

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            # Should have assets from workbooks in the matched project (has workbook with TEST_WORKBOOK_ID)
            asset_keys = defs.resolve_asset_graph().get_all_asset_keys()

            # Assets from workbook with TEST_WORKBOOK_ID (project TEST_PROJECT_ID) SHOULD be present
            assert AssetKey(["test_workbook", "sheet", "sales"]) in asset_keys
            assert AssetKey(["test_workbook", "sheet", "account"]) in asset_keys
            # Hidden sheets from selected workbook SHOULD be present
            assert AssetKey(["test_workbook", "sheet", "hidden"]) in asset_keys
            # Check for dashboards from workbook with TEST_WORKBOOK_ID
            assert AssetKey(["test_workbook", "dashboard", "dashboard_sales"]) in asset_keys
            # Embedded datasources from selected workbook SHOULD be present
            assert (
                AssetKey(["test_workbook", "embedded_datasource", "embedded_superstore_datasource"])
                in asset_keys
            )

            # Published data sources (not workbook-specific) SHOULD be present
            assert AssetKey(["superstore_datasource"]) in asset_keys
            assert AssetKey(["hidden_sheet_datasource"]) in asset_keys

            # Assets from workbook with TEST_SECOND_WORKBOOK_ID (project TEST_SECOND_PROJECT_ID) should NOT be present
            assert AssetKey(["second_workbook", "sheet", "revenue"]) not in asset_keys
            assert AssetKey(["second_workbook", "sheet", "profit"]) not in asset_keys
            assert AssetKey(["second_workbook", "dashboard", "dashboard_revenue"]) not in asset_keys
            assert (
                AssetKey(["second_workbook", "embedded_datasource", "embedded_sales_datasource"])
                not in asset_keys
            )

            # Check total number of assets
            assert len(asset_keys) == 7


def test_component_workbook_selector_by_project_id_no_match(
    workspace_data_two_workbooks, get_workbooks_two_workbooks
) -> None:
    """Test that workbook selector with non-matching project ID returns only standalone data sources."""
    body = copy.deepcopy(BASIC_TABLEAU_COMPONENT_BODY)
    body["attributes"]["defs_state"] = {"management_type": "LOCAL_FILESYSTEM"}
    # Add workbook selector with project ID that doesn't match any workbooks
    body["attributes"]["workbook_selector"] = {"by_project_id": ["non-existent-project-id"]}

    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
    ):
        defs_path = sandbox.scaffold_component(
            component_cls=TableauComponent,
            defs_yaml_contents=body,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, TableauComponent)
            asyncio.run(component.refresh_state(sandbox.project_root))

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            # Should have only standalone published data sources (no workbook-related assets)
            asset_keys = defs.resolve_asset_graph().get_all_asset_keys()

            # Published data sources (not workbook-specific) SHOULD be present
            assert AssetKey(["superstore_datasource"]) in asset_keys
            assert AssetKey(["hidden_sheet_datasource"]) in asset_keys

            # ALL workbook-related assets should NOT be present (from both workbooks)
            # First workbook assets should NOT be present
            assert AssetKey(["test_workbook", "sheet", "sales"]) not in asset_keys
            assert AssetKey(["test_workbook", "sheet", "account"]) not in asset_keys
            assert AssetKey(["test_workbook", "sheet", "hidden"]) not in asset_keys
            assert AssetKey(["test_workbook", "dashboard", "dashboard_sales"]) not in asset_keys
            assert (
                AssetKey(["test_workbook", "embedded_datasource", "embedded_superstore_datasource"])
                not in asset_keys
            )

            # Second workbook assets should NOT be present
            assert AssetKey(["second_workbook", "sheet", "revenue"]) not in asset_keys
            assert AssetKey(["second_workbook", "sheet", "profit"]) not in asset_keys
            assert AssetKey(["second_workbook", "dashboard", "dashboard_revenue"]) not in asset_keys
            assert (
                AssetKey(["second_workbook", "embedded_datasource", "embedded_sales_datasource"])
                not in asset_keys
            )

            # Check total number of assets - only 2 published datasources
            assert len(asset_keys) == 2
