import pytest
from dagster import check
from dagster.core.code_pointer import ModuleCodePointer
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation.origin import (
    ExternalPipelineOrigin,
    ExternalRepositoryOrigin,
    InProcessRepositoryLocationOrigin,
)
from dagster.core.storage.pipeline_run import (
    IN_PROGRESS_RUN_STATUSES,
    NON_IN_PROGRESS_RUN_STATUSES,
    PipelineRun,
    PipelineRunStatus,
)


def test_queued_pipeline_origin_check():
    fake_pipeline_origin = ExternalPipelineOrigin(
        ExternalRepositoryOrigin(
            InProcessRepositoryLocationOrigin(
                ReconstructableRepository(ModuleCodePointer("fake", "fake"))
            ),
            "foo_repo",
        ),
        "foo",
    )

    PipelineRun(status=PipelineRunStatus.QUEUED, external_pipeline_origin=fake_pipeline_origin)

    with pytest.raises(check.CheckError):
        PipelineRun(status=PipelineRunStatus.QUEUED)

    with pytest.raises(check.CheckError):
        PipelineRun().with_status(PipelineRunStatus.QUEUED)


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
