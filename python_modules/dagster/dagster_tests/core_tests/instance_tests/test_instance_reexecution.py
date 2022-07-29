import os

import pytest

from dagster import DagsterInstance, job, op, reconstructable, repository
from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.storage.pipeline_run import PipelineRunStatus
from dagster._core.storage.tags import RESUME_RETRY_TAG
from dagster._core.test_utils import (
    environ,
    instance_for_test,
    poll_for_finished_run,
    step_did_not_run,
    step_succeeded,
)
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import PythonFileTarget
from dagster._legacy import execute_pipeline

CONDITIONAL_FAIL_ENV = "DAGSTER_CONDIIONAL_FAIL"


@op
def before_failure():
    return "hello"


@op
def conditional_fail(_, input_value):
    if os.environ.get(CONDITIONAL_FAIL_ENV):
        raise Exception("env set, failing!")

    return input_value


@op
def after_failure(_, input_value):
    return input_value


@job(tags={"foo": "bar"})
def conditional_fail_job():
    after_failure(conditional_fail(before_failure()))


@repository
def repo():
    return [conditional_fail_job]


@pytest.fixture(name="instance", scope="module")
def instance_fixture():
    with instance_for_test() as instance:
        yield instance


@pytest.fixture(name="workspace", scope="module")
def workspace_fixture(instance):
    with WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=__file__,
            attribute=None,
            working_directory=None,
            location_name="repo_loc",
        ),
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


@pytest.fixture(name="repo_location", scope="module")
def repo_location_fixture(workspace):
    return workspace.get_repository_location("repo_loc")


@pytest.fixture(name="external_pipeline", scope="module")
def external_pipeline_fixture(repo_location):
    return repo_location.get_repository("repo").get_full_external_pipeline("conditional_fail_job")


@pytest.fixture(name="failed_run", scope="module")
def failed_run_fixture(instance):
    # trigger failure in the conditionally_fail op
    with environ({CONDITIONAL_FAIL_ENV: "1"}):
        result = execute_pipeline(
            reconstructable(conditional_fail_job),
            instance=instance,
            tags={"fizz": "buzz", "foo": "not bar!"},
        )

    assert not result.success

    return instance.get_run_by_id(result.run_id)


def test_create_reexecuted_run_from_failure(
    instance: DagsterInstance,
    workspace,
    repo_location,
    external_pipeline,
    failed_run,
):
    run = instance.create_reexecuted_run(
        failed_run, repo_location, external_pipeline, ReexecutionStrategy.FROM_FAILURE
    )

    assert run.tags[RESUME_RETRY_TAG] == "true"
    assert set(run.step_keys_to_execute) == {"conditional_fail", "after_failure"}  # type: ignore

    instance.launch_run(run.run_id, workspace)
    run = poll_for_finished_run(instance, run.run_id)

    assert run.status == PipelineRunStatus.SUCCESS
    assert step_did_not_run(instance, run, "before_failure")
    assert step_succeeded(instance, run, "conditional_fail")
    assert step_succeeded(instance, run, "after_failure")


def test_create_reexecuted_run_from_failure_tags(
    instance: DagsterInstance,
    repo_location,
    external_pipeline,
    failed_run,
):
    run = instance.create_reexecuted_run(
        failed_run, repo_location, external_pipeline, ReexecutionStrategy.FROM_FAILURE
    )

    assert run.tags["foo"] == "bar"
    assert "fizz" not in run.tags

    run = instance.create_reexecuted_run(
        failed_run,
        repo_location,
        external_pipeline,
        ReexecutionStrategy.FROM_FAILURE,
        use_parent_run_tags=True,
    )

    assert run.tags["foo"] == "not bar!"
    assert run.tags["fizz"] == "buzz"

    run = instance.create_reexecuted_run(
        failed_run,
        repo_location,
        external_pipeline,
        ReexecutionStrategy.FROM_FAILURE,
        use_parent_run_tags=True,
        extra_tags={"fizz": "not buzz!!"},
    )

    assert run.tags["foo"] == "not bar!"
    assert run.tags["fizz"] == "not buzz!!"


def test_create_reexecuted_run_all_steps(
    instance: DagsterInstance, workspace, repo_location, external_pipeline, failed_run
):
    run = instance.create_reexecuted_run(
        failed_run, repo_location, external_pipeline, ReexecutionStrategy.ALL_STEPS
    )

    assert RESUME_RETRY_TAG not in run.tags

    instance.launch_run(run.run_id, workspace)
    run = poll_for_finished_run(instance, run.run_id)

    assert run.status == PipelineRunStatus.SUCCESS
    assert step_succeeded(instance, run, "before_failure")
    assert step_succeeded(instance, run, "conditional_fail")
    assert step_succeeded(instance, run, "after_failure")
