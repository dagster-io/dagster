import sys

import pytest
from dagster import check
from dagster.core.code_pointer import ModuleCodePointer
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation.origin import (
    ExternalPipelineOrigin,
    ExternalRepositoryOrigin,
    InProcessRepositoryLocationOrigin,
)
from dagster.core.origin import PipelinePythonOrigin, RepositoryPythonOrigin
from dagster.core.storage.dagster_run import (
    IN_PROGRESS_RUN_STATUSES,
    NON_IN_PROGRESS_RUN_STATUSES,
    DagsterRun,
    DagsterRunStatus,
)


def test_queued_pipeline_origin_check():

    code_pointer = ModuleCodePointer("fake", "fake")
    fake_pipeline_origin = ExternalPipelineOrigin(
        ExternalRepositoryOrigin(
            InProcessRepositoryLocationOrigin(ReconstructableRepository(code_pointer)),
            "foo_repo",
        ),
        "foo",
    )

    fake_code_origin = PipelinePythonOrigin(
        pipeline_name="foo",
        repository_origin=RepositoryPythonOrigin(
            sys.executable,
            code_pointer,
        ),
    )

    DagsterRun(
        status=DagsterRunStatus.QUEUED,
        external_pipeline_origin=fake_pipeline_origin,
        pipeline_code_origin=fake_code_origin,
    )

    with pytest.raises(check.CheckError):
        DagsterRun(status=DagsterRunStatus.QUEUED)

    with pytest.raises(check.CheckError):
        DagsterRun().with_status(DagsterRunStatus.QUEUED)


def test_in_progress_statuses():
    """
    If this fails, then the dequeuer's statuses are out of sync with all DagsterRunStatuses.
    """
    for status in DagsterRunStatus:
        in_progress = status in IN_PROGRESS_RUN_STATUSES
        non_in_progress = status in NON_IN_PROGRESS_RUN_STATUSES
        assert in_progress != non_in_progress  # should be in exactly one of the two

    assert len(IN_PROGRESS_RUN_STATUSES) + len(NON_IN_PROGRESS_RUN_STATUSES) == len(
        DagsterRunStatus
    )
