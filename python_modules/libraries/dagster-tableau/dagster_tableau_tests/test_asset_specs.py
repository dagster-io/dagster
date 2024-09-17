# ruff: noqa: SLF001

import uuid
from typing import Callable, Type, Union

import pytest
import responses
from dagster._core.definitions.reconstruct import ReconstructableJob, ReconstructableRepository
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.instance_for_test import instance_for_test
from dagster._utils import file_relative_path
from dagster_tableau import TableauCloudWorkspace, TableauServerWorkspace


@responses.activate
@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
@pytest.mark.usefixtures("site_name")
@pytest.mark.usefixtures("workspace_data_api_mocks_fn")
def test_fetch_tableau_workspace_data(
    clazz: Union[Type[TableauCloudWorkspace], Type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
    workspace_data_api_mocks_fn: Callable,
) -> None:
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }

    resource = clazz(**resource_args)  # type: ignore
    resource.build_client()

    with workspace_data_api_mocks_fn(client=resource._client):
        actual_workspace_data = resource.fetch_tableau_workspace_data()
        assert len(actual_workspace_data.workbooks_by_id) == 1
        assert len(actual_workspace_data.views_by_id) == 1
        assert len(actual_workspace_data.data_sources_by_id) == 1


@responses.activate
@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
@pytest.mark.usefixtures("site_name")
@pytest.mark.usefixtures("workspace_data_api_mocks_fn")
def test_translator_spec(
    clazz: Union[Type[TableauCloudWorkspace], Type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
    workspace_data_api_mocks_fn: Callable,
) -> None:
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }

    resource = clazz(**resource_args)  # type: ignore
    resource.build_client()

    with workspace_data_api_mocks_fn(client=resource._client):
        all_assets = resource.build_defs().get_asset_graph().assets_defs

        # 1 view and 1 data source
        assert len(all_assets) == 2

        # Sanity check outputs, translator tests cover details here
        view_asset = next(asset for asset in all_assets if "workbook" in asset.key.path[0])
        assert view_asset.key.path == ["test_workbook", "view", "sales"]

        data_source_asset = next(asset for asset in all_assets if "datasource" in asset.key.path[0])
        assert data_source_asset.key.path == ["superstore_datasource"]


@pytest.mark.usefixtures("workspace_data_api_mocks_fn")
def test_using_cached_asset_data(
    workspace_data_api_mocks_fn: Callable,
) -> None:
    with instance_for_test() as instance:
        from dagster_tableau_tests.pending_repo import (
            pending_repo_from_cached_asset_metadata,
            resource,
        )

        # Must initialize the resource's client before passing it to the mock response function
        resource.build_client()
        with workspace_data_api_mocks_fn(client=resource._client) as response:
            # Remove the resource's client to properly test the pending repo
            resource._client = None
            assert len(response.calls) == 0

            # first, we resolve the repository to generate our cached metadata
            repository_def = pending_repo_from_cached_asset_metadata.compute_repository_definition()
            assert len(response.calls) == 4

            # 2 Tableau external assets, one materializable asset
            assert len(repository_def.assets_defs_by_key) == 2 + 1

            job_def = repository_def.get_job("all_asset_job")
            repository_load_data = repository_def.repository_load_data

            recon_repo = ReconstructableRepository.for_file(
                file_relative_path(__file__, "pending_repo.py"),
                fn_name="pending_repo_from_cached_asset_metadata",
            )
            recon_job = ReconstructableJob(repository=recon_repo, job_name="all_asset_job")

            execution_plan = create_execution_plan(
                recon_job, repository_load_data=repository_load_data
            )

            run = instance.create_run_for_job(job_def=job_def, execution_plan=execution_plan)

            events = execute_plan(
                execution_plan=execution_plan,
                job=recon_job,
                dagster_run=run,
                instance=instance,
            )

            assert (
                len(
                    [event for event in events if event.event_type == DagsterEventType.STEP_SUCCESS]
                )
                == 1
            ), "Expected two successful steps"

            assert len(response.calls) == 4
