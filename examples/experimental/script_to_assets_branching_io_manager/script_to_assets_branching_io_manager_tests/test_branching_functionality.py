import os
import subprocess
import tempfile
from contextlib import contextmanager
from typing import List

import pytest
import script_to_assets_branching_io_manager
from dagster._core.definitions.assets_job import ASSET_BASE_JOB_PREFIX
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.repository_definition import SINGLETON_REPOSITORY_NAME
from dagster._core.instance import DagsterInstance
from dagster._core.storage.pipeline_run import DagsterRun, DagsterRunStatus
from dagster._core.test_utils import environ, instance_for_test, poll_for_finished_run
from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext
from dagster._core.workspace.load_target import ModuleTarget
from dagster._utils import check, file_relative_path


@pytest.fixture(name="package_dir")
def package_dir_fixture():
    package_dir = file_relative_path(__file__, "../script_to_assets_branching_io_manager")

    cwd = os.getcwd()
    try:
        os.chdir(package_dir)
        yield package_dir
    finally:
        os.chdir(cwd)


@pytest.fixture(name="prod_storage")
def prod_storage_fixture(package_dir):
    prod_storage_dir = os.path.join(package_dir, "prod_storage")
    if os.path.exists(prod_storage_dir):
        subprocess.check_output(["rm", "-rf", prod_storage_dir])
    os.mkdir(prod_storage_dir)
    return prod_storage_dir


@pytest.fixture(name="branch_storage")
def branch_storage_fixture(package_dir):
    branch_storage_dir = os.path.join(package_dir, "my-featured-branch_storage")
    if os.path.exists(branch_storage_dir):
        subprocess.check_output(["rm", "-rf", branch_storage_dir])
    os.mkdir(branch_storage_dir)
    return branch_storage_dir


@pytest.fixture()
def temp_dir():
    with tempfile.TemporaryDirectory() as tempdir:
        yield tempdir


@contextmanager
def prod_instance(temp_dir):
    prod_dagster_home = file_relative_path(temp_dir, "prod_dagster_home")
    if not os.path.exists(prod_dagster_home):
        os.mkdir(prod_dagster_home)
    with environ({"DAGSTER_HOME": prod_dagster_home, "DAGSTER_DEPLOYMENT": "prod"}):
        with instance_for_test(
            temp_dir=prod_dagster_home,
        ) as instance:
            yield instance


@contextmanager
def branch_instance(temp_dir):
    dev_dagster_home = file_relative_path(temp_dir, "dev_dagster_home")
    if not os.path.exists(dev_dagster_home):
        os.mkdir(dev_dagster_home)
    with environ({"DAGSTER_HOME": dev_dagster_home, "DAGSTER_DEPLOYMENT": "my-featured-branch"}):
        with instance_for_test(
            temp_dir=dev_dagster_home,
        ) as instance:
            yield instance


@contextmanager
def foo_example_workspace(instance: DagsterInstance):
    with WorkspaceProcessContext(
        instance,
        ModuleTarget(
            module_name="script_to_assets_branching_io_manager",
            attribute=None,
            working_directory=os.path.dirname(__file__),
            location_name="my_repo",
        ),
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


def _materialize_assets(
    instance: DagsterInstance, workspace: WorkspaceRequestContext, asset_keys: List[AssetKey]
) -> DagsterRun:
    all_assets_job = next(
        j
        for j in workspace.get_repository_location("my_repo")
        .get_repository(SINGLETON_REPOSITORY_NAME)
        .get_all_external_jobs()
        if j.name == ASSET_BASE_JOB_PREFIX
    )
    run = instance.create_run_for_pipeline(
        script_to_assets_branching_io_manager.dev_defs.get_job_def(ASSET_BASE_JOB_PREFIX),
        asset_selection=frozenset(asset_keys),
        external_pipeline_origin=all_assets_job.get_external_origin(),
    )

    instance.launch_run(run.run_id, workspace)

    poll_for_finished_run(instance, run.run_id, timeout=60)

    return check.not_none(instance.get_run_by_id(run.run_id))


def test_base(temp_dir, prod_storage, branch_storage):
    assert not os.listdir(prod_storage)
    assert not os.listdir(branch_storage)

    # Ensure we can't materialize the last asset in the branch without
    # it first being materialized in prod
    with branch_instance(temp_dir) as instance:
        with foo_example_workspace(instance) as workspace:
            assert (
                _materialize_assets(
                    instance,
                    workspace,
                    asset_keys=[
                        AssetKey(["process_wordcloud"]),
                    ],
                ).status
                == DagsterRunStatus.FAILURE
            )

    assert not os.listdir(prod_storage)
    assert not os.listdir(branch_storage)

    # Materialize all assets in prod
    with prod_instance(temp_dir) as instance:
        with foo_example_workspace(instance) as workspace:
            assert (
                _materialize_assets(
                    instance,
                    workspace,
                    asset_keys=[
                        AssetKey(["hackernews_source_data"]),
                        AssetKey(["hackernews_wordcloud"]),
                        AssetKey(["process_wordcloud"]),
                    ],
                ).status
                == DagsterRunStatus.SUCCESS
            )

    assert set(os.listdir(prod_storage)) == {
        "hackernews_source_data",
        "hackernews_wordcloud",
        "process_wordcloud",
    }
    assert not os.listdir(branch_storage)

    # Ensure we can materialize the last asset in the branch,
    # which should now read from the prod assets upstream
    with branch_instance(temp_dir) as instance:
        with foo_example_workspace(instance) as workspace:
            assert (
                _materialize_assets(
                    instance,
                    workspace,
                    asset_keys=[
                        AssetKey(["process_wordcloud"]),
                    ],
                ).status
                == DagsterRunStatus.SUCCESS
            )

    assert set(os.listdir(prod_storage)) == {
        "hackernews_source_data",
        "hackernews_wordcloud",
        "process_wordcloud",
    }
    assert set(os.listdir(branch_storage)) == {"process_wordcloud"}
