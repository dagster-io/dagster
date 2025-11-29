"""Tests for Looker component."""

import asyncio
import copy
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Optional

import pytest
from dagster import AssetKey
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.testing import create_defs_folder_sandbox
from dagster.components.testing.test_cases import TestTranslation
from dagster_looker.api.components import LookerComponent
from unittest.mock import MagicMock
from dagster import resource, build_init_resource_context

BASIC_LOOKER_COMPONENT_BODY = {
    "type": "dagster_looker.LookerComponent",
    "attributes": {
        "looker_resource": {
            "base_url": "https://my-looker.cloud.looker.com",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
        },
    },
}


@contextmanager
def setup_looker_component(
    defs_yaml_contents: dict[str, Any],
) -> Iterator[tuple[LookerComponent, Definitions]]:
    """Sets up a components project with a looker component based on provided params."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=LookerComponent,
            defs_yaml_contents=defs_yaml_contents,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),

        ):
            merged_defs = Definitions.merge(
                defs, 
                Definitions(resources={"looker": mock_looker_resource})
            )
            assert isinstance(component, LookerComponent)
            yield component, merged_defs


@pytest.mark.parametrize(
    "defs_state_type",
    ["LOCAL_FILESYSTEM", "VERSIONED_STATE_STORAGE"],
)
def test_component_load_with_defs_state(
    looker_api_mocks,
    defs_state_type: str,
) -> None:
    """Test component loading with defs state."""
    body = copy.deepcopy(BASIC_LOOKER_COMPONENT_BODY)
    body["attributes"]["defs_state"] = {"management_type": defs_state_type}

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=LookerComponent,
            defs_yaml_contents=body,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            # First load, nothing there
            assert len(defs.resolve_asset_graph().get_all_asset_keys()) == 0
            assert isinstance(component, LookerComponent)
            asyncio.run(component.refresh_state(sandbox.project_root))

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            # Second load, should now have assets
            asset_keys = defs.resolve_asset_graph().get_all_asset_keys()
            assert AssetKey(["view", "my_view"]) in asset_keys
            assert AssetKey(["my_model::my_explore"]) in asset_keys
            assert AssetKey(["my_dashboard_1"]) in asset_keys


class TestLookerTranslation(TestTranslation):
    """Test translation of asset attributes for Looker components."""

    def test_translation(
        self,
        looker_api_mocks,
        attributes: Mapping[str, Any],
        assertion: Callable[[AssetSpec], bool],
        key_modifier: Optional[Callable[[AssetKey], AssetKey]],
    ) -> None:
        body = copy.deepcopy(BASIC_LOOKER_COMPONENT_BODY)
        body["attributes"]["translation"] = attributes
        body["attributes"]["defs_state"] = {"management_type": "LOCAL_FILESYSTEM"}

        with create_defs_folder_sandbox() as sandbox:
            defs_path = sandbox.scaffold_component(
                component_cls=LookerComponent,
                defs_yaml_contents=body,
            )
            # First load and populate state
            with (
                scoped_definitions_load_context(),
                sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
            ):
                assert isinstance(component, LookerComponent)
                asyncio.run(component.refresh_state(sandbox.project_root))

            # Second load with populated state
            with (
                scoped_definitions_load_context(),
                sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
            ):
                key = AssetKey(["my_model::my_explore"])
                if key_modifier:
                    key = key_modifier(key)

                assets_def = defs.resolve_assets_def(key)
                assert assertion(assets_def.get_asset_spec(key))

@resource
def mock_looker_resource(looker_api_mocks: Any):
    return MagicMock()
def test_pdt_assets_configuration(looker_api_mocks):
    """Test that PDT assets are created from YAML configuration."""
    
    body = copy.deepcopy(BASIC_LOOKER_COMPONENT_BODY)
    body["attributes"]["pdt_builds"] = [
        {
            "model_name": "my_model",
            "view_name": "my_pdt_view",
            "force_rebuild": "true"
        },
        {
            "model_name": "sales_model",
            "view_name": "monthly_report",
            "workspace": "dev"
        }
    ]

    with setup_looker_component(defs_yaml_contents=body) as (component, defs):
        all_keys = defs.resolve_asset_graph().get_all_asset_keys()
    
        assert AssetKey(["view", "my_pdt_view"]) in all_keys
        
        assert AssetKey(["view", "monthly_report"]) in all_keys

        assert component.resource_key == "looker" 
        assert len(component.pdt_builds) == 2
