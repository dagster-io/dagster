import sys

import dagster._check as check
import pytest
from dagster._check import CheckError
from dagster._core.code_pointer import ModuleCodePointer
from dagster._core.definitions.decorators.op_decorator import op
from dagster._core.events import DagsterEventType
from dagster._core.host_representation.origin import (
    ExternalJobOrigin,
    ExternalRepositoryOrigin,
    InProcessCodeLocationOrigin,
)
from dagster._core.instance_for_test import instance_for_test
from dagster._core.origin import (
    DEFAULT_DAGSTER_ENTRY_POINT,
    JobPythonOrigin,
    RepositoryPythonOrigin,
)
from dagster._core.storage.dagster_run import (
    IN_PROGRESS_RUN_STATUSES,
    NON_IN_PROGRESS_RUN_STATUSES,
    DagsterRun,
    DagsterRunStatus,
    RunsFilter,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._serdes import deserialize_value, serialize_value
from dagster._utils.test import wrap_op_in_graph_and_execute


def test_queued_job_origin_check():
    code_pointer = ModuleCodePointer("fake", "fake", working_directory=None)
    fake_job_origin = ExternalJobOrigin(
        ExternalRepositoryOrigin(
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

    DagsterRun(
        job_name="foo",
        status=DagsterRunStatus.QUEUED,
        external_job_origin=fake_job_origin,
        job_code_origin=fake_code_origin,
    )

    with pytest.raises(check.CheckError):
        DagsterRun(job_name="foo", status=DagsterRunStatus.QUEUED)

    with pytest.raises(check.CheckError):
        DagsterRun(job_name="foo").with_status(DagsterRunStatus.QUEUED)


def test_in_progress_statuses():
    """If this fails, then the dequeuer's statuses are out of sync with all PipelineRunStatuses."""
    for status in DagsterRunStatus:
        in_progress = status in IN_PROGRESS_RUN_STATUSES
        non_in_progress = status in NON_IN_PROGRESS_RUN_STATUSES
        assert in_progress != non_in_progress  # should be in exactly one of the two

    assert len(IN_PROGRESS_RUN_STATUSES) + len(NON_IN_PROGRESS_RUN_STATUSES) == len(
        DagsterRunStatus
    )


def test_runs_filter_supports_nonempty_run_ids():
    assert RunsFilter()
    assert RunsFilter(run_ids=["1234"])

    with pytest.raises(CheckError):
        RunsFilter(run_ids=[])


def test_serialize_runs_filter():
    deserialize_value(serialize_value(RunsFilter()), RunsFilter)


def test_dagster_run_events():
    @op
    def foo():
        return 1

    with instance_for_test() as instance:
        result = wrap_op_in_graph_and_execute(foo, instance=instance)
        events = result.dagster_run.get_event_records(instance)
        assert any(
            event.event_log_entry.get_dagster_event().event_type
            == DagsterEventType.PIPELINE_SUCCESS
            for event in events
        )
