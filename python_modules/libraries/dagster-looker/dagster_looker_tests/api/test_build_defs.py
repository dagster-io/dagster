from collections.abc import Iterator

import pytest
import responses
from dagster import AssetKey, AssetSpec, Definitions, materialize
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster_looker import LookerFilter
from dagster_looker.api.assets import build_looker_pdt_assets_definitions
from dagster_looker.api.dagster_looker_api_translator import (
    DagsterLookerApiTranslator,
    LookerApiTranslatorStructureData,
    RequestStartPdtBuild,
)
from dagster_looker.api.resource import LookerResource, load_looker_asset_specs

from dagster_looker_tests.api.mock_looker_data import (
    mock_check_pdt_build,
    mock_folders,
    mock_looker_dashboard,
    mock_looker_dashboard_bases,
    mock_lookml_explore,
    mock_lookml_models,
    mock_lookml_other_explore,
    mock_other_looker_dashboard,
    mock_other_user,
    mock_start_pdt_build,
    mock_user,
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
        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/lookml_models/my_model/explores/my_other_explore",
            body=sdk.serialize(api_model=mock_lookml_other_explore),  # type: ignore
        )

        # Mock the request for all looker dashboards
        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/folders",
            body=sdk.serialize(api_model=mock_folders),  # type: ignore
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

        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/dashboards/2",
            body=sdk.serialize(api_model=mock_other_looker_dashboard),  # type: ignore
        )

        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/users/search",
            body=sdk.serialize(api_model=[mock_user, mock_other_user]),  # type: ignore
        )

        yield response


@responses.activate
def test_load_asset_specs_filter(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    asset_specs_by_key = {
        spec.key: spec
        for spec in load_looker_asset_specs(
            looker_resource,
            looker_filter=LookerFilter(
                dashboard_folders=[["my_folder", "my_subfolder"]],
                only_fetch_explores_used_in_dashboards=True,
            ),
        )
    }

    assert len(asset_specs_by_key) == 2
    assert AssetKey(["my_dashboard_2"]) not in asset_specs_by_key
    assert AssetKey(["my_model::my_other_explore"]) not in asset_specs_by_key


@responses.activate
def test_load_asset_specs(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    asset_specs_by_key = {spec.key: spec for spec in load_looker_asset_specs(looker_resource)}

    assert len(asset_specs_by_key) == 4

    expected_lookml_view_asset_dep_key = AssetKey(["view", "my_view"])
    expected_lookml_explore_asset_key = AssetKey(["my_model::my_explore"])
    expected_looker_dashboard_asset_key = AssetKey(["my_dashboard_1"])

    lookml_explore_asset = asset_specs_by_key[expected_lookml_explore_asset_key]
    assert [dep.asset_key for dep in lookml_explore_asset.deps] == [
        expected_lookml_view_asset_dep_key
    ]
    assert lookml_explore_asset.tags == {"dagster/kind/looker": "", "dagster/kind/explore": ""}
    assert lookml_explore_asset.metadata.get("dagster-looker/web_url") == MetadataValue.url(
        "https://your.cloud.looker.com/explore/my_model/my_explore"
    )
    looker_dashboard_asset = asset_specs_by_key[expected_looker_dashboard_asset_key]
    assert [dep.asset_key for dep in looker_dashboard_asset.deps] == [
        expected_lookml_explore_asset_key
    ]
    assert looker_dashboard_asset.tags == {"dagster/kind/looker": "", "dagster/kind/dashboard": ""}
    assert looker_dashboard_asset.owners == ["ben@dagsterlabs.com"]
    assert looker_dashboard_asset.metadata.get("dagster-looker/web_url") == MetadataValue.url(
        "https://your.cloud.looker.com/dashboards/1"
    )


@responses.activate
def test_build_defs_with_pdts(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    resource_key = "looker"

    pdts = build_looker_pdt_assets_definitions(
        resource_key=resource_key,
        request_start_pdt_builds=[RequestStartPdtBuild(model_name="my_model", view_name="my_view")],
    )

    defs = Definitions(
        assets=[*pdts, *load_looker_asset_specs(looker_resource)],
        resources={resource_key: looker_resource},
    )

    assert len(defs.get_all_asset_specs()) == 5

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
def test_custom_asset_specs(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    class CustomDagsterLookerApiTranslator(DagsterLookerApiTranslator):
        def get_asset_spec(self, looker_structure: LookerApiTranslatorStructureData) -> AssetSpec:
            default_spec = super().get_asset_spec(looker_structure)
            return default_spec.replace_attributes(
                key=default_spec.key.with_prefix("my_prefix"),
            ).merge_attributes(metadata={"custom": "metadata"})

    all_assets = (
        asset
        for asset in Definitions(
            assets=[*load_looker_asset_specs(looker_resource, CustomDagsterLookerApiTranslator())],
        )
        .get_asset_graph()
        .assets_defs
        if not asset.is_auto_created_stub
    )

    for asset in all_assets:
        for metadata in asset.metadata_by_key.values():
            assert "custom" in metadata
            assert metadata["custom"] == "metadata"
        assert all(key.path[0] == "my_prefix" for key in asset.keys)
        for deps in asset.asset_deps.values():
            assert all(key.path[0] == "my_prefix" for key in deps), str(deps)


@responses.activate
def test_custom_asset_specs_legacy(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    class CustomDagsterLookerApiTranslator(DagsterLookerApiTranslator):
        def get_asset_spec(self, looker_structure: LookerApiTranslatorStructureData) -> AssetSpec:
            default_spec = super().get_asset_spec(looker_structure)
            return default_spec.replace_attributes(
                key=default_spec.key.with_prefix("my_prefix"),
            ).merge_attributes(metadata={"custom": "metadata"})

    # Pass the translator type
    with pytest.warns(
        DeprecationWarning,
        match=r"Support of `dagster_looker_translator` as a Type\[DagsterLookerApiTranslator\]",
    ):
        all_assets = (
            asset
            for asset in Definitions(
                assets=[
                    *load_looker_asset_specs(looker_resource, CustomDagsterLookerApiTranslator)
                ],
            )
            .get_asset_graph()
            .assets_defs
            if not asset.is_auto_created_stub
        )

    for asset in all_assets:
        for metadata in asset.metadata_by_key.values():
            assert "custom" in metadata
            assert metadata["custom"] == "metadata"
        assert all(key.path[0] == "my_prefix" for key in asset.keys)
        for deps in asset.asset_deps.values():
            assert all(key.path[0] == "my_prefix" for key in deps), str(deps)
