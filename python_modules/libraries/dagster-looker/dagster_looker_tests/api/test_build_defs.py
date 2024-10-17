from typing import Iterator

import pytest
import responses
from dagster import AssetKey, AssetSpec, materialize
from dagster_looker.api.dagster_looker_api_translator import (
    DagsterLookerApiTranslator,
    LookerStructureData,
    RequestStartPdtBuild,
)
from dagster_looker.api.resource import LookerResource
from looker_sdk.sdk.api40.models import ScheduledPlanDestination, WriteScheduledPlan

from dagster_looker_tests.api.mock_looker_data import (
    mock_check_pdt_build,
    mock_looker_dashboard,
    mock_looker_dashboard_bases,
    mock_lookml_explore,
    mock_lookml_models,
    mock_start_pdt_build,
)

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
    sdk = looker_resource.get_sdk()

    with responses.RequestsMock() as response:
        # Mock the login request
        responses.add(method=responses.POST, url=f"{TEST_BASE_URL}/api/4.0/login", json={})

        # Mock the request for all lookml models
        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/lookml_models",
            body=sdk.serialize(api_model=mock_lookml_models),  # type: ignore
        )

        # Mock the request for a single lookml explore
        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/lookml_models/my_model/explores/my_explore",
            body=sdk.serialize(api_model=mock_lookml_explore),  # type: ignore
        )

        # Mock the request for all looker dashboards
        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/dashboards",
            body=sdk.serialize(api_model=mock_looker_dashboard_bases),  # type: ignore
        )

        # Mock the request for a single looker dashboard
        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/dashboards/1",
            body=sdk.serialize(api_model=mock_looker_dashboard),  # type: ignore
        )

        yield response


@responses.activate
def test_build_defs(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    asset_specs_by_key = {
        spec.key: spec for spec in looker_resource.build_defs().get_all_asset_specs()
    }

    assert len(asset_specs_by_key) == 3

    expected_lookml_view_asset_key = AssetKey(["view", "my_view"])
    expected_lookml_explore_asset_key = AssetKey(["my_model_my_explore"])
    expected_looker_dashboard_asset_key = AssetKey(["my_dashboard_1"])

    assert asset_specs_by_key[expected_lookml_view_asset_key]

    lookml_explore_asset = asset_specs_by_key[expected_lookml_explore_asset_key]
    assert [dep.asset_key for dep in lookml_explore_asset.deps] == [expected_lookml_view_asset_key]
    assert lookml_explore_asset.tags == {"dagster/kind/looker": "", "dagster/kind/explore": ""}

    looker_dashboard_asset = asset_specs_by_key[expected_looker_dashboard_asset_key]
    assert [dep.asset_key for dep in looker_dashboard_asset.deps] == [
        expected_lookml_explore_asset_key
    ]
    assert looker_dashboard_asset.tags == {"dagster/kind/looker": "", "dagster/kind/dashboard": ""}


@responses.activate
def test_build_defs_with_pdts(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    defs = looker_resource.build_defs(
        request_start_pdt_builds=[RequestStartPdtBuild(model_name="my_model", view_name="my_view")]
    )

    assert len(defs.get_all_asset_specs()) == 3

    sdk = looker_resource.get_sdk()

    responses.add(
        method=responses.GET,
        url=f"{TEST_BASE_URL}/api/4.0/derived_table/my_model/my_view/start",
        body=sdk.serialize(api_model=mock_start_pdt_build),  # type: ignore
    )

    responses.add(
        method=responses.GET,
        url=f"{TEST_BASE_URL}/api/4.0/derived_table/{mock_start_pdt_build.materialization_id}/status",
        body=sdk.serialize(api_model=mock_check_pdt_build),  # type: ignore
    )

    pdt = defs.get_repository_def().assets_defs_by_key[AssetKey(["view", "my_view"])]
    result = materialize([pdt])

    assert result.success


@responses.activate
def test_build_defs_with_scheduled_plans(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    destination = ScheduledPlanDestination(
        format="csv",
        type="email",
        address="ben@dagsterlabs.com",
        message="Test",
        apply_formatting=False,
        apply_vis=False,
    )
    defs = looker_resource.build_defs(scheduled_plans_by_dashboard_id={"1": destination})

    assert len(defs.get_all_asset_specs()) == 3

    sdk = looker_resource.get_sdk()

    responses.add(
        method=responses.POST,
        url=f"{TEST_BASE_URL}/api/4.0/scheduled_plans/run_once",
        body=sdk.serialize(
            api_model=WriteScheduledPlan(  # type: ignore
                dashboard_id="1",
                scheduled_plan_destination=[destination],
            )
        ),
    )

    dashboard = defs.get_repository_def().assets_defs_by_key[AssetKey(["my_dashboard_1"])]
    result = materialize([dashboard])

    assert result.success


@responses.activate
def test_custom_asset_specs(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    expected_metadata = {"custom": "metadata"}

    class CustomDagsterLookerApiTranslator(DagsterLookerApiTranslator):
        def get_asset_spec(self, looker_structure: LookerStructureData) -> AssetSpec:
            return super().get_asset_spec(looker_structure)._replace(metadata=expected_metadata)

    all_assets = (
        asset
        for asset in looker_resource.build_defs(
            dagster_looker_translator=CustomDagsterLookerApiTranslator()
        )
        .get_asset_graph()
        .assets_defs
        if not asset.is_auto_created_stub
    )

    for asset in all_assets:
        for metadata in asset.metadata_by_key.values():
            assert metadata == expected_metadata
