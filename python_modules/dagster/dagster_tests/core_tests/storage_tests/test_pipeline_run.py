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
from dagster.core.instance import DagsterInstance, InstanceRef
from dagster.core.origin import PipelinePythonOrigin, RepositoryPythonOrigin
from dagster.core.storage.pipeline_run import (
    IN_PROGRESS_RUN_STATUSES,
    NON_IN_PROGRESS_RUN_STATUSES,
    PipelineRun,
    PipelineRunStatus,
    PipelineTarget,
)
from dagster.utils import file_relative_path
from dagster.utils.test import copy_directory


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

    PipelineRun(
        status=PipelineRunStatus.QUEUED,
        external_pipeline_origin=fake_pipeline_origin,
        pipeline_code_origin=fake_code_origin,
    )

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


def test_pipeline_run_target_backcompat():
    src_dir = file_relative_path(__file__, "compat_tests/snapshot_0_12_7_pipeline_name")

    with copy_directory(src_dir) as test_dir:
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))
        runs = instance.get_runs()
        target = runs[0].target
        assert len(runs) == 1
        assert isinstance(target, PipelineTarget)
        assert target.name == "asset_lineage_pipeline"
        assert target.mode == "default"
