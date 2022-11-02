import sys

import pytest

import dagster._check as check
from dagster._check import CheckError
from dagster._core.code_pointer import ModuleCodePointer
from dagster._core.host_representation.origin import (
    ExternalPipelineOrigin,
    ExternalRepositoryOrigin,
    InProcessRepositoryLocationOrigin,
)
from dagster._core.origin import (
    DEFAULT_DAGSTER_ENTRY_POINT,
    PipelinePythonOrigin,
    RepositoryPythonOrigin,
)
from dagster._core.storage.pipeline_run import (
    IN_PROGRESS_RUN_STATUSES,
    NON_IN_PROGRESS_RUN_STATUSES,
    PipelineRun,
    PipelineRunStatus,
    RunsFilter,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._serdes import deserialize_as, serialize_dagster_namedtuple


def test_queued_pipeline_origin_check():
    code_pointer = ModuleCodePointer("fake", "fake", working_directory=None)
    fake_pipeline_origin = ExternalPipelineOrigin(
        ExternalRepositoryOrigin(
            InProcessRepositoryLocationOrigin(
                LoadableTargetOrigin(
                    executable_path=sys.executable,
                    module_name="fake",
                )
            ),
            "foo_repo",
        ),
        "foo",
    )

    fake_code_origin = PipelinePythonOrigin(
        pipeline_name="foo",
        repository_origin=RepositoryPythonOrigin(
            sys.executable,
            code_pointer,
            entry_point=DEFAULT_DAGSTER_ENTRY_POINT,
        ),
    )

    PipelineRun(
        pipeline_name="foo",
        status=PipelineRunStatus.QUEUED,
        external_pipeline_origin=fake_pipeline_origin,
        pipeline_code_origin=fake_code_origin,
    )

    with pytest.raises(check.CheckError):
        PipelineRun(pipeline_name="foo", status=PipelineRunStatus.QUEUED)

    with pytest.raises(check.CheckError):
        PipelineRun(pipeline_name="foo").with_status(PipelineRunStatus.QUEUED)


def test_in_progress_statuses():
    """
    If this fails, then the dequeuer's statuses are out of sync with all PipelineRunStatuses.
    """
    for status in PipelineRunStatus:
        in_progress = status in IN_PROGRESS_RUN_STATUSES
        non_in_progress = status in NON_IN_PROGRESS_RUN_STATUSES
        assert in_progress != non_in_progress  # should be in exactly one of the two

    assert len(IN_PROGRESS_RUN_STATUSES) + len(NON_IN_PROGRESS_RUN_STATUSES) == len(
        PipelineRunStatus
    )


def test_runs_filter_supports_nonempty_run_ids():
    assert RunsFilter()
    assert RunsFilter(run_ids=["1234"])

    with pytest.raises(CheckError):
        RunsFilter(run_ids=[])


def test_serialize_runs_filter():
    deserialize_as(serialize_dagster_namedtuple(RunsFilter()), RunsFilter)
