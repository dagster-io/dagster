"""Fixtures for Looker API tests."""

from collections.abc import Iterator

import pytest
import responses
from dagster._core.instance_for_test import instance_for_test
from looker_sdk.sdk.api40.models import (
    Dashboard,
    DashboardBase,
    DashboardFilter,
    FolderBase,
    LookmlModel,
    LookmlModelExplore,
    LookmlModelNavExplore,
)


@pytest.fixture
def looker_base_url() -> str:
    """Base URL for Looker API."""
    return "https://my-looker.cloud.looker.com"


@pytest.fixture
def looker_api_mocks(looker_base_url: str) -> Iterator[responses.RequestsMock]:
    """Mock Looker API responses."""
    with (
        responses.RequestsMock(assert_all_requests_are_fired=False) as response,
        instance_for_test(),
    ):
        # Mock login endpoint
        response.add(
            method=responses.POST,
            url=f"{looker_base_url}/api/4.0/login",
            json={"access_token": "test_token", "token_type": "Bearer"},
            status=200,
        )

        # Mock all_lookml_models endpoint
        response.add(
            method=responses.GET,
            url=f"{looker_base_url}/api/4.0/lookml_models",
            json=[
                {
                    "name": "my_model",
                    "explores": [
                        {"name": "my_explore"},
                    ],
                }
            ],
            status=200,
        )

        # Mock lookml_model_explore endpoint
        response.add(
            method=responses.GET,
            url=f"{looker_base_url}/api/4.0/lookml_models/my_model/explores/my_explore",
            json={
                "id": "my_model::my_explore",
                "view_name": "my_view",
                "sql_table_name": "my_table",
            },
            status=200,
        )

        # Mock all_folders endpoint
        response.add(
            method=responses.GET,
            url=f"{looker_base_url}/api/4.0/folders",
            json=[
                {
                    "id": "1",
                    "name": "my_folder",
                    "parent_id": None,
                }
            ],
            status=200,
        )

        # Mock search_dashboard_elements endpoint - use regex to match query params
        response.add(
            method=responses.GET,
            url=f"{looker_base_url}/api/4.0/dashboard_elements/search",
            json=[],
            status=200,
        )

        # Mock all_dashboards endpoint
        response.add(
            method=responses.GET,
            url=f"{looker_base_url}/api/4.0/dashboards",
            json=[
                {
                    "id": "1",
                    "hidden": False,
                    "folder": {
                        "id": "1",
                        "name": "my_folder",
                        "parent_id": None,
                    },
                }
            ],
            status=200,
        )

        # Mock dashboard endpoint
        response.add(
            method=responses.GET,
            url=f"{looker_base_url}/api/4.0/dashboards/1",
            json={
                "id": "1",
                "title": "my_dashboard",
                "dashboard_filters": [
                    {
                        "model": "my_model",
                        "explore": "my_explore",
                    }
                ],
                "user_id": "1",
                "url": "/dashboards/1",
            },
            status=200,
        )

        # Mock users search endpoint
        response.add(
            method=responses.GET,
            url=f"{looker_base_url}/api/4.0/users/search",
            json=[
                {
                    "id": "1",
                    "email": "test@example.com",
                }
            ],
            status=200,
        )

        yield response


@pytest.fixture
def sample_lookml_models() -> list[LookmlModel]:
    """Sample LookML models for testing."""
    return [
        LookmlModel(
            explores=[
                LookmlModelNavExplore(name="my_explore"),
            ],
            name="my_model",
        )
    ]


@pytest.fixture
def sample_lookml_explore() -> LookmlModelExplore:
    """Sample LookML explore for testing."""
    return LookmlModelExplore(
        id="my_model::my_explore",
        view_name="my_view",
        sql_table_name="my_table",
    )


@pytest.fixture
def sample_folders() -> list[FolderBase]:
    """Sample folders for testing."""
    return [
        FolderBase(parent_id=None, name="my_folder", id="1"),
    ]


@pytest.fixture
def sample_dashboard_bases() -> list[DashboardBase]:
    """Sample dashboard bases for testing."""
    return [
        DashboardBase(
            id="1",
            hidden=False,
            folder=FolderBase(name="my_folder", id="1", parent_id=None),
        ),
    ]


@pytest.fixture
def sample_dashboard() -> Dashboard:
    """Sample dashboard for testing."""
    return Dashboard(
        title="my_dashboard",
        id="1",
        dashboard_filters=[
            DashboardFilter(model="my_model", explore="my_explore"),
        ],
        user_id="1",
        url="/dashboards/1",
    )
