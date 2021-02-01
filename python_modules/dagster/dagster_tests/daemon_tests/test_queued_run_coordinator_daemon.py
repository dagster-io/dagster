# pylint: disable=redefined-outer-name

import threading
import uuid

import pytest
from dagster.core.host_representation.handle import RepositoryLocationHandle
from dagster.core.storage.pipeline_run import IN_PROGRESS_RUN_STATUSES, PipelineRunStatus
from dagster.core.storage.tags import PRIORITY_TAG
from dagster.core.test_utils import create_run_for_test, instance_for_test
from dagster.daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon
from dagster_tests.api_tests.utils import get_foo_pipeline_handle


@pytest.fixture()
def instance():
    overrides = {
        "run_launcher": {"module": "dagster.core.test_utils", "class": "MockedRunLauncher"},
    }
    with instance_for_test(overrides=overrides) as inst:
        yield inst


def create_run(instance, **kwargs):
    with get_foo_pipeline_handle() as pipeline_handle:
        create_run_for_test(
            instance,
            external_pipeline_origin=pipeline_handle.get_external_origin(),
            pipeline_name="foo",
            **kwargs,
        )


def get_run_ids(runs_queue):
    return [run.run_id for run in runs_queue]


def test_attempt_to_launch_runs_filter(instance):

    create_run(
        instance, run_id="queued-run", status=PipelineRunStatus.QUEUED,
    )

    create_run(
        instance, run_id="non-queued-run", status=PipelineRunStatus.NOT_STARTED,
    )

    coordinator = QueuedRunCoordinatorDaemon(
        instance,
        interval_seconds=5,
        max_concurrent_runs=10,
        daemon_uuid=str(uuid.uuid4()),
        thread_shutdown_event=threading.Event(),
    )
    list(coordinator.run_iteration())

    assert get_run_ids(instance.run_launcher.queue()) == ["queued-run"]


def test_attempt_to_launch_runs_no_queued(instance):

    create_run(
        instance, run_id="queued-run", status=PipelineRunStatus.STARTED,
    )
    create_run(
        instance, run_id="non-queued-run", status=PipelineRunStatus.NOT_STARTED,
    )

    coordinator = QueuedRunCoordinatorDaemon(
        instance,
        interval_seconds=5,
        max_concurrent_runs=10,
        daemon_uuid=str(uuid.uuid4()),
        thread_shutdown_event=threading.Event(),
    )
    list(coordinator.run_iteration())

    assert instance.run_launcher.queue() == []


@pytest.mark.parametrize(
    "num_in_progress_runs", [0, 1, 3, 4, 5],
)
def test_get_queued_runs_max_runs(instance, num_in_progress_runs):
    max_runs = 4

    # fill run store with ongoing runs
    in_progress_run_ids = ["in_progress-run-{}".format(i) for i in range(num_in_progress_runs)]
    for i, run_id in enumerate(in_progress_run_ids):
        # get a selection of all in progress statuses
        status = IN_PROGRESS_RUN_STATUSES[i % len(IN_PROGRESS_RUN_STATUSES)]
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
        instance,
        interval_seconds=5,
        max_concurrent_runs=max_runs,
        daemon_uuid=str(uuid.uuid4()),
        thread_shutdown_event=threading.Event(),
    )
    list(coordinator.run_iteration())

    assert len(instance.run_launcher.queue()) == max(0, max_runs - num_in_progress_runs)


def test_priority(instance):
    create_run(instance, run_id="default-pri-run", status=PipelineRunStatus.QUEUED)
    create_run(
        instance, run_id="low-pri-run", status=PipelineRunStatus.QUEUED, tags={PRIORITY_TAG: "-1"},
    )
    create_run(
        instance, run_id="hi-pri-run", status=PipelineRunStatus.QUEUED, tags={PRIORITY_TAG: "3"},
    )

    coordinator = QueuedRunCoordinatorDaemon(
        instance,
        interval_seconds=5,
        max_concurrent_runs=10,
        daemon_uuid=str(uuid.uuid4()),
        thread_shutdown_event=threading.Event(),
    )
    list(coordinator.run_iteration())

    assert get_run_ids(instance.run_launcher.queue()) == [
        "hi-pri-run",
        "default-pri-run",
        "low-pri-run",
    ]


def test_priority_on_malformed_tag(instance):
    create_run(
        instance,
        run_id="bad-pri-run",
        status=PipelineRunStatus.QUEUED,
        tags={PRIORITY_TAG: "foobar"},
    )

    coordinator = QueuedRunCoordinatorDaemon(
        instance,
        interval_seconds=5,
        max_concurrent_runs=10,
        daemon_uuid=str(uuid.uuid4()),
        thread_shutdown_event=threading.Event(),
    )
    list(coordinator.run_iteration())

    assert get_run_ids(instance.run_launcher.queue()) == ["bad-pri-run"]


def test_tag_limits(instance):
    create_run(
        instance, run_id="tiny-1", status=PipelineRunStatus.QUEUED, tags={"database": "tiny"},
    )
    create_run(
        instance, run_id="tiny-2", status=PipelineRunStatus.QUEUED, tags={"database": "tiny"},
    )
    create_run(
        instance, run_id="large-1", status=PipelineRunStatus.QUEUED, tags={"database": "large"},
    )
    coordinator = QueuedRunCoordinatorDaemon(
        instance,
        interval_seconds=5,
        max_concurrent_runs=10,
        tag_concurrency_limits=[{"key": "database", "value": "tiny", "limit": 1}],
        daemon_uuid=str(uuid.uuid4()),
        thread_shutdown_event=threading.Event(),
    )
    list(coordinator.run_iteration())

    assert get_run_ids(instance.run_launcher.queue()) == ["tiny-1", "large-1"]


def test_multiple_tag_limits(instance):
    create_run(
        instance,
        run_id="run-1",
        status=PipelineRunStatus.QUEUED,
        tags={"database": "tiny", "user": "johann"},
    )
    create_run(
        instance, run_id="run-2", status=PipelineRunStatus.QUEUED, tags={"database": "tiny"},
    )
    create_run(
        instance, run_id="run-3", status=PipelineRunStatus.QUEUED, tags={"user": "johann"},
    )
    create_run(
        instance, run_id="run-4", status=PipelineRunStatus.QUEUED, tags={"user": "johann"},
    )
    coordinator = QueuedRunCoordinatorDaemon(
        instance,
        interval_seconds=5,
        max_concurrent_runs=10,
        tag_concurrency_limits=[
            {"key": "database", "value": "tiny", "limit": 1},
            {"key": "user", "value": "johann", "limit": 2},
        ],
        daemon_uuid=str(uuid.uuid4()),
        thread_shutdown_event=threading.Event(),
    )
    list(coordinator.run_iteration())

    assert get_run_ids(instance.run_launcher.queue()) == ["run-1", "run-3"]


def test_overlapping_tag_limits(instance):
    create_run(
        instance, run_id="run-1", status=PipelineRunStatus.QUEUED, tags={"foo": "bar"},
    )
    create_run(
        instance, run_id="run-2", status=PipelineRunStatus.QUEUED, tags={"foo": "bar"},
    )
    create_run(
        instance, run_id="run-3", status=PipelineRunStatus.QUEUED, tags={"foo": "other"},
    )
    create_run(
        instance, run_id="run-4", status=PipelineRunStatus.QUEUED, tags={"foo": "other"},
    )
    coordinator = QueuedRunCoordinatorDaemon(
        instance,
        interval_seconds=5,
        max_concurrent_runs=10,
        tag_concurrency_limits=[
            {"key": "foo", "limit": 2},
            {"key": "foo", "value": "bar", "limit": 1},
        ],
        daemon_uuid=str(uuid.uuid4()),
        thread_shutdown_event=threading.Event(),
    )
    list(coordinator.run_iteration())

    assert get_run_ids(instance.run_launcher.queue()) == ["run-1", "run-3"]


def test_location_handles_reused(instance, monkeypatch):
    """
    verifies that only one repository location is created when two queued runs from the same
    location are dequeued in the same iteration
    """

    create_run(
        instance, run_id="queued-run", status=PipelineRunStatus.QUEUED,
    )

    create_run(
        instance, run_id="queued-run-2", status=PipelineRunStatus.QUEUED,
    )

    original_method = RepositoryLocationHandle.create_from_repository_location_origin
    method_calls = []

    def mocked_create_location_handle(origin):
        method_calls.append(origin)
        return original_method(origin)

    monkeypatch.setattr(
        RepositoryLocationHandle,
        "create_from_repository_location_origin",
        mocked_create_location_handle,
    )

    coordinator = QueuedRunCoordinatorDaemon(
        instance,
        interval_seconds=5,
        max_concurrent_runs=10,
        daemon_uuid=str(uuid.uuid4()),
        thread_shutdown_event=threading.Event(),
    )
    list(coordinator.run_iteration())

    assert get_run_ids(instance.run_launcher.queue()) == ["queued-run", "queued-run-2"]
    assert len(method_calls) == 1
