import pytest
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import create_run_for_test, instance_for_test
from dagster.daemon.run_coordinator.queued_run_coordinator_daemon import (
    IN_PROGRESS_STATUSES,
    QueuedRunCoordinatorDaemon,
)
from dagster_tests.api_tests.utils import get_foo_pipeline_handle


@pytest.fixture()
def instance():
    overrides = {
        "run_launcher": {"module": "dagster.core.test_utils", "class": "MockedRunLauncher"},
    }
    with instance_for_test(overrides=overrides) as inst:
        yield inst


def create_run(instance, **kwargs):  # pylint: disable=redefined-outer-name
    with get_foo_pipeline_handle() as pipeline_handle:
        create_run_for_test(
            instance,
            external_pipeline_origin=pipeline_handle.get_external_origin(),
            pipeline_name="foo",
            **kwargs
        )


def get_run_ids(runs_queue):
    return [run.run_id for run in runs_queue]


def test_attempt_to_launch_runs_filter(instance):  # pylint: disable=redefined-outer-name

    create_run(
        instance, run_id="queued-run", status=PipelineRunStatus.QUEUED,
    )

    create_run(
        instance, run_id="non-queued-run", status=PipelineRunStatus.NOT_STARTED,
    )

    coordinator = QueuedRunCoordinatorDaemon(instance, interval_seconds=5, max_concurrent_runs=10)
    coordinator.run_iteration()

    assert get_run_ids(instance.run_launcher.queue()) == ["queued-run"]


def test_attempt_to_launch_runs_no_queued(instance):  # pylint: disable=redefined-outer-name

    create_run(
        instance, run_id="queued-run", status=PipelineRunStatus.STARTED,
    )
    create_run(
        instance, run_id="non-queued-run", status=PipelineRunStatus.NOT_STARTED,
    )

    coordinator = QueuedRunCoordinatorDaemon(instance, interval_seconds=5, max_concurrent_runs=10)
    coordinator.run_iteration()

    assert instance.run_launcher.queue() == []


@pytest.mark.parametrize(
    "num_in_progress_runs", [0, 1, 3, 4, 5],
)
def test_get_queued_runs_max_runs(
    instance, num_in_progress_runs
):  # pylint: disable=redefined-outer-name
    max_runs = 4

    # fill run store with ongoing runs
    in_progress_run_ids = ["in_progress-run-{}".format(i) for i in range(num_in_progress_runs)]
    for i, run_id in enumerate(in_progress_run_ids):
        # get a selection of all in progress statuses
        status = IN_PROGRESS_STATUSES[i % len(IN_PROGRESS_STATUSES)]
        create_run(
            instance, run_id=run_id, status=status,
        )

    # add more queued runs than should be launched
    queued_run_ids = ["queued-run-{}".format(i) for i in range(max_runs + 1)]
    for run_id in queued_run_ids:
        create_run(
            instance, run_id=run_id, status=PipelineRunStatus.QUEUED,
        )

    coordinator = QueuedRunCoordinatorDaemon(
        instance, interval_seconds=5, max_concurrent_runs=max_runs,
    )
    coordinator.run_iteration()

    assert len(instance.run_launcher.queue()) == max(0, max_runs - num_in_progress_runs)
