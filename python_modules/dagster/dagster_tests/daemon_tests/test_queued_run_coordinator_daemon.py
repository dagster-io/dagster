# pylint: disable=redefined-outer-name

from contextlib import contextmanager

import pytest
from dagster.core.host_representation.repository_location import GrpcServerRepositoryLocation
from dagster.core.storage.pipeline_run import IN_PROGRESS_RUN_STATUSES, PipelineRunStatus
from dagster.core.storage.tags import PRIORITY_TAG
from dagster.core.test_utils import (
    create_run_for_test,
    create_test_daemon_workspace,
    instance_for_test,
)
from dagster.daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon
from dagster_tests.api_tests.utils import get_foo_pipeline_handle


@contextmanager
def instance_for_queued_run_coordinator(max_concurrent_runs=None, tag_concurrency_limits=None):
    max_concurrent_runs = (
        {"max_concurrent_runs": max_concurrent_runs} if max_concurrent_runs else {}
    )
    tag_concurrency_limits = (
        {"tag_concurrency_limits": tag_concurrency_limits} if tag_concurrency_limits else {}
    )
    overrides = {
        "run_coordinator": {
            "module": "dagster.core.run_coordinator",
            "class": "QueuedRunCoordinator",
            "config": {**max_concurrent_runs, **tag_concurrency_limits},
        },
        "run_launcher": {
            "module": "dagster.core.test_utils",
            "class": "MockedRunLauncher",
            "config": {"bad_run_ids": ["bad-run"]},
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


@pytest.fixture(name="workspace")
def workspace_fixture():
    with create_test_daemon_workspace() as workspace:
        yield workspace


def create_run(instance, **kwargs):
    with get_foo_pipeline_handle() as pipeline_handle:
        create_run_for_test(
            instance,
            external_pipeline_origin=pipeline_handle.get_external_origin(),
            pipeline_code_origin=pipeline_handle.get_python_origin(),
            pipeline_name="foo",
            **kwargs,
        )


def get_run_ids(runs_queue):
    return [run.run_id for run in runs_queue]


def test_attempt_to_launch_runs_filter(instance, workspace, daemon):
    create_run(
        instance,
        run_id="queued-run",
        status=PipelineRunStatus.QUEUED,
    )
    create_run(
        instance,
        run_id="non-queued-run",
        status=PipelineRunStatus.NOT_STARTED,
    )

    list(daemon.run_iteration(instance, workspace))

    assert get_run_ids(instance.run_launcher.queue()) == ["queued-run"]


def test_attempt_to_launch_runs_no_queued(instance, workspace, daemon):
    create_run(
        instance,
        run_id="queued-run",
        status=PipelineRunStatus.STARTED,
    )
    create_run(
        instance,
        run_id="non-queued-run",
        status=PipelineRunStatus.NOT_STARTED,
    )

    list(daemon.run_iteration(instance, workspace))

    assert instance.run_launcher.queue() == []


@pytest.mark.parametrize(
    "num_in_progress_runs",
    range(6),
)
def test_get_queued_runs_max_runs(num_in_progress_runs, workspace, daemon):
    max_runs = 4
    with instance_for_queued_run_coordinator(max_concurrent_runs=max_runs) as instance:
        # fill run store with ongoing runs
        in_progress_run_ids = ["in_progress-run-{}".format(i) for i in range(num_in_progress_runs)]
        for i, run_id in enumerate(in_progress_run_ids):
            # get a selection of all in progress statuses
            status = IN_PROGRESS_RUN_STATUSES[i % len(IN_PROGRESS_RUN_STATUSES)]
            create_run(
                instance,
                run_id=run_id,
                status=status,
            )

        # add more queued runs than should be launched
        queued_run_ids = ["queued-run-{}".format(i) for i in range(max_runs + 1)]
        for run_id in queued_run_ids:
            create_run(
                instance,
                run_id=run_id,
                status=PipelineRunStatus.QUEUED,
            )

        list(daemon.run_iteration(instance, workspace))

        assert len(instance.run_launcher.queue()) == max(0, max_runs - num_in_progress_runs)


def test_priority(instance, workspace, daemon):
    create_run(instance, run_id="default-pri-run", status=PipelineRunStatus.QUEUED)
    create_run(
        instance,
        run_id="low-pri-run",
        status=PipelineRunStatus.QUEUED,
        tags={PRIORITY_TAG: "-1"},
    )
    create_run(
        instance,
        run_id="hi-pri-run",
        status=PipelineRunStatus.QUEUED,
        tags={PRIORITY_TAG: "3"},
    )

    list(daemon.run_iteration(instance, workspace))

    assert get_run_ids(instance.run_launcher.queue()) == [
        "hi-pri-run",
        "default-pri-run",
        "low-pri-run",
    ]


def test_priority_on_malformed_tag(instance, workspace, daemon):
    create_run(
        instance,
        run_id="bad-pri-run",
        status=PipelineRunStatus.QUEUED,
        tags={PRIORITY_TAG: "foobar"},
    )

    list(daemon.run_iteration(instance, workspace))

    assert get_run_ids(instance.run_launcher.queue()) == ["bad-pri-run"]


def test_tag_limits(workspace, daemon):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        tag_concurrency_limits=[{"key": "database", "value": "tiny", "limit": 1}],
    ) as instance:
        create_run(
            instance,
            run_id="tiny-1",
            status=PipelineRunStatus.QUEUED,
            tags={"database": "tiny"},
        )
        create_run(
            instance,
            run_id="tiny-2",
            status=PipelineRunStatus.QUEUED,
            tags={"database": "tiny"},
        )
        create_run(
            instance,
            run_id="large-1",
            status=PipelineRunStatus.QUEUED,
            tags={"database": "large"},
        )

        list(daemon.run_iteration(instance, workspace))

        assert get_run_ids(instance.run_launcher.queue()) == ["tiny-1", "large-1"]


def test_tag_limits_just_key(workspace, daemon):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        tag_concurrency_limits=[
            {"key": "database", "value": {"applyLimitPerUniqueValue": False}, "limit": 2}
        ],
    ) as instance:
        create_run(
            instance,
            run_id="tiny-1",
            status=PipelineRunStatus.QUEUED,
            tags={"database": "tiny"},
        )
        create_run(
            instance,
            run_id="tiny-2",
            status=PipelineRunStatus.QUEUED,
            tags={"database": "tiny"},
        )
        create_run(
            instance,
            run_id="large-1",
            status=PipelineRunStatus.QUEUED,
            tags={"database": "large"},
        )

        list(daemon.run_iteration(instance, workspace))

        assert get_run_ids(instance.run_launcher.queue()) == ["tiny-1", "tiny-2"]


def test_multiple_tag_limits(workspace, daemon):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        tag_concurrency_limits=[
            {"key": "database", "value": "tiny", "limit": 1},
            {"key": "user", "value": "johann", "limit": 2},
        ],
    ) as instance:
        create_run(
            instance,
            run_id="run-1",
            status=PipelineRunStatus.QUEUED,
            tags={"database": "tiny", "user": "johann"},
        )
        create_run(
            instance,
            run_id="run-2",
            status=PipelineRunStatus.QUEUED,
            tags={"database": "tiny"},
        )
        create_run(
            instance,
            run_id="run-3",
            status=PipelineRunStatus.QUEUED,
            tags={"user": "johann"},
        )
        create_run(
            instance,
            run_id="run-4",
            status=PipelineRunStatus.QUEUED,
            tags={"user": "johann"},
        )

        list(daemon.run_iteration(instance, workspace))

        assert get_run_ids(instance.run_launcher.queue()) == ["run-1", "run-3"]


def test_overlapping_tag_limits(workspace, daemon):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        tag_concurrency_limits=[
            {"key": "foo", "limit": 2},
            {"key": "foo", "value": "bar", "limit": 1},
        ],
    ) as instance:
        create_run(
            instance,
            run_id="run-1",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "bar"},
        )
        create_run(
            instance,
            run_id="run-2",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "bar"},
        )
        create_run(
            instance,
            run_id="run-3",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "other"},
        )
        create_run(
            instance,
            run_id="run-4",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "other"},
        )

        list(daemon.run_iteration(instance, workspace))

        assert get_run_ids(instance.run_launcher.queue()) == ["run-1", "run-3"]


def test_limits_per_unique_value(workspace, daemon):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        tag_concurrency_limits=[
            {"key": "foo", "limit": 1, "value": {"applyLimitPerUniqueValue": True}},
        ],
    ) as instance:
        create_run(
            instance,
            run_id="run-1",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "bar"},
        )
        create_run(
            instance,
            run_id="run-2",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "bar"},
        )
        list(daemon.run_iteration(instance, workspace))

        create_run(
            instance,
            run_id="run-3",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "other"},
        )
        create_run(
            instance,
            run_id="run-4",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "other"},
        )

        list(daemon.run_iteration(instance, workspace))

        assert get_run_ids(instance.run_launcher.queue()) == ["run-1", "run-3"]


def test_limits_per_unique_value_overlapping_limits(workspace, daemon):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        tag_concurrency_limits=[
            {"key": "foo", "limit": 1, "value": {"applyLimitPerUniqueValue": True}},
            {"key": "foo", "limit": 2},
        ],
    ) as instance:
        create_run(
            instance,
            run_id="run-1",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "bar"},
        )
        create_run(
            instance,
            run_id="run-2",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "bar"},
        )
        create_run(
            instance,
            run_id="run-3",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "other"},
        )
        create_run(
            instance,
            run_id="run-4",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "other-2"},
        )

        list(daemon.run_iteration(instance, workspace))

        assert get_run_ids(instance.run_launcher.queue()) == ["run-1", "run-3"]

    with instance_for_queued_run_coordinator(
        max_concurrent_runs=10,
        tag_concurrency_limits=[
            {"key": "foo", "limit": 2, "value": {"applyLimitPerUniqueValue": True}},
            {"key": "foo", "limit": 1, "value": "bar"},
        ],
    ) as instance:
        create_run(
            instance,
            run_id="run-1",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "bar"},
        )
        create_run(
            instance,
            run_id="run-2",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "baz"},
        )
        create_run(
            instance,
            run_id="run-3",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "bar"},
        )
        create_run(
            instance,
            run_id="run-4",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "baz"},
        )
        create_run(
            instance,
            run_id="run-5",
            status=PipelineRunStatus.QUEUED,
            tags={"foo": "baz"},
        )

        list(daemon.run_iteration(instance, workspace))

        assert get_run_ids(instance.run_launcher.queue()) == ["run-1", "run-2", "run-4"]


def test_locations_not_created(instance, monkeypatch, workspace, daemon):
    """
    Verifies that no repository location is created when runs are dequeued
    """

    create_run(
        instance,
        run_id="queued-run",
        status=PipelineRunStatus.QUEUED,
    )

    create_run(
        instance,
        run_id="queued-run-2",
        status=PipelineRunStatus.QUEUED,
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

    list(daemon.run_iteration(instance, workspace))

    assert get_run_ids(instance.run_launcher.queue()) == ["queued-run", "queued-run-2"]
    assert len(method_calls) == 0


def test_skip_error_runs(instance, workspace, daemon):
    create_run(
        instance,
        run_id="bad-run",
        status=PipelineRunStatus.QUEUED,
    )

    create_run(
        instance,
        run_id="good-run",
        status=PipelineRunStatus.QUEUED,
    )

    errors = [error for error in list(daemon.run_iteration(instance, workspace)) if error]

    assert len(errors) == 1
    assert "Bad run bad-run" in errors[0].message

    assert get_run_ids(instance.run_launcher.queue()) == ["good-run"]
    assert instance.get_run_by_id("bad-run").status == PipelineRunStatus.FAILURE


def test_key_limit_with_extra_tags(workspace, daemon):
    with instance_for_queued_run_coordinator(
        max_concurrent_runs=2,
        tag_concurrency_limits=[
            {"key": "test", "limit": 1},
        ],
    ) as instance:
        create_run(
            instance,
            run_id="run-1",
            status=PipelineRunStatus.QUEUED,
            tags={"other-tag": "value", "test": "value"},
        )

        create_run(
            instance,
            run_id="run-2",
            status=PipelineRunStatus.QUEUED,
            tags={"other-tag": "value", "test": "value"},
        )

        list(daemon.run_iteration(instance, workspace))
        assert get_run_ids(instance.run_launcher.queue()) == ["run-1"]
