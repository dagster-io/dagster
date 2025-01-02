import uuid
from pathlib import Path

import pytest
import responses
from dagster import materialize
from dagster._config.field_utils import EnvVar
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.reconstruct import (
    ReconstructableJob,
    ReconstructableRepository,
    initialize_repository_def_from_pointer,
)
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.instance_for_test import instance_for_test
from dagster._utils.env import environ
from dagster._utils.test.definitions import lazy_definitions
from dagster_powerbi import PowerBIWorkspace
from dagster_powerbi.assets import build_semantic_model_refresh_asset_definition
from dagster_powerbi.resource import BASE_API_URL, PowerBIToken, load_powerbi_asset_specs
from dagster_powerbi.translator import DagsterPowerBITranslator, PowerBITranslatorData

from dagster_powerbi_tests.conftest import SAMPLE_SEMANTIC_MODEL


def test_fetch_powerbi_workspace_data(workspace_data_api_mocks: None, workspace_id: str) -> None:
    fake_token = uuid.uuid4().hex
    resource = PowerBIWorkspace(
        credentials=PowerBIToken(api_token=fake_token),
        workspace_id=workspace_id,
    )

    actual_workspace_data = resource._fetch_powerbi_workspace_data(use_workspace_scan=False)  # noqa: SLF001
    assert len(actual_workspace_data.dashboards_by_id) == 1
    assert len(actual_workspace_data.reports_by_id) == 1
    assert len(actual_workspace_data.semantic_models_by_id) == 1
    assert len(actual_workspace_data.data_sources_by_id) == 2


def test_fetch_powerbi_workspace_data_scan(
    workspace_scan_data_api_mocks: None, workspace_id: str
) -> None:
    fake_token = uuid.uuid4().hex
    resource = PowerBIWorkspace(
        credentials=PowerBIToken(api_token=fake_token),
        workspace_id=workspace_id,
    )

    actual_workspace_data = resource._fetch_powerbi_workspace_data(use_workspace_scan=True)  # noqa: SLF001
    assert len(actual_workspace_data.dashboards_by_id) == 1
    assert len(actual_workspace_data.reports_by_id) == 1
    assert len(actual_workspace_data.semantic_models_by_id) == 1
    # assert len(actual_workspace_data.data_sources_by_id) == 2


def test_translator_dashboard_spec(workspace_data_api_mocks: None, workspace_id: str) -> None:
    fake_token = uuid.uuid4().hex
    resource = PowerBIWorkspace(
        credentials=PowerBIToken(api_token=fake_token),
        workspace_id=workspace_id,
    )
    all_assets = load_powerbi_asset_specs(resource, use_workspace_scan=False)

    # 1 dashboard, 1 report, 1 semantic model
    assert len(all_assets) == 3

    # Sanity check outputs, translator tests cover details here
    dashboard_asset = next(asset for asset in all_assets if asset.key.path[0] == "dashboard")
    assert dashboard_asset.key.path == ["dashboard", "Sales_Returns_Sample_v201912"]

    report_asset = next(asset for asset in all_assets if asset.key.path[0] == "report")
    assert report_asset.key.path == ["report", "Sales_Returns_Sample_v201912"]

    semantic_model_asset = next(
        asset for asset in all_assets if asset.key.path[0] == "semantic_model"
    )
    assert semantic_model_asset.key.path == ["semantic_model", "Sales_Returns_Sample_v201912"]


class MyCustomTranslator(DagsterPowerBITranslator):
    def get_asset_spec(self, data: PowerBITranslatorData) -> AssetSpec:
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("prefix"),
        ).merge_attributes(metadata={"custom": "metadata"})


def test_translator_custom_metadata(workspace_data_api_mocks: None, workspace_id: str) -> None:
    fake_token = uuid.uuid4().hex
    resource = PowerBIWorkspace(
        credentials=PowerBIToken(api_token=fake_token),
        workspace_id=workspace_id,
    )
    all_asset_specs = load_powerbi_asset_specs(
        workspace=resource,
        dagster_powerbi_translator=MyCustomTranslator(),
        use_workspace_scan=False,
    )
    asset_spec = next(spec for spec in all_asset_specs)

    assert "custom" in asset_spec.metadata
    assert asset_spec.metadata["custom"] == "metadata"
    assert asset_spec.key.path == ["prefix", "dashboard", "Sales_Returns_Sample_v201912"]
    assert "dagster/kind/powerbi" in asset_spec.tags


def test_translator_custom_metadata_legacy(
    workspace_data_api_mocks: None, workspace_id: str
) -> None:
    fake_token = uuid.uuid4().hex
    resource = PowerBIWorkspace(
        credentials=PowerBIToken(api_token=fake_token),
        workspace_id=workspace_id,
    )
    with pytest.warns(
        DeprecationWarning,
        match=r"Support of `dagster_powerbi_translator` as a Type\[DagsterPowerBITranslator\]",
    ):
        # Pass the translator type
        all_asset_specs = load_powerbi_asset_specs(
            workspace=resource,
            dagster_powerbi_translator=MyCustomTranslator,
            use_workspace_scan=False,
        )
    asset_spec = next(spec for spec in all_asset_specs)

    assert "custom" in asset_spec.metadata
    assert asset_spec.metadata["custom"] == "metadata"
    assert asset_spec.key.path == ["prefix", "dashboard", "Sales_Returns_Sample_v201912"]
    assert "dagster/kind/powerbi" in asset_spec.tags


@lazy_definitions
def state_derived_defs_two_workspaces() -> Definitions:
    resource = PowerBIWorkspace(
        credentials=PowerBIToken(api_token=EnvVar("FAKE_API_TOKEN")),
        workspace_id="a2122b8f-d7e1-42e8-be2b-a5e636ca3221",
    )
    resource_second_workspace = PowerBIWorkspace(
        credentials=PowerBIToken(api_token=EnvVar("FAKE_API_TOKEN")),
        workspace_id="c5322b8a-d7e1-42e8-be2b-a5e636ca3221",
    )
    return Definitions(
        assets=[
            *load_powerbi_asset_specs(resource, use_workspace_scan=False),
            *load_powerbi_asset_specs(resource_second_workspace, use_workspace_scan=False),
        ]
    )


def test_two_workspaces(
    workspace_data_api_mocks: responses.RequestsMock,
    second_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with instance_for_test(), environ({"FAKE_API_TOKEN": uuid.uuid4().hex}):
        assert len(workspace_data_api_mocks.calls) == 0

        # first, we resolve the repository to generate our cached metadata
        repository_def = state_derived_defs_two_workspaces().get_repository_def()
        assert len(workspace_data_api_mocks.calls) == 9

        # 3 PowerBI external assets from first workspace, 1 from second
        assert len(repository_def.assets_defs_by_key) == 3 + 1


@pytest.mark.parametrize("success", [True, False])
def test_refreshable_semantic_model(
    workspace_data_api_mocks: responses.RequestsMock, workspace_id: str, success: bool
) -> None:
    fake_token = uuid.uuid4().hex
    resource = PowerBIWorkspace(
        credentials=PowerBIToken(api_token=fake_token),
        workspace_id=workspace_id,
        refresh_poll_interval=0,
    )
    all_specs = load_powerbi_asset_specs(resource, use_workspace_scan=False)

    assets_with_semantic_models = [
        build_semantic_model_refresh_asset_definition(resource_key="powerbi", spec=spec)
        if spec.tags.get("dagster-powerbi/asset_type") == "semantic_model"
        else spec
        for spec in all_specs
    ]

    # 1 dashboard, 1 report, 1 semantic model
    assert len(assets_with_semantic_models) == 3

    semantic_model_asset = next(
        asset for asset in assets_with_semantic_models if asset.key.path[0] == "semantic_model"
    )

    assert semantic_model_asset.key.path == ["semantic_model", "Sales_Returns_Sample_v201912"]
    assert isinstance(semantic_model_asset, AssetsDefinition) and semantic_model_asset.is_executable

    # materialize the semantic model

    workspace_data_api_mocks.add(
        method=responses.POST,
        url=f"{BASE_API_URL}/groups/{workspace_id}/datasets/{SAMPLE_SEMANTIC_MODEL['id']}/refreshes",
        json={"notifyOption": "NoNotification"},
        status=202,
    )

    workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{BASE_API_URL}/groups/{workspace_id}/datasets/{SAMPLE_SEMANTIC_MODEL['id']}/refreshes",
        json={"value": [{"status": "Unknown"}]},
        status=200,
    )
    workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{BASE_API_URL}/groups/{workspace_id}/datasets/{SAMPLE_SEMANTIC_MODEL['id']}/refreshes",
        json={
            "value": [{"status": "Completed" if success else "Failed", "serviceExceptionJson": {}}]
        },
        status=200,
    )

    # Missing resource
    with pytest.raises(DagsterInvalidDefinitionError):
        materialize([semantic_model_asset], raise_on_error=False)

    result = materialize(
        [semantic_model_asset], raise_on_error=False, resources={"powerbi": resource}
    )
    assert result.success is success


@pytest.mark.parametrize("success", [True, False])
def test_refreshable_semantic_model_legacy(
    workspace_data_api_mocks: responses.RequestsMock, workspace_id: str, success: bool
) -> None:
    fake_token = uuid.uuid4().hex
    resource = PowerBIWorkspace(
        credentials=PowerBIToken(api_token=fake_token),
        workspace_id=workspace_id,
        refresh_poll_interval=0,
    )

    defs = resource.build_defs(enable_refresh_semantic_models=True)

    semantic_model_asset = next(
        asset
        for asset in defs.get_asset_graph().assets_defs
        if asset.is_executable and asset.key.path[0] == "semantic_model"
    )

    assert semantic_model_asset.key.path == ["semantic_model", "Sales_Returns_Sample_v201912"]
    assert isinstance(semantic_model_asset, AssetsDefinition) and semantic_model_asset.is_executable

    # materialize the semantic model

    workspace_data_api_mocks.add(
        method=responses.POST,
        url=f"{BASE_API_URL}/groups/{workspace_id}/datasets/{SAMPLE_SEMANTIC_MODEL['id']}/refreshes",
        json={"notifyOption": "NoNotification"},
        status=202,
    )

    workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{BASE_API_URL}/groups/{workspace_id}/datasets/{SAMPLE_SEMANTIC_MODEL['id']}/refreshes",
        json={"value": [{"status": "Unknown"}]},
        status=200,
    )
    workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{BASE_API_URL}/groups/{workspace_id}/datasets/{SAMPLE_SEMANTIC_MODEL['id']}/refreshes",
        json={
            "value": [{"status": "Completed" if success else "Failed", "serviceExceptionJson": {}}]
        },
        status=200,
    )

    result = materialize([semantic_model_asset], raise_on_error=False)
    assert result.success is success


@lazy_definitions
def state_derived_defs() -> Definitions:
    fake_token = uuid.uuid4().hex
    resource = PowerBIWorkspace(
        credentials=PowerBIToken(api_token=fake_token),
        workspace_id="a2122b8f-d7e1-42e8-be2b-a5e636ca3221",
    )
    powerbi_specs = load_powerbi_asset_specs(resource, use_workspace_scan=False)

    @asset
    def my_materializable_asset(): ...

    return Definitions(
        assets=[my_materializable_asset, *powerbi_specs], jobs=[define_asset_job("all_asset_job")]
    )


def test_state_derived_defs(
    workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with instance_for_test() as instance:
        assert len(workspace_data_api_mocks.calls) == 0

        repository_def = initialize_repository_def_from_pointer(
            CodePointer.from_python_file(str(Path(__file__)), "state_derived_defs", None),
        )

        # first, we resolve the repository to generate our cached metadata
        assert len(workspace_data_api_mocks.calls) == 5

        # 3 PowerBI external assets, one materializable asset
        assert len(repository_def.assets_defs_by_key) == 3 + 1

        # Assert that all Power BI assets have upstreams, which are resolved
        for asset_def in repository_def.assets_defs_by_key.values():
            for key, deps in asset_def.asset_deps.items():
                if key.path[-1] == "my_materializable_asset":
                    continue
                if key.path[0] == "semantic_model":
                    continue
                assert len(deps) > 0, f"Expected upstreams for {key}"
                assert all(
                    dep in repository_def.assets_defs_by_key for dep in deps
                ), f"Asset {key} depends on {deps} which are not in the repository"

        job_def = repository_def.get_job("all_asset_job")
        repository_load_data = repository_def.repository_load_data

        recon_repo = ReconstructableRepository.for_file(__file__, fn_name="state_derived_defs")
        recon_job = ReconstructableJob(repository=recon_repo, job_name="all_asset_job")

        execution_plan = create_execution_plan(recon_job, repository_load_data=repository_load_data)

        run = instance.create_run_for_job(job_def=job_def, execution_plan=execution_plan)

        events = execute_plan(
            execution_plan=execution_plan,
            job=recon_job,
            dagster_run=run,
            instance=instance,
        )

        assert (
            len([event for event in events if event.event_type == DagsterEventType.STEP_SUCCESS])
            == 1
        ), "Expected two successful steps"

        assert len(workspace_data_api_mocks.calls) == 5
