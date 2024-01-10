import time
from abc import ABC, abstractmethod
from typing import Iterator

import pytest
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.host_representation.code_location import GrpcServerCodeLocation
from dagster._core.host_representation.handle import JobHandle
from dagster._core.host_representation.origin import ManagedGrpcPythonEnvCodeLocationOrigin
from dagster._core.storage.dagster_run import IN_PROGRESS_RUN_STATUSES, DagsterRunStatus
from dagster._core.storage.tags import PRIORITY_TAG
from dagster._core.test_utils import (
    create_run_for_test,
    create_test_daemon_workspace_context,
    instance_for_test,
)
from dagster._core.workspace.load_target import EmptyWorkspaceTarget, PythonFileTarget
from dagster._daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon
from dagster._utils import file_relative_path

from dagster_tests.api_tests.utils import (
    get_foo_job_handle,
)


class QueuedRunCoordinatorDaemonTests(ABC):
    @pytest.fixture
    def run_coordinator_config(self):
        return {}

    @abstractmethod
    @pytest.fixture()
    def instance(self, run_coordinator_config):
        raise NotImplementedError

    @pytest.fixture(params=[1, 25])
    def page_size(self, request):
        yield request.param

    @abstractmethod
    @pytest.fixture()
    def daemon(self, page_size):
        raise NotImplementedError

    @pytest.fixture()
    def workspace_context(self, instance):
        with create_test_daemon_workspace_context(
            workspace_load_target=EmptyWorkspaceTarget(), instance=instance
        ) as workspace_context:
            yield workspace_context

    @pytest.fixture(scope="module")
    def job_handle(self) -> Iterator[JobHandle]:
        with get_foo_job_handle() as handle:
            yield handle

    @pytest.fixture()
    def concurrency_limited_workspace_context(self, instance):
        with create_test_daemon_workspace_context(
            workspace_load_target=PythonFileTarget(
                python_file=file_relative_path(
                    __file__, "test_locations/concurrency_limited_workspace.py"
                ),
                attribute=None,
                working_directory=None,
                location_name="test",
            ),
            instance=instance,
        ) as workspace_context:
            yield workspace_context

    @pytest.fixture(scope="module")
    def other_location_job_handle(self, job_handle: JobHandle) -> JobHandle:
        code_location_origin = job_handle.repository_handle.code_location_origin
        assert isinstance(code_location_origin, ManagedGrpcPythonEnvCodeLocationOrigin)
        return job_handle._replace(
            repository_handle=job_handle.repository_handle._replace(
                code_location_origin=code_location_origin._replace(
                    location_name="other_location_name"
                )
            )
        )

    def create_run(self, instance, job_handle, **kwargs):
        create_run_for_test(
            instance,
            external_job_origin=job_handle.get_external_origin(),
            job_code_origin=job_handle.get_python_origin(),
            job_name="foo",
            **kwargs,
        )

    def create_queued_run(self, instance, job_handle, **kwargs):
        run = create_run_for_test(
            instance,
            external_job_origin=job_handle.get_external_origin(),
            job_code_origin=job_handle.get_python_origin(),
            job_name="foo",
            status=DagsterRunStatus.NOT_STARTED,
            **kwargs,
        )
        enqueued_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_ENQUEUED.value,
            job_name=run.job_name,
        )
        instance.report_dagster_event(enqueued_event, run_id=run.run_id)
        return instance.get_run_by_id(run.run_id)

    def get_run_ids(self, runs_queue):
        return [run.run_id for run in runs_queue]

    def test_attempt_to_launch_runs_filter(self, instance, workspace_context, daemon, job_handle):
        self.create_queued_run(
            instance,
            job_handle,
            run_id="queued-run",
        )
        self.create_run(
            instance,
            job_handle,
            run_id="non-queued-run",
            status=DagsterRunStatus.NOT_STARTED,
        )

        list(daemon.run_iteration(workspace_context))

        assert self.get_run_ids(instance.run_launcher.queue()) == ["queued-run"]

    def test_attempt_to_launch_runs_no_queued(
        self, instance, job_handle, workspace_context, daemon
    ):
        self.create_run(
            instance,
            job_handle,
            run_id="queued-run",
            status=DagsterRunStatus.STARTED,
        )
        self.create_run(
            instance,
            job_handle,
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
        "run_coordinator_config",
        [
            dict(max_concurrent_runs=4, dequeue_use_threads=True),
            dict(max_concurrent_runs=4, dequeue_use_threads=False),
        ],
    )
    def test_get_queued_runs_max_runs(
        self,
        num_in_progress_runs,
        job_handle,
        workspace_context,
        daemon,
        run_coordinator_config,
        instance,
    ):
        max_runs = run_coordinator_config["max_concurrent_runs"]
        # fill run store with ongoing runs
        in_progress_run_ids = [f"in_progress-run-{i}" for i in range(num_in_progress_runs)]
        for i, run_id in enumerate(in_progress_run_ids):
            # get a selection of all in progress statuses
            status = IN_PROGRESS_RUN_STATUSES[i % len(IN_PROGRESS_RUN_STATUSES)]
            self.create_run(
                instance,
                job_handle,
                run_id=run_id,
                status=status,
            )

        # add more queued runs than should be launched
        queued_run_ids = [f"queued-run-{i}" for i in range(max_runs + 1)]
        for run_id in queued_run_ids:
            self.create_queued_run(
                instance,
                job_handle,
                run_id=run_id,
            )

        list(daemon.run_iteration(workspace_context))

        assert len(instance.run_launcher.queue()) == max(0, max_runs - num_in_progress_runs)

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(max_concurrent_runs=-1, dequeue_use_threads=True),
            dict(max_concurrent_runs=-1, dequeue_use_threads=False),
        ],
    )
    def test_disable_max_concurrent_runs_limit(
        self, workspace_context, job_handle, daemon, instance
    ):
        # create ongoing runs
        in_progress_run_ids = [f"in_progress-run-{i}" for i in range(5)]
        for i, run_id in enumerate(in_progress_run_ids):
            # get a selection of all in progress statuses
            status = IN_PROGRESS_RUN_STATUSES[i % len(IN_PROGRESS_RUN_STATUSES)]
            self.create_run(
                instance,
                job_handle,
                run_id=run_id,
                status=status,
            )

        # add more queued runs
        queued_run_ids = [f"queued-run-{i}" for i in range(6)]
        for run_id in queued_run_ids:
            self.create_queued_run(
                instance,
                job_handle,
                run_id=run_id,
            )

        list(daemon.run_iteration(workspace_context))

        assert len(instance.run_launcher.queue()) == 6

    def test_priority(self, instance, workspace_context, job_handle, daemon):
        self.create_run(
            instance, job_handle, run_id="default-pri-run", status=DagsterRunStatus.QUEUED
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="low-pri-run",
            tags={PRIORITY_TAG: "-1"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="hi-pri-run",
            tags={PRIORITY_TAG: "3"},
        )

        list(daemon.run_iteration(workspace_context))

        assert self.get_run_ids(instance.run_launcher.queue()) == [
            "hi-pri-run",
            "default-pri-run",
            "low-pri-run",
        ]

    def test_priority_on_malformed_tag(self, instance, workspace_context, job_handle, daemon):
        self.create_queued_run(
            instance,
            job_handle,
            run_id="bad-pri-run",
            tags={PRIORITY_TAG: "foobar"},
        )

        list(daemon.run_iteration(workspace_context))

        assert self.get_run_ids(instance.run_launcher.queue()) == ["bad-pri-run"]

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(
                max_concurrent_runs=10,
                tag_concurrency_limits=[{"key": "database", "value": "tiny", "limit": 1}],
                dequeue_use_threads=True,
            ),
            dict(
                max_concurrent_runs=10,
                tag_concurrency_limits=[{"key": "database", "value": "tiny", "limit": 1}],
                dequeue_use_threads=False,
            ),
        ],
    )
    def test_tag_limits(self, workspace_context, job_handle, daemon, instance):
        self.create_queued_run(
            instance,
            job_handle,
            run_id="tiny-1",
            tags={"database": "tiny"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="tiny-2",
            tags={"database": "tiny"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="large-1",
            tags={"database": "large"},
        )

        list(daemon.run_iteration(workspace_context))

        # exact order non-deterministic due to threaded dequeue
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {"tiny-1", "large-1"}

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(
                max_concurrent_runs=10,
                tag_concurrency_limits=[
                    {"key": "database", "value": {"applyLimitPerUniqueValue": False}, "limit": 2}
                ],
                dequeue_use_threads=True,
            ),
            dict(
                max_concurrent_runs=10,
                tag_concurrency_limits=[
                    {"key": "database", "value": {"applyLimitPerUniqueValue": False}, "limit": 2}
                ],
                dequeue_use_threads=False,
            ),
        ],
    )
    def test_tag_limits_just_key(self, workspace_context, job_handle, daemon, instance):
        self.create_queued_run(
            instance,
            job_handle,
            run_id="tiny-1",
            tags={"database": "tiny"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="tiny-2",
            tags={"database": "tiny"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="large-1",
            tags={"database": "large"},
        )

        list(daemon.run_iteration(workspace_context))

        # exact order non-deterministic due to threaded dequeue
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {"tiny-1", "tiny-2"}

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(
                max_concurrent_runs=10,
                tag_concurrency_limits=[
                    {"key": "database", "value": "tiny", "limit": 1},
                    {"key": "user", "value": "johann", "limit": 2},
                ],
                dequeue_use_threads=True,
            ),
            dict(
                max_concurrent_runs=10,
                tag_concurrency_limits=[
                    {"key": "database", "value": "tiny", "limit": 1},
                    {"key": "user", "value": "johann", "limit": 2},
                ],
                dequeue_use_threads=False,
            ),
        ],
    )
    def test_multiple_tag_limits(
        self,
        workspace_context,
        daemon,
        job_handle,
        instance,
    ):
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-1",
            tags={"database": "tiny", "user": "johann"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-2",
            tags={"database": "tiny"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-3",
            tags={"user": "johann"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-4",
            tags={"user": "johann"},
        )

        list(daemon.run_iteration(workspace_context))

        # exact order non-deterministic due to threaded dequeue
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {"run-1", "run-3"}

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(
                max_concurrent_runs=10,
                tag_concurrency_limits=[
                    {"key": "foo", "limit": 2},
                    {"key": "foo", "value": "bar", "limit": 1},
                ],
                dequeue_use_threads=True,
            ),
            dict(
                max_concurrent_runs=10,
                tag_concurrency_limits=[
                    {"key": "foo", "limit": 2},
                    {"key": "foo", "value": "bar", "limit": 1},
                ],
                dequeue_use_threads=False,
            ),
        ],
    )
    def test_overlapping_tag_limits(self, workspace_context, daemon, job_handle, instance):
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-1",
            tags={"foo": "bar"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-2",
            tags={"foo": "bar"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-3",
            tags={"foo": "other"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-4",
            tags={"foo": "other"},
        )

        list(daemon.run_iteration(workspace_context))

        # exact order non-deterministic due to threaded dequeue
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {"run-1", "run-3"}

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(
                max_concurrent_runs=10,
                tag_concurrency_limits=[
                    {"key": "foo", "limit": 1, "value": {"applyLimitPerUniqueValue": True}},
                ],
                dequeue_use_threads=True,
            ),
            dict(
                max_concurrent_runs=10,
                tag_concurrency_limits=[
                    {"key": "foo", "limit": 1, "value": {"applyLimitPerUniqueValue": True}},
                ],
                dequeue_use_threads=False,
            ),
        ],
    )
    def test_limits_per_unique_value(self, workspace_context, job_handle, daemon, instance):
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-1",
            tags={"foo": "bar"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-2",
            tags={"foo": "bar"},
        )
        list(daemon.run_iteration(workspace_context))

        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-3",
            tags={"foo": "other"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-4",
            tags={"foo": "other"},
        )

        list(daemon.run_iteration(workspace_context))

        # exact order non-deterministic due to threaded dequeue
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {"run-1", "run-3"}

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(
                max_concurrent_runs=10,
                tag_concurrency_limits=[
                    {"key": "foo", "limit": 1, "value": {"applyLimitPerUniqueValue": True}},
                    {"key": "foo", "limit": 2},
                ],
                dequeue_use_threads=True,
            ),
            dict(
                max_concurrent_runs=10,
                tag_concurrency_limits=[
                    {"key": "foo", "limit": 1, "value": {"applyLimitPerUniqueValue": True}},
                    {"key": "foo", "limit": 2},
                ],
                dequeue_use_threads=False,
            ),
        ],
    )
    def test_limits_per_unique_value_overlapping_limits_less_than(
        self,
        workspace_context,
        daemon,
        job_handle,
        instance,
    ):
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-1",
            tags={"foo": "bar"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-2",
            tags={"foo": "bar"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-3",
            tags={"foo": "other"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-4",
            tags={"foo": "other-2"},
        )

        list(daemon.run_iteration(workspace_context))

        # exact order non-deterministic due to threaded dequeue
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {"run-1", "run-3"}

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(
                max_concurrent_runs=10,
                tag_concurrency_limits=[
                    {"key": "foo", "limit": 2, "value": {"applyLimitPerUniqueValue": True}},
                    {"key": "foo", "limit": 1, "value": "bar"},
                ],
                dequeue_use_threads=True,
            ),
            dict(
                max_concurrent_runs=10,
                tag_concurrency_limits=[
                    {"key": "foo", "limit": 2, "value": {"applyLimitPerUniqueValue": True}},
                    {"key": "foo", "limit": 1, "value": "bar"},
                ],
                dequeue_use_threads=False,
            ),
        ],
    )
    def test_limits_per_unique_value_overlapping_limits_greater_than(
        self,
        workspace_context,
        daemon,
        job_handle,
        instance,
    ):
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-1",
            tags={"foo": "bar"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-2",
            tags={"foo": "baz"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-3",
            tags={"foo": "bar"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-4",
            tags={"foo": "baz"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-5",
            tags={"foo": "baz"},
        )

        list(daemon.run_iteration(workspace_context))

        # exact order non-deterministic due to threaded dequeue
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {
            "run-1",
            "run-2",
            "run-4",
        }

    def test_locations_not_created(
        self, instance, monkeypatch, workspace_context, daemon, job_handle
    ):
        """Verifies that no repository location is created when runs are dequeued."""
        self.create_queued_run(
            instance,
            job_handle,
            run_id="queued-run",
        )

        self.create_queued_run(
            instance,
            job_handle,
            run_id="queued-run-2",
        )

        original_method = GrpcServerCodeLocation.__init__

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
            GrpcServerCodeLocation,
            "__init__",
            mocked_location_init,
        )

        list(daemon.run_iteration(workspace_context))

        assert self.get_run_ids(instance.run_launcher.queue()) == ["queued-run", "queued-run-2"]
        assert len(method_calls) == 0

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(max_concurrent_runs=10, dequeue_use_threads=True),
            dict(max_concurrent_runs=10, dequeue_use_threads=False),
        ],
    )
    def test_skip_error_runs(self, job_handle, daemon, instance, workspace_context):
        self.create_queued_run(
            instance,
            job_handle,
            run_id="bad-run",
        )

        self.create_queued_run(
            instance,
            job_handle,
            run_id="good-run",
        )

        self.create_queued_run(
            instance,
            job_handle,
            run_id="bad-user-code-run",
        )

        list(daemon.run_iteration(workspace_context))

        assert self.get_run_ids(instance.run_launcher.queue()) == ["good-run"]
        assert instance.get_run_by_id("bad-run").status == DagsterRunStatus.FAILURE
        assert instance.get_run_by_id("bad-user-code-run").status == DagsterRunStatus.FAILURE

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(max_user_code_failure_retries=2, max_concurrent_runs=10, dequeue_use_threads=True),
            dict(
                max_user_code_failure_retries=2, max_concurrent_runs=10, dequeue_use_threads=False
            ),
        ],
    )
    def test_retry_user_code_error_run(
        self, job_handle, other_location_job_handle, daemon, instance, workspace_context
    ):
        fixed_iteration_time = time.time() - 3600 * 24 * 365

        self.create_queued_run(instance, job_handle, run_id="bad-run")
        self.create_queued_run(instance, job_handle, run_id="good-run")
        self.create_queued_run(
            instance,
            job_handle,
            run_id="bad-user-code-run",
        )

        list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

        assert self.get_run_ids(instance.run_launcher.queue()) == ["good-run"]
        assert instance.get_run_by_id("bad-run").status == DagsterRunStatus.FAILURE

        # Run was put back into the queue due to the user code failure
        assert instance.get_run_by_id("bad-user-code-run").status == DagsterRunStatus.QUEUED

        # Other runs in the same location are skipped
        self.create_queued_run(
            instance,
            job_handle,
            run_id="good-run-same-location",
            tags={
                "dagster/priority": "5",
            },
        )
        self.create_queued_run(
            instance,
            other_location_job_handle,
            run_id="good-run-other-location",
        )
        list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

        assert self.get_run_ids(instance.run_launcher.queue()) == [
            "good-run",
            "good-run-other-location",
        ]

        fixed_iteration_time = fixed_iteration_time + 10

        # Add more runs, one in the same location, one in another location - the former is
        # skipped, the other launches. The original failed run is also skipped
        list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

        assert instance.get_run_by_id("bad-user-code-run").status == DagsterRunStatus.QUEUED
        assert instance.get_run_by_id("good-run-same-location").status == DagsterRunStatus.QUEUED

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
        assert self.get_run_ids(instance.run_launcher.queue()) == [
            "good-run",
            "good-run-other-location",
            "good-run-same-location",
        ]

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(
                max_user_code_failure_retries=1,
                user_code_failure_retry_delay=5,
                max_concurrent_runs=10,
                dequeue_use_threads=True,
            ),
            dict(
                max_user_code_failure_retries=1,
                user_code_failure_retry_delay=5,
                max_concurrent_runs=10,
                dequeue_use_threads=False,
            ),
        ],
    )
    def test_retry_user_code_error_recovers(self, job_handle, daemon, instance, workspace_context):
        fixed_iteration_time = time.time() - 3600 * 24 * 365

        self.create_queued_run(
            instance,
            job_handle,
            run_id="bad-user-code-run",
        )

        # fails on initial dequeue

        list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

        assert instance.get_run_by_id("bad-user-code-run").status == DagsterRunStatus.QUEUED

        fixed_iteration_time = fixed_iteration_time + 6

        # Passes on retry

        instance.run_launcher.bad_user_code_run_ids = set()

        list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

        assert self.get_run_ids(instance.run_launcher.queue()) == [
            "bad-user-code-run",
        ]

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(
                max_concurrent_runs=2,
                tag_concurrency_limits=[
                    {"key": "test", "limit": 1},
                ],
                dequeue_use_threads=True,
            ),
            dict(
                max_concurrent_runs=2,
                tag_concurrency_limits=[
                    {"key": "test", "limit": 1},
                ],
                dequeue_use_threads=False,
            ),
        ],
    )
    def test_key_limit_with_extra_tags(self, workspace_context, daemon, job_handle, instance):
        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-1",
            tags={"other-tag": "value", "test": "value"},
        )

        self.create_queued_run(
            instance,
            job_handle,
            run_id="run-2",
            tags={"other-tag": "value", "test": "value"},
        )

        list(daemon.run_iteration(workspace_context))
        assert self.get_run_ids(instance.run_launcher.queue()) == ["run-1"]

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(
                max_concurrent_runs=2,
                tag_concurrency_limits=[
                    {"key": "test", "limit": 1},
                ],
                dequeue_use_threads=True,
            ),
        ],
    )
    def test_key_limit_with_priority(
        self, workspace_context, daemon, job_handle, instance, run_coordinator_config
    ):
        self.create_queued_run(
            instance,
            job_handle,
            run_id="low-priority",
            tags={"test": "value", PRIORITY_TAG: "-100"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id="high-priority",
            tags={"test": "value", PRIORITY_TAG: "100"},
        )

        list(daemon.run_iteration(workspace_context))
        assert self.get_run_ids(instance.run_launcher.queue()) == ["high-priority"]

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(block_op_concurrency_limited_runs=True),
        ],
    )
    def test_op_concurrency_aware_dequeuing(
        self,
        concurrency_limited_workspace_context,
        daemon,
        instance,
    ):
        workspace = concurrency_limited_workspace_context.create_request_context()
        external_job = workspace.get_full_external_job(
            JobSubsetSelector(
                location_name="test",
                repository_name="__repository__",
                job_name="concurrency_limited_asset_job",
                op_selection=None,
            )
        )
        self.create_queued_run(
            instance,
            external_job.handle,
            run_id="run-1",
            asset_selection=set([AssetKey("concurrency_limited_asset")]),
            job_snapshot=external_job.job_snapshot,
        )

        instance.event_log_storage.set_concurrency_slots("foo", 1)
        list(daemon.run_iteration(concurrency_limited_workspace_context))
        assert set(self.get_run_ids(instance.run_launcher.queue())) == set(["run-1"])

        self.create_queued_run(
            instance,
            external_job.handle,
            run_id="run-2",
            asset_selection=set([AssetKey("concurrency_limited_asset")]),
            job_snapshot=external_job.job_snapshot,
        )
        instance.event_log_storage.set_concurrency_slots("foo", 0)
        list(daemon.run_iteration(concurrency_limited_workspace_context))
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {"run-1"}
        assert any(
            [
                event
                for event in instance.all_logs("run-2")
                if "blocked waiting for op concurrency slots" in event.message
            ]
        )


class TestQueuedRunCoordinatorDaemon(QueuedRunCoordinatorDaemonTests):
    @pytest.fixture
    def instance(self, run_coordinator_config):
        overrides = {
            "run_coordinator": {
                "module": "dagster._core.run_coordinator",
                "class": "QueuedRunCoordinator",
                "config": {**run_coordinator_config},
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

    @pytest.fixture()
    def daemon(self, page_size):
        return QueuedRunCoordinatorDaemon(interval_seconds=1, page_size=page_size)
