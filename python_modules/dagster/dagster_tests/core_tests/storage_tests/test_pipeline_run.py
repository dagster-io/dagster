import pytest
from dagster import check
from dagster.core.code_pointer import ModuleCodePointer
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation.origin import (
    ExternalPipelineOrigin,
    ExternalRepositoryOrigin,
    InProcessRepositoryLocationOrigin,
)
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus


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
