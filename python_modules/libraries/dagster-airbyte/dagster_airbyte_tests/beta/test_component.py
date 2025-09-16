import copy
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Optional, Union

import pytest
import responses
from dagster import AssetKey
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster._utils import alter_sys_path
from dagster._utils.env import environ
from dagster.components.core.component_tree import ComponentTree
from dagster.components.testing.test_cases import TestTranslation
from dagster.components.testing.utils import create_defs_folder_sandbox
from dagster_airbyte import AirbyteCloudWorkspace, AirbyteWorkspace
from dagster_airbyte.components.workspace_component.component import (
    AirbyteCloudWorkspaceComponent,
    AirbyteWorkspaceComponent,
)
from dagster_airbyte.resources import AIRBYTE_CLOUD_REST_API_BASE_URL, BaseAirbyteWorkspace
from dagster_airbyte.translator import AirbyteConnection
from dagster_shared.merger import deep_merge_dicts

ensure_dagster_tests_import()
from dagster_test.dg_utils.utils import ProxyRunner, isolated_example_project_foo_bar

from dagster_airbyte_tests.beta.conftest import (
    TEST_AIRBYTE_OSS_REST_API_BASE_URL,
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    TEST_CONNECTION_ID,
    TEST_PASSWORD,
    TEST_USERNAME,
    TEST_WORKSPACE_ID,
)


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
    defs_yaml_contents: dict[str, Any],
) -> Iterator[tuple[AirbyteWorkspaceComponent, Definitions]]:
    """Sets up a components project with an airbyte component based on provided params."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=AirbyteWorkspaceComponent, defs_yaml_contents=defs_yaml_contents
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, AirbyteWorkspaceComponent)
            yield component, defs


OAUTH_AIRBYTE_CLOUD_COMPONENT_BODY_LEGACY_COMPONENT = {
    "type": "dagster_airbyte.AirbyteCloudWorkspaceComponent",
    "attributes": {
        "workspace": {
            "client_id": "{{ env.AIRBYTE_CLIENT_ID }}",
            "client_secret": "{{ env.AIRBYTE_CLIENT_SECRET }}",
            "workspace_id": "{{ env.AIRBYTE_WORKSPACE_ID }}",
        },
    },
}
OAUTH_AIRBYTE_CLOUD_COMPONENT_BODY = {
    "type": "dagster_airbyte.AirbyteWorkspaceComponent",
    "attributes": {
        "workspace": {
            "client_id": "{{ env.AIRBYTE_CLIENT_ID }}",
            "client_secret": "{{ env.AIRBYTE_CLIENT_SECRET }}",
            "workspace_id": "{{ env.AIRBYTE_WORKSPACE_ID }}",
        },
    },
}
OAUTH_AIRBYTE_OSS_COMPONENT_BODY = {
    "type": "dagster_airbyte.AirbyteWorkspaceComponent",
    "attributes": {
        "workspace": {
            "rest_api_base_url": "{{ env.AIRBYTE_REST_API_BASE_URL }}",
            "configuration_api_base_url": "{{ env.AIRBYTE_CONFIGURATION_API_BASE_URL }}",
            "client_id": "{{ env.AIRBYTE_CLIENT_ID }}",
            "client_secret": "{{ env.AIRBYTE_CLIENT_SECRET }}",
            "workspace_id": "{{ env.AIRBYTE_WORKSPACE_ID }}",
        },
    },
}
BASIC_AIRBYTE_OSS_COMPONENT_BODY = {
    "type": "dagster_airbyte.AirbyteWorkspaceComponent",
    "attributes": {
        "workspace": {
            "rest_api_base_url": "{{ env.AIRBYTE_REST_API_BASE_URL }}",
            "configuration_api_base_url": "{{ env.AIRBYTE_CONFIGURATION_API_BASE_URL }}",
            "username": "{{ env.AIRBYTE_USERNAME }}",
            "password": "{{ env.AIRBYTE_PASSWORD }}",
            "workspace_id": "{{ env.AIRBYTE_WORKSPACE_ID }}",
        },
    },
}
NO_AUTH_AIRBYTE_OSS_COMPONENT_BODY = {
    "type": "dagster_airbyte.AirbyteWorkspaceComponent",
    "attributes": {
        "workspace": {
            "rest_api_base_url": "{{ env.AIRBYTE_REST_API_BASE_URL }}",
            "configuration_api_base_url": "{{ env.AIRBYTE_CONFIGURATION_API_BASE_URL }}",
            "workspace_id": "{{ env.AIRBYTE_WORKSPACE_ID }}",
        },
    },
}


def should_test_combinations(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    rest_api_url: str,
    expected_workspace_type: type[BaseAirbyteWorkspace],
) -> None:
    """Skip test if the api mocks fixture is for Cloud but the Workspace is OSS, and vice versa."""
    if (
        expected_workspace_type == AirbyteCloudWorkspace
        and rest_api_url != AIRBYTE_CLOUD_REST_API_BASE_URL
    ):
        fetch_workspace_data_api_mocks.assert_all_requests_are_fired = False
        pytest.skip("Only run Airbyte Cloud tests against Airbyte Cloud API URL")
    if (
        expected_workspace_type == AirbyteWorkspace
        and rest_api_url != TEST_AIRBYTE_OSS_REST_API_BASE_URL
    ):
        fetch_workspace_data_api_mocks.assert_all_requests_are_fired = False
        pytest.skip("Only run Airbyte OSS tests against Airbyte OSS API URL")


@pytest.mark.parametrize(
    "component_body,expected_workspace_type,assert_all_requests_are_fired",
    [
        (OAUTH_AIRBYTE_CLOUD_COMPONENT_BODY_LEGACY_COMPONENT, AirbyteCloudWorkspace, True),
        (OAUTH_AIRBYTE_CLOUD_COMPONENT_BODY, AirbyteCloudWorkspace, True),
        (OAUTH_AIRBYTE_OSS_COMPONENT_BODY, AirbyteWorkspace, True),
        (BASIC_AIRBYTE_OSS_COMPONENT_BODY, AirbyteWorkspace, False),
        (NO_AUTH_AIRBYTE_OSS_COMPONENT_BODY, AirbyteWorkspace, False),
    ],
    ids=[
        "oauth_cloud_legacy_component",
        "oauth_cloud",
        "oauth_oss",
        "basic_oss",
        "no_auth_oss",
    ],
)
def test_basic_component_load(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    rest_api_url: str,
    config_api_url: str,
    component_body: dict,
    expected_workspace_type: type[BaseAirbyteWorkspace],
    assert_all_requests_are_fired: bool,
) -> None:
    fetch_workspace_data_api_mocks.assert_all_requests_are_fired = assert_all_requests_are_fired
    should_test_combinations(fetch_workspace_data_api_mocks, rest_api_url, expected_workspace_type)

    with (
        environ(
            {
                "AIRBYTE_REST_API_BASE_URL": rest_api_url,
                "AIRBYTE_CONFIGURATION_API_BASE_URL": config_api_url,
                "AIRBYTE_USERNAME": TEST_USERNAME,
                "AIRBYTE_PASSWORD": TEST_PASSWORD,
                "AIRBYTE_CLIENT_ID": TEST_CLIENT_ID,
                "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET,
                "AIRBYTE_WORKSPACE_ID": TEST_WORKSPACE_ID,
            }
        ),
        setup_airbyte_component(
            defs_yaml_contents=component_body,
        ) as (
            component,
            defs,
        ),
    ):
        assert defs.resolve_asset_graph().get_all_asset_keys() == {
            AssetKey(["test_prefix_test_stream"]),
            AssetKey(["test_prefix_test_another_stream"]),
        }
        assert (
            defs.get_assets_def("test_prefix_test_stream")
            .resource_defs["airbyte"]
            .configurable_resource_cls  # pyright: ignore [reportAttributeAccessIssue]
            == expected_workspace_type
        )


@pytest.mark.parametrize(
    "component_body,expected_workspace_type,assert_all_requests_are_fired",
    [
        (OAUTH_AIRBYTE_CLOUD_COMPONENT_BODY_LEGACY_COMPONENT, AirbyteCloudWorkspace, True),
        (OAUTH_AIRBYTE_CLOUD_COMPONENT_BODY, AirbyteCloudWorkspace, True),
        (OAUTH_AIRBYTE_OSS_COMPONENT_BODY, AirbyteWorkspace, True),
        (BASIC_AIRBYTE_OSS_COMPONENT_BODY, AirbyteWorkspace, False),
        (NO_AUTH_AIRBYTE_OSS_COMPONENT_BODY, AirbyteWorkspace, False),
    ],
    ids=[
        "oauth_cloud_legacy_component",
        "oauth_cloud",
        "oauth_oss",
        "basic_oss",
        "no_auth_oss",
    ],
)
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
    rest_api_url: str,
    config_api_url: str,
    component_body: dict,
    expected_workspace_type: type[BaseAirbyteWorkspace],
    assert_all_requests_are_fired: bool,
) -> None:
    fetch_workspace_data_api_mocks.assert_all_requests_are_fired = assert_all_requests_are_fired
    should_test_combinations(fetch_workspace_data_api_mocks, rest_api_url, expected_workspace_type)

    with (
        environ(
            {
                "AIRBYTE_REST_API_BASE_URL": rest_api_url,
                "AIRBYTE_CONFIGURATION_API_BASE_URL": config_api_url,
                "AIRBYTE_USERNAME": TEST_USERNAME,
                "AIRBYTE_PASSWORD": TEST_PASSWORD,
                "AIRBYTE_CLIENT_ID": TEST_CLIENT_ID,
                "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET,
                "AIRBYTE_WORKSPACE_ID": TEST_WORKSPACE_ID,
            }
        ),
        setup_airbyte_component(
            defs_yaml_contents=deep_merge_dicts(
                component_body,
                {"attributes": {"connection_selector": connection_selector}},
            ),
        ) as (
            component,
            defs,
        ),
    ):
        assert len(defs.resolve_asset_graph().get_all_asset_keys()) == num_assets


@pytest.mark.parametrize(
    "component_class",
    [
        AirbyteCloudWorkspaceComponent,
        AirbyteWorkspaceComponent,
    ],
    ids=[
        "airbyte_cloud_legacy_component",
        "airbyte_component",
    ],
)
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
    component_class: Union[type[AirbyteCloudWorkspaceComponent], type[AirbyteWorkspaceComponent]],
    rest_api_url: str,
    config_api_url: str,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
) -> None:
    defs = component_class(
        workspace=resource,
        connection_selector=filter_fn,
        translation=None,
    ).build_defs(ComponentTree.for_test().load_context)
    assert len(defs.resolve_asset_graph().get_all_asset_keys()) == num_assets


@pytest.mark.parametrize(
    "component_body,expected_workspace_type,assert_all_requests_are_fired",
    [
        (OAUTH_AIRBYTE_CLOUD_COMPONENT_BODY_LEGACY_COMPONENT, AirbyteCloudWorkspace, True),
        (OAUTH_AIRBYTE_CLOUD_COMPONENT_BODY, AirbyteCloudWorkspace, True),
        (OAUTH_AIRBYTE_OSS_COMPONENT_BODY, AirbyteWorkspace, True),
        (BASIC_AIRBYTE_OSS_COMPONENT_BODY, AirbyteWorkspace, False),
        (NO_AUTH_AIRBYTE_OSS_COMPONENT_BODY, AirbyteWorkspace, False),
    ],
    ids=[
        "oauth_cloud_legacy_component",
        "oauth_cloud",
        "oauth_oss",
        "basic_oss",
        "no_auth_oss",
    ],
)
class TestAirbyteTranslation(TestTranslation):
    def test_translation(
        self,
        fetch_workspace_data_api_mocks: responses.RequestsMock,
        attributes: Mapping[str, Any],
        assertion: Callable[[AssetSpec], bool],
        key_modifier: Optional[Callable[[AssetKey], AssetKey]],
        rest_api_url: str,
        config_api_url: str,
        component_body: dict,
        expected_workspace_type: type[BaseAirbyteWorkspace],
        assert_all_requests_are_fired: bool,
    ) -> None:
        fetch_workspace_data_api_mocks.assert_all_requests_are_fired = assert_all_requests_are_fired
        should_test_combinations(
            fetch_workspace_data_api_mocks, rest_api_url, expected_workspace_type
        )

        body = copy.deepcopy(component_body)
        body["attributes"]["translation"] = attributes
        with (
            environ(
                {
                    "AIRBYTE_REST_API_BASE_URL": rest_api_url,
                    "AIRBYTE_CONFIGURATION_API_BASE_URL": config_api_url,
                    "AIRBYTE_USERNAME": TEST_USERNAME,
                    "AIRBYTE_PASSWORD": TEST_PASSWORD,
                    "AIRBYTE_CLIENT_ID": TEST_CLIENT_ID,
                    "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET,
                    "AIRBYTE_WORKSPACE_ID": TEST_WORKSPACE_ID,
                }
            ),
            setup_airbyte_component(
                defs_yaml_contents=body,
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
