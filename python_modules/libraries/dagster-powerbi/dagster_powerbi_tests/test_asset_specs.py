import uuid

import pytest
import responses
from dagster import materialize, multi_asset
from dagster._config.field_utils import EnvVar
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.reconstruct import ReconstructableJob, ReconstructableRepository
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.instance_for_test import instance_for_test
from dagster._utils.env import environ
from dagster._utils.test.definitions import lazy_definitions
from dagster_powerbi import PowerBIWorkspace
from dagster_powerbi.resource import BASE_API_URL, PowerBIToken

from dagster_powerbi_tests.conftest import SAMPLE_SEMANTIC_MODEL


def test_fetch_powerbi_workspace_data(workspace_data_api_mocks: None, workspace_id: str) -> None:
    fake_token = uuid.uuid4().hex
    resource = PowerBIWorkspace(
        credentials=PowerBIToken(api_token=fake_token),
        workspace_id=workspace_id,
    )

    actual_workspace_data = resource._fetch_powerbi_workspace_data()  # noqa: SLF001
    assert len(actual_workspace_data.dashboards_by_id) == 1
    assert len(actual_workspace_data.reports_by_id) == 1
    assert len(actual_workspace_data.semantic_models_by_id) == 1
    assert len(actual_workspace_data.data_sources_by_id) == 2


def test_translator_dashboard_spec(workspace_data_api_mocks: None, workspace_id: str) -> None:
    fake_token = uuid.uuid4().hex
    resource = PowerBIWorkspace(
        credentials=PowerBIToken(api_token=fake_token),
        workspace_id=workspace_id,
    )
    all_asset_specs = resource.build_asset_specs()

    # 1 dashboard, 1 report, 1 semantic model
    assert len(all_asset_specs) == 3

    # Sanity check outputs, translator tests cover details here
    dashboard_asset = next(asset for asset in all_asset_specs if asset.key.path[0] == "dashboard")
    assert dashboard_asset.key.path == ["dashboard", "Sales_Returns_Sample_v201912"]

    report_asset = next(asset for asset in all_asset_specs if asset.key.path[0] == "report")
    assert report_asset.key.path == ["report", "Sales_Returns_Sample_v201912"]

    semantic_model_asset = next(
        asset for asset in all_asset_specs if asset.key.path[0] == "semantic_model"
    )
    assert semantic_model_asset.key.path == [
        "semantic_model",
        "Sales_Returns_Sample_v201912",
    ]

    assert {dep.asset_key for dep in semantic_model_asset.deps} == {
        AssetKey(["data_27_09_2019_xlsx"]),
        AssetKey(["sales_marketing_datas_xlsx"]),
    }


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
            *resource.build_asset_specs(),
            *resource_second_workspace.build_asset_specs(),
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
    semantic_model_specs = resource.build_assets_specs(asset_types={"semantic_model"})
    assert len(semantic_model_specs) == 1

    assert semantic_model_specs[0].key.path == [
        "semantic_model",
        "Sales_Returns_Sample_v201912",
    ]

    @multi_asset(specs=semantic_model_specs, can_subset=True)
    def semantic_model_assets_def(context):
        yield from resource.refresh(context=context).stream()

    # materialize the semantic model

    workspace_data_api_mocks.add(
        method=responses.POST,
        url=f"{BASE_API_URL}/datasets/{SAMPLE_SEMANTIC_MODEL['id']}/refreshes",
        json={"notifyOption": "NoNotification"},
        status=202,
    )

    workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{BASE_API_URL}/datasets/{SAMPLE_SEMANTIC_MODEL['id']}/refreshes",
        json={"value": [{"status": "Unknown"}]},
        status=200,
    )
    workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{BASE_API_URL}/datasets/{SAMPLE_SEMANTIC_MODEL['id']}/refreshes",
        json={
            "value": [
                {
                    "status": "Completed" if success else "Failed",
                    "serviceExceptionJson": {},
                }
            ]
        },
        status=200,
    )

    result = materialize([semantic_model_assets_def], raise_on_error=False)
    assert result.success is success


@lazy_definitions
def state_derived_defs() -> Definitions:
    fake_token = uuid.uuid4().hex
    resource = PowerBIWorkspace(
        credentials=PowerBIToken(api_token=fake_token),
        workspace_id="a2122b8f-d7e1-42e8-be2b-a5e636ca3221",
    )

    @asset
    def my_materializable_asset(): ...

    return Definitions(
        assets=[*resource.build_asset_specs(), my_materializable_asset],
        jobs=[define_asset_job("all_asset_job")],
    )


def test_state_derived_defs(
    workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with instance_for_test() as instance:
        assert len(workspace_data_api_mocks.calls) == 0

        # first, we resolve the repository to generate our cached metadata
        repository_def = state_derived_defs().get_repository_def()
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
