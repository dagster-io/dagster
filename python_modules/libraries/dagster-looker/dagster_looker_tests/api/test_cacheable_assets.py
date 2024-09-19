from typing import Iterator

import pytest
import responses
from dagster import AssetKey, AssetSpec
from dagster_looker.api.dagster_looker_api_translator import DagsterLookerApiTranslator
from dagster_looker.api.resource import LookerResource
from looker_sdk.sdk.api40.models import LookmlModelExplore

from dagster_looker_tests.api.mock_looker_data import mock_lookml_explore, mock_lookml_models

TEST_BASE_URL = "https://your.cloud.looker.com"


@pytest.fixture(name="looker_resource")
def looker_resource_fixture() -> LookerResource:
    return LookerResource(
        base_url=TEST_BASE_URL, client_id="client_id", client_secret="client_secret"
    )


@pytest.fixture(name="looker_instance_data_mocks")
def looker_instance_data_mocks_fixture(
    looker_resource: LookerResource,
) -> Iterator[responses.RequestsMock]:
    with responses.RequestsMock() as response:
        # Mock the login request
        responses.add(method=responses.POST, url=f"{TEST_BASE_URL}/api/4.0/login", json={})

        # Mock the request for all lookml models
        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/lookml_models",
            body=looker_resource.get_sdk().serialize(api_model=mock_lookml_models),  # type: ignore
        )

        # Mock the request for a single lookml explore
        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/lookml_models/my_model/explores/my_explore",
            body=looker_resource.get_sdk().serialize(api_model=mock_lookml_explore),  # type: ignore
        )

        yield response


@responses.activate
def test_build_defs(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    all_assets = looker_resource.build_defs().get_asset_graph().assets_defs

    assert len(all_assets) == 1

    explore_asset = all_assets[0]

    expected_asset_key = AssetKey(["my_model::my_explore"])
    assert list(explore_asset.keys) == [expected_asset_key]
    assert explore_asset.tags_by_key[expected_asset_key] == {
        "dagster/kind/looker": "",
        "dagster/kind/explore": "",
    }


@responses.activate
def test_custom_asset_specs(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    expected_metadata = {"custom": "metadata"}

    class CustomDagsterLookerApiTranslator(DagsterLookerApiTranslator):
        def get_asset_spec(self, api_model: LookmlModelExplore) -> AssetSpec:
            return super().get_asset_spec(api_model)._replace(metadata=expected_metadata)

    all_assets = (
        looker_resource.build_defs(dagster_looker_translator=CustomDagsterLookerApiTranslator())
        .get_asset_graph()
        .assets_defs
    )

    for asset in all_assets:
        for metadata in asset.metadata_by_key.values():
            assert metadata == expected_metadata
