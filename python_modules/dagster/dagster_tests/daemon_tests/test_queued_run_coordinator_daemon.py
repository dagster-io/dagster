# pylint: disable=redefined-outer-name

import time
from contextlib import contextmanager

import pytest
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.host_representation.repository_location import GrpcServerRepositoryLocation
from dagster._core.storage.pipeline_run import IN_PROGRESS_RUN_STATUSES, DagsterRunStatus
from dagster._core.storage.tags import PRIORITY_TAG
from dagster._core.test_utils import (
    create_run_for_test,
    create_test_daemon_workspace_context,
    instance_for_test,
)
from dagster._core.workspace.load_target import EmptyWorkspaceTarget
from dagster._daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon

from dagster_tests.api_tests.utils import get_foo_job_handle


@contextmanager
def instance_for_queued_run_coordinator(**kwargs):
    overrides = {
        "run_coordinator": {
            "module": "dagster._core.run_coordinator",
            "class": "QueuedRunCoordinator",
            "config": {**kwargs},
        },
        "run_launcher": {
            "module": "dagster._core.test_utils",
            "class": "MockedRunLauncher",
            "config": {
                "bad_run_ids": ["bad-run"],
                "bad_user_code_run_ids": ["bad-user-code-run"],
            },
        },
    }

    with instance_for_test(overrides=overrides) as instance:
        yield instance


@pytest.fixture(name="instance")
def instance_fixture():
    with instance_for_queued_run_coordinator(max_concurrent_runs=10) as instance:
        yield instance


@pytest.fixture(name="daemon")
def daemon_fixture():
    return QueuedRunCoordinatorDaemon(interval_seconds=1)


@pytest.fixture(name="workspace_context")
def workspace_fixture(instance):
    with create_test_daemon_workspace_context(
        workspace_load_target=EmptyWorkspaceTarget(), instance=instance
    ) as workspace_context:
        yield workspace_context


@pytest.fixture(scope="module")
def pipeline_handle():
    with get_foo_job_handle() as handle:
        yield handle


@pytest.fixture(scope="module")
def other_location_pipeline_handle(pipeline_handle):
    return pipeline_handle._replace(
        repository_handle=pipeline_handle.repository_handle._replace(
            repository_location_origin=pipeline_handle.repository_handle.repository_location_origin._replace(
                location_name="other_location_name"
            )
        )
    )


def create_run(instance, pipeline_handle, **kwargs):
    create_run_for_test(
        instance,
        external_pipeline_origin=pipeline_handle.get_external_origin(),
        pipeline_code_origin=pipeline_handle.get_python_origin(),
        pipeline_name="foo",
        **kwargs,
    )


def create_queued_run(instance, pipeline_handle, **kwargs):
    run = create_run_for_test(
        instance,
        external_pipeline_origin=pipeline_handle.get_external_origin(),
        pipeline_code_origin=pipeline_handle.get_python_origin(),
        pipeline_name="foo",
        status=DagsterRunStatus.NOT_STARTED,
        **kwargs,
    )
    enqueued_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_ENQUEUED.value,
        pipeline_name=run.pipeline_name,
    )
    instance.report_dagster_event(enqueued_event, run_id=run.run_id)
    return instance.get_run_by_id(run.run_id)


def get_run_ids(runs_queue):
    return [run.run_id for run in runs_queue]


def test_attempt_to_launch_runs_filter(instance, workspace_context, daemon, pipeline_handle):
    create_queued_run(
        instance,
        pipeline_handle,
        run_id="queued-run",
    )
    create_run(
        instance,
        pipeline_handle,
        run_id="non-queued-run",
        status=DagsterRunStatus.NOT_STARTED,
    )

    list(daemon.run_iteration(workspace_context))

    assert get_run_ids(instance.run_launcher.queue()) == ["queued-run"]


def test_attempt_to_launch_runs_no_queued(instance, pipeline_handle, workspace_context, daemon):
    create_run(
        instance,
        pipeline_handle,
        run_id="queued-run",
        status=DagsterRunStatus.STARTED,
    )
    create_run(
        instance,
        pipeline_handle,
        run_id="non-queued-run",
        status=DagsterRunStatus.NOT_STARTED,
    )

    list(daemon.run_iteration(workspace_context))

    assert instance.run_launcher.queue() == []


@pytest.mark.parametrize(
    "num_in_progress_runs",
    [0, 1, 5],
)
@pytest.mark.parametrize(
    "use_threads",
    [False, True],
)
def test_get_queued_runs_max_runs(
    num_in_progress_runs,
    use_threads,
    pipeline_handle,
    workspace_context,
    daemon,
):
    max_runs = 4
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=max_runs, dequeue_use_threads=use_threads
    ) as instance:
        bounded_ctx = workspace_context.copy_for_test_instance(instance)
        # fill run store with ongoing runs
        in_progress_run_ids = ["in_progress-run-{}".format(i) for i in range(num_in_progress_runs)]
        for i, run_id in enumerate(in_progress_run_ids):
            # get a selection of all in progress statuses
            status = IN_PROGRESS_RUN_STATUSES[i % len(IN_PROGRESS_RUN_STATUSES)]
            create_run(
                instance,
                pipeline_handle,
                run_id=run_id,
                status=status,
            )

        # add more queued runs than should be launched
        queued_run_ids = ["queued-run-{}".format(i) for i in range(max_runs + 1)]
        for run_id in queued_run_ids:
            create_queued_run(
                instance,
                pipeline_handle,
                run_id=run_id,
            )

        list(daemon.run_iteration(bounded_ctx))

        assert len(instance.run_launcher.queue()) == max(0, max_runs - num_in_progress_runs)


@pytest.mark.parametrize(
    "use_threads",
    [False, True],
)
def test_disable_max_concurrent_runs_limit(use_threads, workspace_context, pipeline_handle, daemon):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=-1, dequeue_use_threads=use_threads
    ) as instance:
        bounded_ctx = workspace_context.copy_for_test_instance(instance)

        # create ongoing runs
        in_progress_run_ids = ["in_progress-run-{}".format(i) for i in range(5)]
        for i, run_id in enumerate(in_progress_run_ids):
            # get a selection of all in progress statuses
            status = IN_PROGRESS_RUN_STATUSES[i % len(IN_PROGRESS_RUN_STATUSES)]
            create_run(
                instance,
                pipeline_handle,
                run_id=run_id,
                status=status,
            )

        # add more queued runs
        queued_run_ids = ["queued-run-{}".format(i) for i in range(6)]
        for run_id in queued_run_ids:
            create_queued_run(
                instance,
                pipeline_handle,
                run_id=run_id,
            )

        list(daemon.run_iteration(bounded_ctx))

        assert len(instance.run_launcher.queue()) == 6


def test_priority(instance, workspace_context, pipeline_handle, daemon):
    create_run(instance, pipeline_handle, run_id="default-pri-run", status=DagsterRunStatus.QUEUED)
    create_queued_run(
        instance,
        pipeline_handle,
        run_id="low-pri-run",
        tags={PRIORITY_TAG: "-1"},
    )
    create_queued_run(
        instance,
        pipeline_handle,
        run_id="hi-pri-run",
        tags={PRIORITY_TAG: "3"},
    )

    list(daemon.run_iteration(workspace_context))

    assert get_run_ids(instance.run_launcher.queue()) == [
        "hi-pri-run",
        "default-pri-run",
        "low-pri-run",
    ]


def test_priority_on_malformed_tag(instance, workspace_context, pipeline_handle, daemon):
    create_queued_run(
        instance,
        pipeline_handle,
        run_id="bad-pri-run",
        tags={PRIORITY_TAG: "foobar"},
    )

    list(daemon.run_iteration(workspace_context))

    assert get_run_ids(instance.run_launcher.queue()) == ["bad-pri-run"]


@pytest.mark.parametrize(
    "use_threads",
    [False, True],
)
def test_tag_limits(use_threads, workspace_context, pipeline_handle, daemon):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        tag_concurrency_limits=[{"key": "database", "value": "tiny", "limit": 1}],
        dequeue_use_threads=use_threads,
    ) as instance:
        bounded_ctx = workspace_context.copy_for_test_instance(instance)

        create_queued_run(
            instance,
            pipeline_handle,
            run_id="tiny-1",
            tags={"database": "tiny"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="tiny-2",
            tags={"database": "tiny"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="large-1",
            tags={"database": "large"},
        )

        list(daemon.run_iteration(bounded_ctx))

        # exact order non-deterministic due to threaded dequeue
        assert set(get_run_ids(instance.run_launcher.queue())) == {"tiny-1", "large-1"}


@pytest.mark.parametrize(
    "use_threads",
    [False, True],
)
def test_tag_limits_just_key(use_threads, workspace_context, pipeline_handle, daemon):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        tag_concurrency_limits=[
            {"key": "database", "value": {"applyLimitPerUniqueValue": False}, "limit": 2}
        ],
        dequeue_use_threads=use_threads,
    ) as instance:
        bounded_ctx = workspace_context.copy_for_test_instance(instance)

        create_queued_run(
            instance,
            pipeline_handle,
            run_id="tiny-1",
            tags={"database": "tiny"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="tiny-2",
            tags={"database": "tiny"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="large-1",
            tags={"database": "large"},
        )

        list(daemon.run_iteration(bounded_ctx))

        # exact order non-deterministic due to threaded dequeue
        assert set(get_run_ids(instance.run_launcher.queue())) == {"tiny-1", "tiny-2"}


@pytest.mark.parametrize(
    "use_threads",
    [False, True],
)
def test_multiple_tag_limits(
    use_threads,
    workspace_context,
    daemon,
    pipeline_handle,
):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        tag_concurrency_limits=[
            {"key": "database", "value": "tiny", "limit": 1},
            {"key": "user", "value": "johann", "limit": 2},
        ],
        dequeue_use_threads=use_threads,
    ) as instance:
        bounded_ctx = workspace_context.copy_for_test_instance(instance)

        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-1",
            tags={"database": "tiny", "user": "johann"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-2",
            tags={"database": "tiny"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-3",
            tags={"user": "johann"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-4",
            tags={"user": "johann"},
        )

        list(daemon.run_iteration(bounded_ctx))

        # exact order non-deterministic due to threaded dequeue
        assert set(get_run_ids(instance.run_launcher.queue())) == {"run-1", "run-3"}


@pytest.mark.parametrize(
    "use_threads",
    [False, True],
)
def test_overlapping_tag_limits(use_threads, workspace_context, daemon, pipeline_handle):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        tag_concurrency_limits=[
            {"key": "foo", "limit": 2},
            {"key": "foo", "value": "bar", "limit": 1},
        ],
        dequeue_use_threads=use_threads,
    ) as instance:
        bounded_ctx = workspace_context.copy_for_test_instance(instance)

        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-1",
            tags={"foo": "bar"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-2",
            tags={"foo": "bar"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-3",
            tags={"foo": "other"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-4",
            tags={"foo": "other"},
        )

        list(daemon.run_iteration(bounded_ctx))

        # exact order non-deterministic due to threaded dequeue
        assert set(get_run_ids(instance.run_launcher.queue())) == {"run-1", "run-3"}


@pytest.mark.parametrize(
    "use_threads",
    [False, True],
)
def test_limits_per_unique_value(use_threads, workspace_context, pipeline_handle, daemon):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        tag_concurrency_limits=[
            {"key": "foo", "limit": 1, "value": {"applyLimitPerUniqueValue": True}},
        ],
        dequeue_use_threads=use_threads,
    ) as instance:
        bounded_ctx = workspace_context.copy_for_test_instance(instance)

        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-1",
            tags={"foo": "bar"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-2",
            tags={"foo": "bar"},
        )
        list(daemon.run_iteration(bounded_ctx))

        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-3",
            tags={"foo": "other"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-4",
            tags={"foo": "other"},
        )

        list(daemon.run_iteration(bounded_ctx))

        # exact order non-deterministic due to threaded dequeue
        assert set(get_run_ids(instance.run_launcher.queue())) == {"run-1", "run-3"}


@pytest.mark.parametrize(
    "use_threads",
    [False, True],
)
def test_limits_per_unique_value_overlapping_limits(
    use_threads,
    workspace_context,
    daemon,
    pipeline_handle,
):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        tag_concurrency_limits=[
            {"key": "foo", "limit": 1, "value": {"applyLimitPerUniqueValue": True}},
            {"key": "foo", "limit": 2},
        ],
        dequeue_use_threads=use_threads,
    ) as instance:
        bounded_ctx = workspace_context.copy_for_test_instance(instance)

        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-1",
            tags={"foo": "bar"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-2",
            tags={"foo": "bar"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-3",
            tags={"foo": "other"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-4",
            tags={"foo": "other-2"},
        )

        list(daemon.run_iteration(bounded_ctx))

        # exact order non-deterministic due to threaded dequeue
        assert set(get_run_ids(instance.run_launcher.queue())) == {"run-1", "run-3"}

    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        tag_concurrency_limits=[
            {"key": "foo", "limit": 2, "value": {"applyLimitPerUniqueValue": True}},
            {"key": "foo", "limit": 1, "value": "bar"},
        ],
        dequeue_use_threads=use_threads,
    ) as instance:
        bounded_ctx = workspace_context.copy_for_test_instance(instance)

        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-1",
            tags={"foo": "bar"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-2",
            tags={"foo": "baz"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-3",
            tags={"foo": "bar"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-4",
            tags={"foo": "baz"},
        )
        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-5",
            tags={"foo": "baz"},
        )

        list(daemon.run_iteration(bounded_ctx))

        # exact order non-deterministic due to threaded dequeue
        assert set(get_run_ids(instance.run_launcher.queue())) == {"run-1", "run-2", "run-4"}


def test_locations_not_created(instance, monkeypatch, workspace_context, daemon, pipeline_handle):
    """Verifies that no repository location is created when runs are dequeued."""
    create_queued_run(
        instance,
        pipeline_handle,
        run_id="queued-run",
    )

    create_queued_run(
        instance,
        pipeline_handle,
        run_id="queued-run-2",
    )

    original_method = GrpcServerRepositoryLocation.__init__

    method_calls = []

    def mocked_location_init(
        self,
        origin,
        host=None,
        port=None,
        socket=None,
        server_id=None,
        heartbeat=False,
        watch_server=True,
        grpc_server_registry=None,
    ):
        method_calls.append(origin)
        return original_method(
            self,
            origin,
            host,
            port,
            socket,
            server_id,
            heartbeat,
            watch_server,
            grpc_server_registry,
        )

    monkeypatch.setattr(
        GrpcServerRepositoryLocation,
        "__init__",
        mocked_location_init,
    )

    list(daemon.run_iteration(workspace_context))

    assert get_run_ids(instance.run_launcher.queue()) == ["queued-run", "queued-run-2"]
    assert len(method_calls) == 0


@pytest.mark.parametrize(
    "use_threads",
    [False, True],
)
def test_skip_error_runs(pipeline_handle, daemon, use_threads):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10, dequeue_use_threads=use_threads
    ) as instance:
        with create_test_daemon_workspace_context(
            workspace_load_target=EmptyWorkspaceTarget(), instance=instance
        ) as workspace_context:
            create_queued_run(
                instance,
                pipeline_handle,
                run_id="bad-run",
            )

            create_queued_run(
                instance,
                pipeline_handle,
                run_id="good-run",
            )

            create_queued_run(
                instance,
                pipeline_handle,
                run_id="bad-user-code-run",
            )

            list(daemon.run_iteration(workspace_context))

            assert get_run_ids(instance.run_launcher.queue()) == ["good-run"]
            assert instance.get_run_by_id("bad-run").status == DagsterRunStatus.FAILURE
            assert instance.get_run_by_id("bad-user-code-run").status == DagsterRunStatus.FAILURE


@pytest.mark.parametrize(
    "use_threads",
    [False, True],
)
def test_retry_user_code_error_run(
    pipeline_handle, other_location_pipeline_handle, daemon, use_threads
):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        dequeue_use_threads=use_threads,
        max_user_code_failure_retries=2,
        user_code_failure_retry_delay=120,
    ) as instance:
        with create_test_daemon_workspace_context(
            workspace_load_target=EmptyWorkspaceTarget(), instance=instance
        ) as workspace_context:
            fixed_iteration_time = time.time() - 3600 * 24 * 365

            create_queued_run(instance, pipeline_handle, run_id="bad-run")
            create_queued_run(instance, pipeline_handle, run_id="good-run")
            create_queued_run(
                instance,
                pipeline_handle,
                run_id="bad-user-code-run",
            )

            list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

            assert get_run_ids(instance.run_launcher.queue()) == ["good-run"]
            assert instance.get_run_by_id("bad-run").status == DagsterRunStatus.FAILURE

            # Run was put back into the queue due to the user code failure
            assert instance.get_run_by_id("bad-user-code-run").status == DagsterRunStatus.QUEUED

            # Other runs in the same location are skipped
            create_queued_run(
                instance,
                pipeline_handle,
                run_id="good-run-same-location",
                tags={
                    "dagster/priority": "5",
                },
            )
            create_queued_run(
                instance,
                other_location_pipeline_handle,
                run_id="good-run-other-location",
            )
            list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

            assert get_run_ids(instance.run_launcher.queue()) == [
                "good-run",
                "good-run-other-location",
            ]

            fixed_iteration_time = fixed_iteration_time + 10

            # Add more runs, one in the same location, one in another location - the former is
            # skipped, the other launches. The original failed run is also skipped
            list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

            assert instance.get_run_by_id("bad-user-code-run").status == DagsterRunStatus.QUEUED
            assert (
                instance.get_run_by_id("good-run-same-location").status == DagsterRunStatus.QUEUED
            )

            fixed_iteration_time = fixed_iteration_time + 121

            list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

            assert instance.get_run_by_id("bad-user-code-run").status == DagsterRunStatus.QUEUED

            fixed_iteration_time = fixed_iteration_time + 121

            # Gives up after max_user_code_failure_retries retries - the good run from that
            # location succeeds

            list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

            assert instance.get_run_by_id("bad-user-code-run").status == DagsterRunStatus.FAILURE

            fixed_iteration_time = fixed_iteration_time + 121

            list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

            # good run is now free to launch (since it is dequeud before the bad run due to), bad run does its second retry
            assert get_run_ids(instance.run_launcher.queue()) == [
                "good-run",
                "good-run-other-location",
                "good-run-same-location",
            ]


@pytest.mark.parametrize(
    "use_threads",
    [False, True],
)
def test_retry_user_code_error_recovers(pipeline_handle, daemon, use_threads):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        dequeue_use_threads=use_threads,
        max_user_code_failure_retries=1,
        user_code_failure_retry_delay=5,
    ) as instance:
        with create_test_daemon_workspace_context(
            workspace_load_target=EmptyWorkspaceTarget(), instance=instance
        ) as workspace_context:
            fixed_iteration_time = time.time() - 3600 * 24 * 365

            create_queued_run(
                instance,
                pipeline_handle,
                run_id="bad-user-code-run",
            )

            # fails on initial dequeue

            list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

            assert instance.get_run_by_id("bad-user-code-run").status == DagsterRunStatus.QUEUED

            fixed_iteration_time = fixed_iteration_time + 6

            # Passes on retry

            instance.run_launcher.bad_user_code_run_ids = set()

            list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

            assert get_run_ids(instance.run_launcher.queue()) == [
                "bad-user-code-run",
            ]


@pytest.mark.parametrize(
    "use_threads",
    [False, True],
)
def test_key_limit_with_extra_tags(use_threads, workspace_context, daemon, pipeline_handle):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=2,
        tag_concurrency_limits=[
            {"key": "test", "limit": 1},
        ],
        dequeue_use_threads=use_threads,
    ) as instance:
        bounded_ctx = workspace_context.copy_for_test_instance(instance)

        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-1",
            tags={"other-tag": "value", "test": "value"},
        )

        create_queued_run(
            instance,
            pipeline_handle,
            run_id="run-2",
            tags={"other-tag": "value", "test": "value"},
        )

        list(daemon.run_iteration(bounded_ctx))
        assert get_run_ids(instance.run_launcher.queue()) == ["run-1"]
