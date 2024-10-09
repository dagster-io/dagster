import datetime
import time
from abc import ABC, abstractmethod
from typing import Iterator

import pytest
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.remote_representation.code_location import GrpcServerCodeLocation
from dagster._core.remote_representation.handle import JobHandle, RepositoryHandle
from dagster._core.remote_representation.origin import ManagedGrpcPythonEnvCodeLocationOrigin
from dagster._core.storage.dagster_run import IN_PROGRESS_RUN_STATUSES, DagsterRunStatus
from dagster._core.storage.tags import PRIORITY_TAG
from dagster._core.test_utils import (
    create_run_for_test,
    create_test_daemon_workspace_context,
    environ,
    freeze_time,
    instance_for_test,
)
from dagster._core.utils import make_new_run_id
from dagster._core.workspace.load_target import EmptyWorkspaceTarget, PythonFileTarget
from dagster._daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon
from dagster._record import copy
from dagster._time import create_datetime
from dagster._utils import file_relative_path

from dagster_tests.api_tests.utils import get_foo_job_handle

BAD_RUN_ID_UUID = make_new_run_id()
BAD_USER_CODE_RUN_ID_UUID = make_new_run_id()


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
        new_origin = code_location_origin._replace(location_name="other_location_name")
        with instance_for_test() as temp_instance:
            with new_origin.create_single_location(temp_instance) as location:
                new_repo_handle = RepositoryHandle.from_location(
                    job_handle.repository_name, location
                )

        return copy(
            job_handle,
            repository_handle=new_repo_handle,
        )

    def create_run(self, instance, job_handle, **kwargs):
        create_run_for_test(
            instance,
            remote_job_origin=job_handle.get_remote_origin(),
            job_code_origin=job_handle.get_python_origin(),
            job_name="foo",
            **kwargs,
        )

    def create_queued_run(self, instance, job_handle, **kwargs):
        run = create_run_for_test(
            instance,
            remote_job_origin=job_handle.get_remote_origin(),
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

    def submit_run(self, instance, external_job, workspace, **kwargs):
        location = workspace.get_code_location(external_job.handle.location_name)
        subset_job = location.get_external_job(
            JobSubsetSelector(
                location_name=location.name,
                repository_name=external_job.handle.repository_name,
                job_name=external_job.handle.job_name,
                op_selection=None,
                asset_selection=kwargs.get("asset_selection"),
            )
        )
        external_execution_plan = location.get_external_execution_plan(
            subset_job,
            {},
            step_keys_to_execute=None,
            known_state=None,
            instance=instance,
        )
        run = create_run_for_test(
            instance,
            remote_job_origin=subset_job.get_remote_origin(),
            job_code_origin=subset_job.get_python_origin(),
            job_name=subset_job.name,
            execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
            job_snapshot=subset_job.job_snapshot,
            parent_job_snapshot=subset_job.parent_job_snapshot,
            status=DagsterRunStatus.NOT_STARTED,
            **kwargs,
        )
        instance.submit_run(run.run_id, workspace)
        return run

    def get_run_ids(self, runs_queue):
        return [run.run_id for run in runs_queue]

    def get_external_concurrency_job(self, workspace):
        return workspace.get_full_job(
            JobSubsetSelector(
                location_name="test",
                repository_name="__repository__",
                job_name="concurrency_limited_asset_job",
                op_selection=None,
            )
        )

    def test_attempt_to_launch_runs_filter(self, instance, workspace_context, daemon, job_handle):
        queued_run_id, non_queued_run_id = [make_new_run_id() for _ in range(2)]
        self.create_queued_run(instance, job_handle, run_id=queued_run_id)
        self.create_run(
            instance, job_handle, run_id=non_queued_run_id, status=DagsterRunStatus.NOT_STARTED
        )

        list(daemon.run_iteration(workspace_context))

        assert self.get_run_ids(instance.run_launcher.queue()) == [queued_run_id]

    def test_attempt_to_launch_runs_no_queued(
        self, instance, job_handle, workspace_context, daemon
    ):
        queued_run_id = make_new_run_id()
        non_queued_run_id = make_new_run_id()
        self.create_run(instance, job_handle, run_id=queued_run_id, status=DagsterRunStatus.STARTED)
        self.create_run(
            instance, job_handle, run_id=non_queued_run_id, status=DagsterRunStatus.NOT_STARTED
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
        in_progress_run_ids = [make_new_run_id() for i in range(num_in_progress_runs)]
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
        queued_run_ids = [make_new_run_id() for i in range(max_runs + 1)]
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
        in_progress_run_ids = [make_new_run_id() for i in range(5)]
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
        queued_run_ids = [make_new_run_id() for i in range(6)]
        for run_id in queued_run_ids:
            self.create_queued_run(
                instance,
                job_handle,
                run_id=run_id,
            )

        list(daemon.run_iteration(workspace_context))

        assert len(instance.run_launcher.queue()) == 6

    def test_priority(self, instance, workspace_context, job_handle, daemon):
        default_run_id, hi_pri_run_id, lo_pri_run_id = [make_new_run_id() for _ in range(3)]
        self.create_run(instance, job_handle, run_id=default_run_id, status=DagsterRunStatus.QUEUED)
        self.create_queued_run(
            instance, job_handle, run_id=lo_pri_run_id, tags={PRIORITY_TAG: "-1"}
        )
        self.create_queued_run(instance, job_handle, run_id=hi_pri_run_id, tags={PRIORITY_TAG: "3"})

        list(daemon.run_iteration(workspace_context))

        assert self.get_run_ids(instance.run_launcher.queue()) == [
            hi_pri_run_id,
            default_run_id,
            lo_pri_run_id,
        ]

    def test_priority_on_malformed_tag(self, instance, workspace_context, job_handle, daemon):
        bad_pri_run_id = make_new_run_id()
        self.create_queued_run(
            instance,
            job_handle,
            run_id=bad_pri_run_id,
            tags={PRIORITY_TAG: "foobar"},
        )

        list(daemon.run_iteration(workspace_context))

        assert self.get_run_ids(instance.run_launcher.queue()) == [bad_pri_run_id]

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
        tiny_run_id, tiny_run_id_2, large_run_id = [make_new_run_id() for _ in range(3)]
        self.create_queued_run(instance, job_handle, run_id=tiny_run_id, tags={"database": "tiny"})
        self.create_queued_run(
            instance, job_handle, run_id=tiny_run_id_2, tags={"database": "tiny"}
        )
        self.create_queued_run(
            instance, job_handle, run_id=large_run_id, tags={"database": "large"}
        )

        list(daemon.run_iteration(workspace_context))

        # exact order non-deterministic due to threaded dequeue
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {tiny_run_id, large_run_id}

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
        tiny_run_id, tiny_run_id_2, large_run_id = [make_new_run_id() for _ in range(3)]
        self.create_queued_run(instance, job_handle, run_id=tiny_run_id, tags={"database": "tiny"})
        self.create_queued_run(
            instance, job_handle, run_id=tiny_run_id_2, tags={"database": "tiny"}
        )
        self.create_queued_run(
            instance, job_handle, run_id=large_run_id, tags={"database": "large"}
        )

        list(daemon.run_iteration(workspace_context))

        # exact order non-deterministic due to threaded dequeue
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {tiny_run_id, tiny_run_id_2}

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
        run_id_1, run_id_2, run_id_3, run_id_4 = [make_new_run_id() for _ in range(4)]
        self.create_queued_run(
            instance,
            job_handle,
            run_id=run_id_1,
            tags={"database": "tiny", "user": "johann"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id=run_id_2,
            tags={"database": "tiny"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id=run_id_3,
            tags={"user": "johann"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id=run_id_4,
            tags={"user": "johann"},
        )

        list(daemon.run_iteration(workspace_context))

        # exact order non-deterministic due to threaded dequeue
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {run_id_1, run_id_3}

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
        run_id_1, run_id_2, run_id_3, run_id_4 = [make_new_run_id() for _ in range(4)]
        self.create_queued_run(instance, job_handle, run_id=run_id_1, tags={"foo": "bar"})
        self.create_queued_run(instance, job_handle, run_id=run_id_2, tags={"foo": "bar"})
        self.create_queued_run(instance, job_handle, run_id=run_id_3, tags={"foo": "other"})
        self.create_queued_run(instance, job_handle, run_id=run_id_4, tags={"foo": "other"})

        list(daemon.run_iteration(workspace_context))

        # exact order non-deterministic due to threaded dequeue
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {run_id_1, run_id_3}

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
        run_id_1, run_id_2, run_id_3, run_id_4 = [make_new_run_id() for _ in range(4)]
        self.create_queued_run(instance, job_handle, run_id=run_id_1, tags={"foo": "bar"})
        self.create_queued_run(
            instance,
            job_handle,
            run_id=run_id_2,
            tags={"foo": "bar"},
        )
        list(daemon.run_iteration(workspace_context))

        self.create_queued_run(instance, job_handle, run_id=run_id_3, tags={"foo": "other"})
        self.create_queued_run(instance, job_handle, run_id=run_id_4, tags={"foo": "other"})

        list(daemon.run_iteration(workspace_context))

        # exact order non-deterministic due to threaded dequeue
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {run_id_1, run_id_3}

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
        run_id_1, run_id_2, run_id_3, run_id_4 = [make_new_run_id() for _ in range(4)]
        self.create_queued_run(instance, job_handle, run_id=run_id_1, tags={"foo": "bar"})
        self.create_queued_run(instance, job_handle, run_id=run_id_2, tags={"foo": "bar"})
        self.create_queued_run(instance, job_handle, run_id=run_id_3, tags={"foo": "other"})
        self.create_queued_run(instance, job_handle, run_id=run_id_4, tags={"foo": "other-2"})

        list(daemon.run_iteration(workspace_context))

        # exact order non-deterministic due to threaded dequeue
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {run_id_1, run_id_3}

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
        run_id_1, run_id_2, run_id_3, run_id_4, run_id_5 = [make_new_run_id() for _ in range(5)]
        self.create_queued_run(instance, job_handle, run_id=run_id_1, tags={"foo": "bar"})
        self.create_queued_run(instance, job_handle, run_id=run_id_2, tags={"foo": "baz"})
        self.create_queued_run(instance, job_handle, run_id=run_id_3, tags={"foo": "bar"})
        self.create_queued_run(instance, job_handle, run_id=run_id_4, tags={"foo": "baz"})
        self.create_queued_run(instance, job_handle, run_id=run_id_5, tags={"foo": "baz"})

        list(daemon.run_iteration(workspace_context))

        # exact order non-deterministic due to threaded dequeue
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {
            run_id_1,
            run_id_2,
            run_id_4,
        }

    def test_locations_not_created(
        self, instance, monkeypatch, workspace_context, daemon, job_handle
    ):
        """Verifies that no repository location is created when runs are dequeued."""
        queued_run_id_1, queued_run_id_2 = [make_new_run_id() for _ in range(2)]
        self.create_queued_run(instance, job_handle, run_id=queued_run_id_1)
        self.create_queued_run(instance, job_handle, run_id=queued_run_id_2)

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

        assert self.get_run_ids(instance.run_launcher.queue()) == [queued_run_id_1, queued_run_id_2]
        assert len(method_calls) == 0

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            dict(max_concurrent_runs=10, dequeue_use_threads=True),
            dict(max_concurrent_runs=10, dequeue_use_threads=False),
        ],
    )
    def test_skip_error_runs(self, job_handle, daemon, instance, workspace_context):
        good_run_id = make_new_run_id()
        self.create_queued_run(instance, job_handle, run_id=BAD_RUN_ID_UUID)
        self.create_queued_run(instance, job_handle, run_id=good_run_id)
        self.create_queued_run(instance, job_handle, run_id=BAD_USER_CODE_RUN_ID_UUID)

        list(daemon.run_iteration(workspace_context))

        assert self.get_run_ids(instance.run_launcher.queue()) == [good_run_id]
        assert instance.get_run_by_id(BAD_RUN_ID_UUID).status == DagsterRunStatus.FAILURE
        assert instance.get_run_by_id(BAD_USER_CODE_RUN_ID_UUID).status == DagsterRunStatus.FAILURE

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
        good_run_id, good_run_same_location_id, good_run_other_location_id = [
            make_new_run_id() for _ in range(3)
        ]
        fixed_iteration_time = time.time() - 3600 * 24 * 365

        self.create_queued_run(instance, job_handle, run_id=BAD_RUN_ID_UUID)
        self.create_queued_run(instance, job_handle, run_id=good_run_id)
        self.create_queued_run(instance, job_handle, run_id=BAD_USER_CODE_RUN_ID_UUID)

        list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

        assert self.get_run_ids(instance.run_launcher.queue()) == [good_run_id]
        assert instance.get_run_by_id(BAD_RUN_ID_UUID).status == DagsterRunStatus.FAILURE

        # Run was put back into the queue due to the user code failure
        assert instance.get_run_by_id(BAD_USER_CODE_RUN_ID_UUID).status == DagsterRunStatus.QUEUED

        # Other runs in the same location are skipped
        self.create_queued_run(
            instance,
            job_handle,
            run_id=good_run_same_location_id,
            tags={
                "dagster/priority": "5",
            },
        )
        self.create_queued_run(
            instance,
            other_location_job_handle,
            run_id=good_run_other_location_id,
        )
        list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

        assert self.get_run_ids(instance.run_launcher.queue()) == [
            good_run_id,
            good_run_other_location_id,
        ]

        fixed_iteration_time = fixed_iteration_time + 10

        # Add more runs, one in the same location, one in another location - the former is
        # skipped, the other launches. The original failed run is also skipped
        list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

        assert instance.get_run_by_id(BAD_USER_CODE_RUN_ID_UUID).status == DagsterRunStatus.QUEUED
        assert instance.get_run_by_id(good_run_same_location_id).status == DagsterRunStatus.QUEUED

        fixed_iteration_time = fixed_iteration_time + 121

        list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

        assert instance.get_run_by_id(BAD_USER_CODE_RUN_ID_UUID).status == DagsterRunStatus.QUEUED

        fixed_iteration_time = fixed_iteration_time + 121

        # Gives up after max_user_code_failure_retries retries _ the good run from that
        # location succeeds

        list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

        assert instance.get_run_by_id(BAD_USER_CODE_RUN_ID_UUID).status == DagsterRunStatus.FAILURE

        fixed_iteration_time = fixed_iteration_time + 121

        list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

        # good run is now free to launch (since it is dequeud before the bad run due to), bad run does its second retry
        assert self.get_run_ids(instance.run_launcher.queue()) == [
            good_run_id,
            good_run_other_location_id,
            good_run_same_location_id,
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
            run_id=BAD_USER_CODE_RUN_ID_UUID,
        )

        # fails on initial dequeue

        list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

        assert instance.get_run_by_id(BAD_USER_CODE_RUN_ID_UUID).status == DagsterRunStatus.QUEUED

        fixed_iteration_time = fixed_iteration_time + 6

        # Passes on retry

        instance.run_launcher.bad_user_code_run_ids = set()

        list(daemon.run_iteration(workspace_context, fixed_iteration_time=fixed_iteration_time))

        assert self.get_run_ids(instance.run_launcher.queue()) == [BAD_USER_CODE_RUN_ID_UUID]

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
        run_id_1 = make_new_run_id()
        run_id_2 = make_new_run_id()
        self.create_queued_run(
            instance,
            job_handle,
            run_id=run_id_1,
            tags={"other-tag": "value", "test": "value"},
        )

        self.create_queued_run(
            instance,
            job_handle,
            run_id=run_id_2,
            tags={"other-tag": "value", "test": "value"},
        )

        list(daemon.run_iteration(workspace_context))
        assert self.get_run_ids(instance.run_launcher.queue()) == [run_id_1]

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
        lo_pri_run_id, hi_pri_run_id = [make_new_run_id() for _ in range(2)]
        self.create_queued_run(
            instance,
            job_handle,
            run_id=lo_pri_run_id,
            tags={"test": "value", PRIORITY_TAG: "-100"},
        )
        self.create_queued_run(
            instance,
            job_handle,
            run_id=hi_pri_run_id,
            tags={"test": "value", PRIORITY_TAG: "100"},
        )

        list(daemon.run_iteration(workspace_context))
        assert self.get_run_ids(instance.run_launcher.queue()) == [hi_pri_run_id]

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            {"block_op_concurrency_limited_runs": {"enabled": True}},
        ],
    )
    def test_op_concurrency_aware_dequeuing(
        self,
        concurrency_limited_workspace_context,
        daemon,
        instance,
        caplog,
    ):
        run_id_1, run_id_2, run_id_3 = [make_new_run_id() for _ in range(3)]
        workspace = concurrency_limited_workspace_context.create_request_context()
        external_job = self.get_external_concurrency_job(workspace)
        foo_key = AssetKey(["prefix", "foo_limited_asset"])

        self.submit_run(
            instance, external_job, workspace, run_id=run_id_1, asset_selection=set([foo_key])
        )

        instance.event_log_storage.set_concurrency_slots("foo", 1)
        list(daemon.run_iteration(concurrency_limited_workspace_context))
        assert set(self.get_run_ids(instance.run_launcher.queue())) == set([run_id_1])
        caplog.text.count("is blocked by global concurrency limits") == 0

        self.submit_run(
            instance, external_job, workspace, run_id=run_id_2, asset_selection=set([foo_key])
        )
        list(daemon.run_iteration(concurrency_limited_workspace_context))
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {run_id_1}
        caplog.text.count(f"Run {run_id_2} is blocked by global concurrency limits") == 1

        self.submit_run(
            instance, external_job, workspace, run_id=run_id_3, asset_selection=set([foo_key])
        )
        list(daemon.run_iteration(concurrency_limited_workspace_context))
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {run_id_1}
        # the log message only shows up once per run
        caplog.text.count(f"Run {run_id_2} is blocked by global concurrency limits") == 1
        caplog.text.count(f"Run {run_id_3} is blocked by global concurrency limits") == 1

        # bumping up the slot by one means that one more run should get dequeued
        instance.event_log_storage.set_concurrency_slots("foo", 2)
        list(daemon.run_iteration(concurrency_limited_workspace_context))
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {run_id_1, run_id_2}
        caplog.text.count(f"Run {run_id_2} is blocked by global concurrency limits") == 1
        caplog.text.count(f"Run {run_id_3} is blocked by global concurrency limits") == 1

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            {"block_op_concurrency_limited_runs": {"enabled": True}},
        ],
    )
    def test_op_concurrency_root_progress(
        self,
        concurrency_limited_workspace_context,
        daemon,
        instance,
    ):
        run_id_1, run_id_2 = [make_new_run_id() for _ in range(2)]
        workspace = concurrency_limited_workspace_context.create_request_context()
        external_job = self.get_external_concurrency_job(workspace)
        foo_key = AssetKey(["prefix", "foo_limited_asset"])
        bar_key = AssetKey(["prefix", "bar_limited_asset"])

        # foo is blocked, but bar is not
        instance.event_log_storage.set_concurrency_slots("foo", 0)
        instance.event_log_storage.set_concurrency_slots("bar", 1)

        self.submit_run(
            instance, external_job, workspace, run_id=run_id_1, asset_selection=set([foo_key])
        )
        list(daemon.run_iteration(concurrency_limited_workspace_context))
        assert set(self.get_run_ids(instance.run_launcher.queue())) == set()

        self.submit_run(
            instance, external_job, workspace, run_id=run_id_2, asset_selection=set([bar_key])
        )
        list(daemon.run_iteration(concurrency_limited_workspace_context))
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {run_id_2}

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            {"block_op_concurrency_limited_runs": {"enabled": True}},
        ],
    )
    def test_op_concurrency_partial_root(
        self,
        concurrency_limited_workspace_context,
        daemon,
        instance,
    ):
        run_id_1 = make_new_run_id()
        workspace = concurrency_limited_workspace_context.create_request_context()
        external_job = workspace.get_full_job(
            JobSubsetSelector(
                location_name="test",
                repository_name="__repository__",
                job_name="partial_concurrency_limited_multi_root_job",
                op_selection=None,
            )
        )

        instance.event_log_storage.set_concurrency_slots("foo", 0)
        self.submit_run(instance, external_job, workspace, run_id=run_id_1)
        list(daemon.run_iteration(concurrency_limited_workspace_context))
        # is not blocked because there's an unconstrained node at the root
        assert set(self.get_run_ids(instance.run_launcher.queue())) == {run_id_1}

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            {"block_op_concurrency_limited_runs": {"enabled": True}},
        ],
    )
    def test_in_progress_root_key_accounting(
        self,
        concurrency_limited_workspace_context,
        daemon,
        instance,
    ):
        run_id_1, run_id_2 = [make_new_run_id() for _ in range(2)]
        workspace = concurrency_limited_workspace_context.create_request_context()
        foo_key = AssetKey(["prefix", "foo_limited_asset"])
        external_job = self.get_external_concurrency_job(workspace)
        self.submit_run(
            instance, external_job, workspace, run_id=run_id_1, asset_selection=set([foo_key])
        )
        self.submit_run(
            instance, external_job, workspace, run_id=run_id_2, asset_selection=set([foo_key])
        )
        instance.event_log_storage.set_concurrency_slots("foo", 1)
        with environ({"DAGSTER_OP_CONCURRENCY_KEYS_ALLOTTED_FOR_STARTED_RUN_SECONDS": "0"}):
            list(daemon.run_iteration(concurrency_limited_workspace_context))
            assert set(self.get_run_ids(instance.run_launcher.queue())) == set([run_id_1])
            list(daemon.run_iteration(concurrency_limited_workspace_context))
            assert set(self.get_run_ids(instance.run_launcher.queue())) == set([run_id_1])
            assert instance.get_run_by_id(run_id_1).status == DagsterRunStatus.STARTING
            instance.handle_run_event(
                run_id_1,
                DagsterEvent(
                    event_type_value=DagsterEventType.RUN_START,
                    job_name="concurrency_limited_asset_job",
                    message="start that run",
                ),
            )
            assert instance.get_run_by_id(run_id_1).status == DagsterRunStatus.STARTED
            list(daemon.run_iteration(concurrency_limited_workspace_context))
            assert set(self.get_run_ids(instance.run_launcher.queue())) == set([run_id_1, run_id_2])

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            {
                "block_op_concurrency_limited_runs": {
                    "enabled": True,
                    "op_concurrency_slot_buffer": 1,
                }
            },
        ],
    )
    def test_op_concurrency_aware_slot_buffer(
        self,
        concurrency_limited_workspace_context,
        daemon,
        instance,
    ):
        run_id_1, run_id_2, run_id_3 = [make_new_run_id() for _ in range(3)]
        workspace = concurrency_limited_workspace_context.create_request_context()
        foo_key = AssetKey(["prefix", "foo_limited_asset"])
        external_job = self.get_external_concurrency_job(workspace)
        self.submit_run(
            instance, external_job, workspace, run_id=run_id_1, asset_selection=set([foo_key])
        )
        self.submit_run(
            instance, external_job, workspace, run_id=run_id_2, asset_selection=set([foo_key])
        )
        self.submit_run(
            instance, external_job, workspace, run_id=run_id_3, asset_selection=set([foo_key])
        )
        instance.event_log_storage.set_concurrency_slots("foo", 1)
        list(daemon.run_iteration(concurrency_limited_workspace_context))
        assert set(self.get_run_ids(instance.run_launcher.queue())) == set([run_id_1, run_id_2])
        list(daemon.run_iteration(concurrency_limited_workspace_context))
        assert set(self.get_run_ids(instance.run_launcher.queue())) == set([run_id_1, run_id_2])

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            {"block_op_concurrency_limited_runs": {"enabled": True}},
        ],
    )
    def test_op_concurrency_aware_started_allottment_time(
        self,
        concurrency_limited_workspace_context,
        daemon,
        instance,
    ):
        run_id_1, run_id_2, run_id_3 = [make_new_run_id() for _ in range(3)]
        workspace = concurrency_limited_workspace_context.create_request_context()
        foo_key = AssetKey(["prefix", "foo_limited_asset"])
        external_job = self.get_external_concurrency_job(workspace)
        self.submit_run(
            instance, external_job, workspace, run_id=run_id_1, asset_selection=set([foo_key])
        )
        self.submit_run(
            instance, external_job, workspace, run_id=run_id_2, asset_selection=set([foo_key])
        )
        self.submit_run(
            instance, external_job, workspace, run_id=run_id_3, asset_selection=set([foo_key])
        )
        instance.event_log_storage.set_concurrency_slots("foo", 1)
        list(daemon.run_iteration(concurrency_limited_workspace_context))
        assert set(self.get_run_ids(instance.run_launcher.queue())) == set([run_id_1])
        freeze_datetime = create_datetime(year=2024, month=2, day=21)
        with environ({"DAGSTER_OP_CONCURRENCY_KEYS_ALLOTTED_FOR_STARTED_RUN_SECONDS": "1"}):
            with freeze_time(freeze_datetime):
                assert instance.get_run_by_id(run_id_1).status == DagsterRunStatus.STARTING
                instance.handle_run_event(
                    run_id_1,
                    DagsterEvent(
                        event_type_value=DagsterEventType.RUN_START,
                        job_name="concurrency_limited_asset_job",
                        message="start that run",
                    ),
                )
                assert instance.get_run_by_id(run_id_1).status == DagsterRunStatus.STARTED
                assert (
                    instance.get_run_record_by_id(run_id_1).start_time
                    == freeze_datetime.timestamp()
                )
                list(daemon.run_iteration(concurrency_limited_workspace_context))
                # even though run-1 is started, it still occupies one of the foo "slots" in the run
                # coordinator accounting because the env var is set to wait for at 1 second after
                # the run has started
                assert set(self.get_run_ids(instance.run_launcher.queue())) == set([run_id_1])

            freeze_datetime = freeze_datetime + datetime.timedelta(seconds=2)

            with freeze_time(freeze_datetime):
                # we are now out of the 1-second window for having run-1 account for slots in the
                # run coordinator
                list(daemon.run_iteration(concurrency_limited_workspace_context))
                assert set(self.get_run_ids(instance.run_launcher.queue())) == set(
                    [run_id_1, run_id_2]
                )

    @pytest.mark.parametrize(
        "run_coordinator_config",
        [
            {
                "tag_concurrency_limits": [{"key": "database", "value": "tiny", "limit": 0}],
                "block_op_concurrency_limited_runs": {"enabled": True},
            },
        ],
    )
    def test_multiple_blocks(
        self,
        concurrency_limited_workspace_context,
        daemon,
        instance,
    ):
        run_id_1 = make_new_run_id()
        workspace = concurrency_limited_workspace_context.create_request_context()
        external_job = self.get_external_concurrency_job(workspace)
        foo_key = AssetKey(["prefix", "foo_limited_asset"])

        # foo is blocked, but bar is not
        instance.event_log_storage.set_concurrency_slots("foo", 0)

        self.submit_run(
            instance,
            external_job,
            workspace,
            run_id=run_id_1,
            asset_selection=set([foo_key]),
            tags={"database": "tiny"},
        )
        list(daemon.run_iteration(concurrency_limited_workspace_context))
        assert set(self.get_run_ids(instance.run_launcher.queue())) == set()


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
                    "bad_run_ids": [BAD_RUN_ID_UUID],
                    "bad_user_code_run_ids": [BAD_USER_CODE_RUN_ID_UUID],
                },
            },
        }

        with instance_for_test(overrides=overrides) as instance:
            yield instance

    @pytest.fixture()
    def daemon(self, page_size):
        return QueuedRunCoordinatorDaemon(interval_seconds=1, page_size=page_size)
