# ruff: noqa: F841 TID252

import copy
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Optional

import pytest
import responses
from dagster import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster._utils import alter_sys_path
from dagster._utils.env import environ
from dagster.components.core.tree import ComponentTree
from dagster.components.testing import TestTranslation, scaffold_defs_sandbox
from dagster_airbyte.components.workspace_component.component import AirbyteCloudWorkspaceComponent
from dagster_airbyte.resources import AirbyteCloudWorkspace
from dagster_airbyte.translator import AirbyteConnection
from dagster_dg_core.utils import ensure_dagster_dg_tests_import
from dagster_shared.merger import deep_merge_dicts

from dagster_airbyte_tests.beta.conftest import (
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    TEST_CONNECTION_ID,
    TEST_WORKSPACE_ID,
)

ensure_dagster_tests_import()

ensure_dagster_dg_tests_import()

from dagster_dg_core_tests.utils import ProxyRunner, isolated_example_project_foo_bar


@contextmanager
def setup_airbyte_ready_project() -> Iterator[None]:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
        alter_sys_path(to_add=[str(Path.cwd() / "src")], to_remove=[]),
    ):
        yield


@contextmanager
def setup_airbyte_component(
    component_body: dict[str, Any],
) -> Iterator[tuple[AirbyteCloudWorkspaceComponent, Definitions]]:
    """Sets up a components project with an airbyte component based on provided params."""
    with scaffold_defs_sandbox(component_cls=AirbyteCloudWorkspaceComponent) as defs_sandbox:
        with defs_sandbox.load(component_body=component_body) as (component, defs):
            assert isinstance(component, AirbyteCloudWorkspaceComponent)
            yield component, defs


BASIC_AIRBYTE_COMPONENT_BODY = {
    "type": "dagster_airbyte.AirbyteCloudWorkspaceComponent",
    "attributes": {
        "workspace": {
            "client_id": "{{ env.AIRBYTE_CLIENT_ID }}",
            "client_secret": "{{ env.AIRBYTE_CLIENT_SECRET }}",
            "workspace_id": "{{ env.AIRBYTE_WORKSPACE_ID }}",
        },
    },
}


def test_basic_component_load(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with (
        environ(
            {
                "AIRBYTE_CLIENT_ID": TEST_CLIENT_ID,
                "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET,
                "AIRBYTE_WORKSPACE_ID": TEST_WORKSPACE_ID,
            }
        ),
        setup_airbyte_component(
            component_body=BASIC_AIRBYTE_COMPONENT_BODY,
        ) as (
            component,
            defs,
        ),
    ):
        assert defs.resolve_asset_graph().get_all_asset_keys() == {
            AssetKey(["test_prefix_test_stream"]),
            AssetKey(["test_prefix_test_another_stream"]),
        }


@pytest.mark.parametrize(
    "connection_selector, num_assets",
    [
        ({"by_name": ["Postgres To Snowflake"]}, 2),
        ({"by_id": [TEST_CONNECTION_ID]}, 2),
        ({"by_id": []}, 0),
        ({"by_name": ["Postgres To Snowflake", "junk"]}, 2),
    ],
    ids=[
        "single_connection",
        "single_connection_by_id",
        "no_connections",
        "junk_connection",
    ],
)
def test_basic_component_filter(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    connection_selector: dict[str, Any],
    num_assets: int,
) -> None:
    with (
        environ(
            {
                "AIRBYTE_CLIENT_ID": TEST_CLIENT_ID,
                "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET,
                "AIRBYTE_WORKSPACE_ID": TEST_WORKSPACE_ID,
            }
        ),
        setup_airbyte_component(
            component_body=deep_merge_dicts(
                BASIC_AIRBYTE_COMPONENT_BODY,
                {"attributes": {"connection_selector": connection_selector}},
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
        (lambda _: True, 2),
        (lambda connection: connection.id == TEST_CONNECTION_ID, 2),
        (lambda _: False, 0),
    ],
    ids=[
        "all_connections",
        "filter_by_id",
        "no_connections",
    ],
)
def test_custom_filter_fn_python(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    filter_fn: Callable[[AirbyteConnection], bool],
    num_assets: int,
) -> None:
    defs = AirbyteCloudWorkspaceComponent(
        workspace=AirbyteCloudWorkspace(
            client_id=TEST_CLIENT_ID,
            client_secret=TEST_CLIENT_SECRET,
            workspace_id=TEST_WORKSPACE_ID,
        ),
        connection_selector=filter_fn,
        translation=None,
    ).build_defs(ComponentTree.for_test().load_context)
    assert len(defs.resolve_asset_graph().get_all_asset_keys()) == num_assets


class TestAirbyteTranslation(TestTranslation):
    def test_translation(
        self,
        fetch_workspace_data_api_mocks,
        attributes: Mapping[str, Any],
        assertion: Callable[[AssetSpec], bool],
        key_modifier: Optional[Callable[[AssetKey], AssetKey]],
    ) -> None:
        body = copy.deepcopy(BASIC_AIRBYTE_COMPONENT_BODY)
        body["attributes"]["translation"] = attributes
        with (
            environ(
                {
                    "AIRBYTE_CLIENT_ID": TEST_CLIENT_ID,
                    "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET,
                    "AIRBYTE_WORKSPACE_ID": TEST_WORKSPACE_ID,
                }
            ),
            setup_airbyte_component(
                component_body=body,
            ) as (
                component,
                defs,
            ),
        ):
            key = AssetKey(["test_prefix_test_stream"])
            if key_modifier:
                key = key_modifier(key)

            assets_def = defs.get_assets_def(key)
            assert assertion(assets_def.get_asset_spec(key))
