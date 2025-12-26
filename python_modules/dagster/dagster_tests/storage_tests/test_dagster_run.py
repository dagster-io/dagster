import sys

import dagster as dg
import dagster._check as check
import pytest
from dagster._check import CheckError
from dagster._core.code_pointer import ModuleCodePointer
from dagster._core.origin import (
    DEFAULT_DAGSTER_ENTRY_POINT,
    JobPythonOrigin,
    RepositoryPythonOrigin,
)
from dagster._core.remote_origin import (
    InProcessCodeLocationOrigin,
    RemoteJobOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.storage.dagster_run import (
    IN_PROGRESS_RUN_STATUSES,
    NON_IN_PROGRESS_RUN_STATUSES,
    DagsterRunStatus,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._utils.env import environ


def test_queued_job_origin_check():
    code_pointer = ModuleCodePointer("fake", "fake", working_directory=None)
    fake_job_origin = RemoteJobOrigin(
        RemoteRepositoryOrigin(
            InProcessCodeLocationOrigin(
                LoadableTargetOrigin(
                    executable_path=sys.executable,
                    module_name="fake",
                )
            ),
            "foo_repo",
        ),
        "foo",
    )

    fake_code_origin = JobPythonOrigin(
        job_name="foo",
        repository_origin=RepositoryPythonOrigin(
            sys.executable,
            code_pointer,
            entry_point=DEFAULT_DAGSTER_ENTRY_POINT,
        ),
    )

    dg.DagsterRun(
        job_name="foo",
        status=DagsterRunStatus.QUEUED,
        remote_job_origin=fake_job_origin,
        job_code_origin=fake_code_origin,
    )

    with pytest.raises(check.CheckError):
        dg.DagsterRun(job_name="foo", status=DagsterRunStatus.QUEUED)

    with pytest.raises(check.CheckError):
        dg.DagsterRun(job_name="foo").with_status(DagsterRunStatus.QUEUED)


def test_in_progress_statuses():
    """If this fails, then the dequeuer's statuses are out of sync with all PipelineRunStatuses."""
    for status in dg.DagsterRunStatus:
        in_progress = status in IN_PROGRESS_RUN_STATUSES
        non_in_progress = status in NON_IN_PROGRESS_RUN_STATUSES
        assert in_progress != non_in_progress  # should be in exactly one of the two

    assert len(IN_PROGRESS_RUN_STATUSES) + len(NON_IN_PROGRESS_RUN_STATUSES) == len(
        dg.DagsterRunStatus
    )


def test_runs_filter_supports_nonempty_run_ids():
    assert dg.RunsFilter()
    assert dg.RunsFilter(run_ids=["1234"])

    with pytest.raises(CheckError):
        dg.RunsFilter(run_ids=[])


@pytest.mark.parametrize(
    "env,expected_tags",
    [
        ({}, {"dagster/job": "foo", "dagster/run-id": "a_run_id", "dagster/user": "a_user"}),
        (
            {"DAGSTER_EXECUTION_THE_ATTRIBUTE": "bar"},
            {
                "dagster/the-attribute": "bar",
                "dagster/job": "foo",
                "dagster/run-id": "a_run_id",
                "dagster/user": "a_user",
            },
        ),
        (
            {
                "SUPER_SECRET_ENV_VAR": "super-secret-value",
                "DAGSTER_CLOUD_DEPLOYMENT_NAME": "deployment-name",
                "DAGSTER_CLOUD_GIT_REPO": "git-repo",
                "DAGSTER_CLOUD_GIT_BRANCH": "git-branch",
                "DAGSTER_CLOUD_GIT_SHA": "git-sha",
                "DAGSTER_EXECUTION_THE_ATTRIBUTE": "bar",
                "DAGSTER_EXECUTION_THE_OTHER_ATTRIBUTE": "qux",
            },
            {
                "dagster/the-attribute": "bar",
                "dagster/the-other-attribute": "qux",
                "dagster/deployment-name": "deployment-name",
                "dagster/git-repo": "git-repo",
                "dagster/git-branch": "git-branch",
                "dagster/git-sha": "git-sha",
                "dagster/job": "foo",
                "dagster/run-id": "a_run_id",
                "dagster/user": "a_user",
            },
        ),
    ],
)
def test_dagster_execution_metadata_tags(env: dict[str, str], expected_tags: dict[str, str]):
    with environ(env):
        run = dg.DagsterRun("foo", "a_run_id", tags={"dagster/user": "a_user"})
        assert run.dagster_execution_info == expected_tags
