import os

import pytest

from dagster import DagsterInstance, execute_pipeline, job, op, reconstructable, repository
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.tags import RESUME_RETRY_TAG
from dagster.core.test_utils import (
    environ,
    instance_for_test,
    poll_for_finished_run,
    step_did_not_run,
    step_succeeded,
)
from dagster.core.workspace.context import WorkspaceProcessContext
from dagster.core.workspace.load_target import PythonFileTarget
from dagster.seven import get_system_temp_directory

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


@job
def conditional_fail_job():
    after_failure(conditional_fail(before_failure()))


@repository
def repo():
    return [conditional_fail_job]


@pytest.fixture
def instance():
    with instance_for_test() as instance:
        yield instance


@pytest.fixture
def workspace(instance):
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


def test_create_reexecuted_run_from_failure(instance: DagsterInstance, workspace):
    # trigger failure in the conditionally_fail op
    with environ({CONDITIONAL_FAIL_ENV: "1"}):
        result = execute_pipeline(reconstructable(conditional_fail_job), instance=instance)

    assert not result.success

    parent_run = instance.get_run_by_id(result.run_id)
    repository_location = workspace.get_repository_location("repo_loc")
    external_pipeline = repository_location.get_repository("repo").get_full_external_pipeline(
        "conditional_fail_job"
    )

    run = instance.create_reexecuted_run_from_failure(
        parent_run, repository_location, external_pipeline
    )

    assert run.tags[RESUME_RETRY_TAG] == "true"
    assert set(run.step_keys_to_execute) == {"conditional_fail", "after_failure"}  # type: ignore

    instance.launch_run(run.run_id, workspace)
    run = poll_for_finished_run(instance, run.run_id)

    assert run.status == PipelineRunStatus.SUCCESS
    assert step_did_not_run(instance, run, "before_failure")
    assert step_succeeded(instance, run, "conditional_fail")
    assert step_succeeded(instance, run, "after_failure")
