# ruff: noqa: SLF001

from typing import Callable

import pytest
from dagster import asset, define_asset_job
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.reconstruct import ReconstructableJob, ReconstructableRepository
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.instance_for_test import instance_for_test
from dagster._utils.test.definitions import lazy_definitions
from dagster_tableau import TableauCloudWorkspace

from dagster_tableau_tests.conftest import (
    FAKE_CONNECTED_APP_CLIENT_ID,
    FAKE_CONNECTED_APP_SECRET_ID,
    FAKE_CONNECTED_APP_SECRET_VALUE,
    FAKE_POD_NAME,
    FAKE_SITE_NAME,
    FAKE_USERNAME,
)

resource = TableauCloudWorkspace(
    connected_app_client_id=FAKE_CONNECTED_APP_CLIENT_ID,
    connected_app_secret_id=FAKE_CONNECTED_APP_SECRET_ID,
    connected_app_secret_value=FAKE_CONNECTED_APP_SECRET_VALUE,
    username=FAKE_USERNAME,
    site_name=FAKE_SITE_NAME,
    pod_name=FAKE_POD_NAME,
)


@lazy_definitions
def cacheable_asset_defs():
    @asset
    def my_materializable_asset():
        pass

    return Definitions.merge(
        Definitions(assets=[my_materializable_asset], jobs=[define_asset_job("all_asset_job")]),
        resource.build_defs(),
    )


@pytest.mark.usefixtures("workspace_data_api_mocks_fn")
def test_using_cached_asset_data(
    workspace_data_api_mocks_fn: Callable,
) -> None:
    with instance_for_test() as instance:
        # Must initialize the resource's client before passing it to the mock response function
        resource.build_client()
        with workspace_data_api_mocks_fn(client=resource._client, include_views=True) as response:
            # Remove the resource's client to properly test the pending repo
            resource._client = None
            assert len(response.calls) == 0

            recon_repo = ReconstructableRepository.for_file(
                __file__, fn_name="cacheable_asset_defs"
            )
            repository_def = recon_repo.get_definition()

            # 4 calls to creates the defs
            assert len(response.calls) == 4

            # 1 Tableau external assets, 2 Tableau materializable asset and 1 Dagster materializable asset
            assert len(repository_def.assets_defs_by_key) == 1 + 2 + 1

            job_def = repository_def.get_job("all_asset_job")
            repository_load_data = repository_def.repository_load_data

            recon_repo = ReconstructableRepository.for_file(
                __file__, fn_name="cacheable_asset_defs"
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
                == 2
            ), "Expected two successful steps"

            # 4 calls to create the defs + 4 calls to materialize the Tableau assets with 1 sheet and 1 dashboard
            assert len(response.calls) == 4 + 4
