# ruff: noqa: F841 TID252

import copy
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Callable, Optional

import pytest
import responses
import yaml
from dagster import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.env import environ
from dagster.components.core.tree import ComponentTree
from dagster.components.testing import TestTranslation, scaffold_defs_sandbox
from dagster_fivetran.components.workspace_component.component import FivetranAccountComponent
from dagster_fivetran.resources import FivetranWorkspace
from dagster_fivetran.translator import FivetranConnector
from dagster_shared.merger import deep_merge_dicts

from dagster_fivetran_tests.conftest import (
    EXTRA_TEST_CONNECTOR_ID,
    EXTRA_TEST_CONNECTOR_NAME,
    TEST_ACCOUNT_ID,
    TEST_API_KEY,
    TEST_API_SECRET,
    TEST_CONNECTOR_ID,
    TEST_CONNECTOR_NAME,
    TEST_GROUP_ID,
)


@contextmanager
def setup_fivetran_component(
    component_body: dict[str, Any],
) -> Iterator[tuple[FivetranAccountComponent, Definitions]]:
    """Sets up a components project with a fivetran component based on provided params."""
    with scaffold_defs_sandbox(
        component_cls=FivetranAccountComponent,
    ) as defs_sandbox:
        with defs_sandbox.load(component_body=component_body) as (component, defs):
            assert isinstance(component, FivetranAccountComponent)
            yield component, defs


BASIC_FIVETRAN_COMPONENT_BODY = {
    "type": "dagster_fivetran.FivetranAccountComponent",
    "attributes": {
        "workspace": {
            "api_key": "{{ env.FIVETRAN_API_KEY }}",
            "api_secret": "{{ env.FIVETRAN_API_SECRET }}",
            "account_id": "{{ env.FIVETRAN_ACCOUNT_ID }}",
        },
    },
}


def test_basic_component_load(
    fetch_workspace_data_multiple_connectors_mocks: responses.RequestsMock,
) -> None:
    with (
        environ(
            {
                "FIVETRAN_API_KEY": TEST_API_KEY,
                "FIVETRAN_API_SECRET": TEST_API_SECRET,
                "FIVETRAN_ACCOUNT_ID": TEST_ACCOUNT_ID,
            }
        ),
        setup_fivetran_component(
            component_body=BASIC_FIVETRAN_COMPONENT_BODY,
        ) as (
            component,
            defs,
        ),
    ):
        assert defs.resolve_asset_graph().get_all_asset_keys() == {
            AssetKey(["schema_name_in_destination_1", "table_name_in_destination_1"]),
            AssetKey(["schema_name_in_destination_1", "table_name_in_destination_2"]),
            AssetKey(["schema_name_in_destination_2", "table_name_in_destination_1"]),
            AssetKey(["schema_name_in_destination_2", "table_name_in_destination_2"]),
            AssetKey(["schema_name_in_destination_1", "table_name_in_destination_1_extra"]),
            AssetKey(["schema_name_in_destination_1", "table_name_in_destination_2_extra"]),
            AssetKey(["schema_name_in_destination_2", "table_name_in_destination_1_extra"]),
            AssetKey(["schema_name_in_destination_2", "table_name_in_destination_2_extra"]),
        }


@pytest.mark.parametrize(
    "connector_selector, num_assets",
    [
        ({"by_name": [TEST_CONNECTOR_NAME]}, 4),
        ({"by_name": [EXTRA_TEST_CONNECTOR_NAME]}, 4),
        ({"by_name": [TEST_CONNECTOR_NAME, EXTRA_TEST_CONNECTOR_NAME]}, 8),
        ({"by_id": [TEST_CONNECTOR_ID]}, 4),
        ({"by_id": [EXTRA_TEST_CONNECTOR_ID]}, 4),
        ({"by_id": [TEST_CONNECTOR_ID, EXTRA_TEST_CONNECTOR_ID]}, 8),
        ({"by_id": []}, 0),
        ({"by_name": [TEST_CONNECTOR_NAME, "junk"]}, 4),
    ],
    ids=[
        "single_connector",
        "single_connector_extra",
        "multiple_connectors",
        "single_connector_by_id",
        "single_connector_extra_by_id",
        "multiple_connectors_by_id",
        "no_connectors",
        "junk_connector",
    ],
)
def test_basic_component_filter(
    fetch_workspace_data_multiple_connectors_mocks: responses.RequestsMock,
    connector_selector: dict[str, Any],
    num_assets: int,
) -> None:
    with (
        environ(
            {
                "FIVETRAN_API_KEY": TEST_API_KEY,
                "FIVETRAN_API_SECRET": TEST_API_SECRET,
                "FIVETRAN_ACCOUNT_ID": TEST_ACCOUNT_ID,
            }
        ),
        setup_fivetran_component(
            component_body=deep_merge_dicts(
                BASIC_FIVETRAN_COMPONENT_BODY,
                {"attributes": {"connector_selector": connector_selector}},
            ),
        ) as (
            component,
            defs,
        ),
    ):
        assert len(defs.resolve_asset_graph().get_all_asset_keys()) == num_assets


@pytest.mark.parametrize(
    "filter_fn, num_assets",
    [
        (lambda _: True, 8),
        (lambda connector: connector.id == EXTRA_TEST_CONNECTOR_ID, 4),
        (lambda connector: connector.group_id == TEST_GROUP_ID, 8),
        (lambda _: False, 0),
    ],
    ids=[
        "all_connectors",
        "filter_by_id",
        "filter_by_group_id",
        "no_connectors",
    ],
)
def test_custom_filter_fn_python(
    fetch_workspace_data_multiple_connectors_mocks: responses.RequestsMock,
    filter_fn: Callable[[FivetranConnector], bool],
    num_assets: int,
) -> None:
    defs = FivetranAccountComponent(
        workspace=FivetranWorkspace(
            api_key=TEST_API_KEY,
            api_secret=TEST_API_SECRET,
            account_id=TEST_ACCOUNT_ID,
        ),
        connector_selector=filter_fn,
        translation=None,
    ).build_defs(ComponentTree.for_test().load_context)
    assert len(defs.resolve_asset_graph().get_all_asset_keys()) == num_assets


class TestFivetranTranslation(TestTranslation):
    def test_translation(
        self,
        fetch_workspace_data_multiple_connectors_mocks,
        attributes: Mapping[str, Any],
        assertion: Callable[[AssetSpec], bool],
        key_modifier: Optional[Callable[[AssetKey], AssetKey]],
    ) -> None:
        body = copy.deepcopy(BASIC_FIVETRAN_COMPONENT_BODY)
        body["attributes"]["translation"] = attributes
        with (
            environ(
                {
                    "FIVETRAN_API_KEY": TEST_API_KEY,
                    "FIVETRAN_API_SECRET": TEST_API_SECRET,
                    "FIVETRAN_ACCOUNT_ID": TEST_ACCOUNT_ID,
                }
            ),
            setup_fivetran_component(
                component_body=body,
            ) as (
                component,
                defs,
            ),
        ):
            key = AssetKey(["schema_name_in_destination_1", "table_name_in_destination_1"])
            if key_modifier:
                key = key_modifier(key)

            assets_def = defs.resolve_assets_def(key)
            assert assertion(assets_def.get_asset_spec(key))


@pytest.mark.parametrize(
    "scaffold_params",
    [
        {},
        {"account_id": "test_account", "api_key": "test_key", "api_secret": "test_secret"},
        {"account_id": "test_account"},
        {"api_key": "test_key", "api_secret": "test_secret"},
    ],
    ids=["no_params", "all_params", "just_account_id", "just_credentials"],
)
def test_scaffold_component_with_params(scaffold_params: dict):
    with scaffold_defs_sandbox(
        component_cls=FivetranAccountComponent,
        scaffold_params=scaffold_params,
    ) as instance_folder:
        defs_yaml_path = instance_folder.defs_folder_path / "defs.yaml"
        assert defs_yaml_path.exists()
        assert {
            k: v
            for k, v in yaml.safe_load(defs_yaml_path.read_text())["attributes"][
                "workspace"
            ].items()
            if v is not None
        } == scaffold_params
