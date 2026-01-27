import sys

import dagster as dg
import dagster._check as check
import pytest
from dagster._check import CheckError
from dagster._core.code_pointer import ModuleCodePointer
from dagster._core.definitions.partitions.definition import (
    HourlyPartitionsDefinition,
    StaticPartitionsDefinition,
)
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
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    PARTITION_NAME_TAG,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin


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
    "test_case, partitions_def, run_kwargs, expected_keys",
    [
        # Case 1: stored subset - directly stored partitions_subset returns stored subset
        (
            "stored_subset",
            HourlyPartitionsDefinition(start_date="2024-01-01-00:00"),
            {
                "partitions_subset": HourlyPartitionsDefinition(start_date="2024-01-01-00:00")
                .subset_with_partition_keys(["2024-01-01-00:00", "2024-01-01-02:00"])
                .to_serializable_subset()
            },
            ["2024-01-01-00:00", "2024-01-01-02:00"],
        ),
        # Case 2: single tag - PARTITION_NAME_TAG returns single partition
        (
            "single_tag",
            StaticPartitionsDefinition(["a", "b", "c"]),
            {"tags": {PARTITION_NAME_TAG: "b"}},
            ["b"],
        ),
        # Case 3: range tags - ASSET_PARTITION_RANGE_START_TAG + END_TAG returns range
        (
            "range_tags",
            StaticPartitionsDefinition(["a", "b", "c", "d"]),
            {
                "tags": {
                    ASSET_PARTITION_RANGE_START_TAG: "b",
                    ASSET_PARTITION_RANGE_END_TAG: "d",
                }
            },
            ["b", "c", "d"],
        ),
        # Case 4: unpartitioned - no partition info returns None
        (
            "unpartitioned",
            StaticPartitionsDefinition(["a", "b", "c"]),
            {},
            None,
        ),
    ],
)
def test_get_resolved_partitions_subset(test_case, partitions_def, run_kwargs, expected_keys):
    """Test that get_resolved_partitions_subset correctly resolves partitions from various sources."""
    run = dg.DagsterRun(job_name="test", **run_kwargs)
    result = run.get_resolved_partitions_subset_for_events(partitions_def)

    if expected_keys is None:
        assert result is None
    else:
        assert result is not None
        assert set(result.get_partition_keys()) == set(expected_keys)
