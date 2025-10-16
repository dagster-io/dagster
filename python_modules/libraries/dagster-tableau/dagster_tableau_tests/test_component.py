"""Tests for Tableau component."""

import asyncio
import copy
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Callable, Optional

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
    workspace_data,
    defs_state_type: str,
) -> None:
    """Test component loading with defs state."""
    body = copy.deepcopy(BASIC_TABLEAU_COMPONENT_BODY)
    body["attributes"]["defs_state"] = {"type": defs_state_type}

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
            # Second load, should now have assets
            asset_keys = defs.resolve_asset_graph().get_all_asset_keys()
            # Check for sheets (with workbook name prefix)
            assert AssetKey(["test_workbook", "sheet", "sales"]) in asset_keys
            assert AssetKey(["test_workbook", "sheet", "account"]) in asset_keys
            # Check for dashboards (with workbook name prefix)
            assert AssetKey(["test_workbook", "dashboard", "dashboard_sales"]) in asset_keys
            # Check for data sources
            assert AssetKey(["superstore_datasource"]) in asset_keys


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
        body["attributes"]["defs_state"] = {"type": "LOCAL_FILESYSTEM"}

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
