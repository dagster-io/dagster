import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest
import responses
from dagster import AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.env import environ
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.testing.utils import create_defs_folder_sandbox
from dagster_census import CensusComponent
from dagster_shared.merger import deep_merge_dicts

# Test constants
TEST_API_KEY = "test_api_key"
TEST_SYNC_ID_1 = 61
TEST_SYNC_ID_2 = 62
TEST_SYNC_NAME_1 = "test_sync_1"
TEST_SYNC_NAME_2 = "test_sync_2"
TEST_SOURCE_ID = 15
TEST_DESTINATION_ID = 15

CENSUS_API_BASE_URL = "https://app.getcensus.com/api/v1"


def get_sample_sync_data(sync_id: int, sync_name: str) -> dict[str, Any]:
    """Returns sample sync data for testing."""
    return {
        "id": sync_id,
        "label": sync_name,
        "resource_identifier": f"sync_{sync_id}",
        "schedule_frequency": "never",
        "schedule_day": None,
        "schedule_hour": None,
        "schedule_minute": None,
        "created_at": "2021-10-22T00:40:11.246Z",
        "updated_at": "2021-10-22T00:43:44.173Z",
        "operation": "upsert",
        "paused": False,
        "status": "Ready",
        "lead_union_insert_to": None,
        "trigger_on_dbt_cloud_rebuild": False,
        "field_behavior": "specific_properties",
        "field_normalization": None,
        "source_attributes": {
            "connection_id": TEST_SOURCE_ID,
            "object": {
                "type": "model",
                "id": 15,
                "name": "test_model",
                "created_at": "2021-10-11T20:52:58.293Z",
                "updated_at": "2021-10-14T23:15:18.508Z",
                "query": "select email, name from users",
            },
        },
        "destination_attributes": {"connection_id": TEST_DESTINATION_ID, "object": "user"},
        "mappings": [
            {
                "from": {"type": "column", "data": "EMAIL"},
                "to": "external_id",
                "is_primary_identifier": True,
                "generate_field": False,
                "preserve_values": False,
                "operation": None,
            },
            {
                "from": {
                    "type": "constant_value",
                    "data": {"value": "test", "basic_type": "text"},
                },
                "to": "first_name",
                "is_primary_identifier": False,
                "generate_field": False,
                "preserve_values": False,
                "operation": None,
            },
        ],
    }


def get_sample_syncs_response() -> dict[str, Any]:
    """Returns a paginated response for syncs list."""
    return {
        "status": "success",
        "data": [
            get_sample_sync_data(TEST_SYNC_ID_1, TEST_SYNC_NAME_1),
            get_sample_sync_data(TEST_SYNC_ID_2, TEST_SYNC_NAME_2),
        ],
        "pagination": {
            "page": 1,
            "per_page": 25,
            "total": 2,
            "last_page": 1,
        },
    }


@contextmanager
def setup_census_component(
    defs_yaml_contents: dict[str, Any],
) -> Iterator[tuple[CensusComponent, Definitions]]:
    """Sets up a components project with a Census component based on provided params."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=CensusComponent, defs_yaml_contents=defs_yaml_contents
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (
                component,
                defs,
            ),
        ):
            assert isinstance(component, CensusComponent)
            asyncio.run(component.refresh_state(sandbox.project_root))

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (
                component,
                defs,
            ),
        ):
            assert isinstance(component, CensusComponent)
            yield component, defs


BASIC_CENSUS_COMPONENT_BODY = {
    "type": "dagster_census.CensusComponent",
    "attributes": {
        "workspace": {
            "api_key": "{{ env.CENSUS_API_KEY }}",
        },
    },
}


@pytest.fixture(name="base_api_mocks")
def base_api_mocks_fixture() -> Iterator[responses.RequestsMock]:
    """Base API mocks fixture."""
    with responses.RequestsMock() as response:
        yield response


@pytest.fixture(name="fetch_workspace_data_api_mocks")
def fetch_workspace_data_api_mocks_fixture(
    base_api_mocks: responses.RequestsMock,
) -> Iterator[responses.RequestsMock]:
    """Fixture that mocks Census API calls for fetching workspace data."""
    base_api_mocks.add(
        method=responses.GET,
        url=f"{CENSUS_API_BASE_URL}/syncs",
        json=get_sample_syncs_response(),
        status=200,
    )
    yield base_api_mocks


def test_basic_component_load(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    """Test basic component loading with workspace data."""
    with (
        environ(
            {
                "CENSUS_API_KEY": TEST_API_KEY,
            }
        ),
        setup_census_component(
            defs_yaml_contents=deep_merge_dicts(
                BASIC_CENSUS_COMPONENT_BODY,
                {"attributes": {"defs_state": {"management_type": "LOCAL_FILESYSTEM"}}},
            ),
        ) as (
            _component,
            defs,
        ),
    ):
        assert defs.resolve_asset_graph().get_all_asset_keys() == {
            AssetKey(TEST_SYNC_NAME_1),
            AssetKey(TEST_SYNC_NAME_2),
        }


@pytest.mark.parametrize(
    "sync_selector, num_assets",
    [
        ({"by_name": [TEST_SYNC_NAME_1]}, 1),
        ({"by_id": [TEST_SYNC_ID_1]}, 1),
        ({"by_id": []}, 0),
        ({"by_name": [TEST_SYNC_NAME_1, TEST_SYNC_NAME_2]}, 2),
        ({"by_name": [TEST_SYNC_NAME_1, "nonexistent_sync"]}, 1),
    ],
    ids=[
        "single_sync_by_name",
        "single_sync_by_id",
        "no_syncs",
        "multiple_syncs",
        "partial_match",
    ],
)
def test_basic_component_filter(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    sync_selector: dict[str, Any],
    num_assets: int,
) -> None:
    """Test component filtering with sync selectors."""
    with (
        environ(
            {
                "CENSUS_API_KEY": TEST_API_KEY,
            }
        ),
        setup_census_component(
            defs_yaml_contents=deep_merge_dicts(
                BASIC_CENSUS_COMPONENT_BODY,
                {"attributes": {"sync_selector": sync_selector}},
            ),
        ) as (
            _component,
            defs,
        ),
    ):
        assert len(defs.resolve_asset_graph().get_all_asset_keys()) == num_assets
