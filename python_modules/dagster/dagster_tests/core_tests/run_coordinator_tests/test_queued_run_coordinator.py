from typing import Iterator

import pytest
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.events import DagsterEventType
from dagster._core.host_representation.external import ExternalJob
from dagster._core.instance import DagsterInstance
from dagster._core.run_coordinator import SubmitRunContext
from dagster._core.run_coordinator.queued_run_coordinator import QueuedRunCoordinator
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.test_utils import create_run_for_test, environ, instance_for_test
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._utils.merger import merge_dicts

from dagster_tests.api_tests.utils import get_bar_workspace


class TestQueuedRunCoordinator:
    """You can extend this class to easily run these set of tests on any custom run coordinator
    that subclasses the QueuedRunCoordinator. When extending, you simply need to override the
    `coordinator` fixture and return your implementation of `QueuedRunCoordinator`.

    For example:

    ```
    class TestMyRunCoordinator(TestQueuedRunCoordinator):
        @pytest.fixture(scope='function')
        def coordinator(self, instance):
            run_coordinator = MyRunCoordinator()
            run_coordinator.register_instance(instance)
            yield run_coordinator
    ```
    """

    @pytest.fixture
    def instance(self) -> Iterator[DagsterInstance]:
        overrides = {
            "run_launcher": {"module": "dagster._core.test_utils", "class": "MockedRunLauncher"}
        }
        with instance_for_test(overrides=overrides) as inst:
            yield inst

    @pytest.fixture
    def coordinator(self, instance: DagsterInstance) -> Iterator[QueuedRunCoordinator]:
        run_coordinator = QueuedRunCoordinator()
        run_coordinator.register_instance(instance)
        yield run_coordinator

    @pytest.fixture(name="workspace")
    def workspace_fixture(self, instance: DagsterInstance) -> Iterator[WorkspaceRequestContext]:
        with get_bar_workspace(instance) as workspace:
            yield workspace

    @pytest.fixture(name="external_pipeline")
    def external_job_fixture(self, workspace: WorkspaceRequestContext) -> ExternalJob:
        location = workspace.get_code_location("bar_code_location")
        return location.get_repository("bar_repo").get_full_external_job("foo")

    def create_run_for_test(
        self, instance: DagsterInstance, external_pipeline: ExternalJob, **kwargs: object
    ) -> DagsterRun:
        job_args = merge_dicts(
            {
                "job_name": "foo",
                "external_job_origin": external_pipeline.get_external_origin(),
                "job_code_origin": external_pipeline.get_python_origin(),
            },
            kwargs,
        )
        return create_run_for_test(instance, **job_args)

    def test_config(self):
        with environ({"MAX_RUNS": "10", "DEQUEUE_INTERVAL": "7"}):
            with instance_for_test(
                overrides={
                    "run_coordinator": {
                        "module": "dagster._core.run_coordinator",
                        "class": "QueuedRunCoordinator",
                        "config": {
                            "max_concurrent_runs": {
                                "env": "MAX_RUNS",
                            },
                            "tag_concurrency_limits": [
                                {"key": "foo", "value": "bar", "limit": 3},
                                {"key": "backfill", "limit": 2},
                            ],
                            "dequeue_interval_seconds": {
                                "env": "DEQUEUE_INTERVAL",
                            },
                            "block_op_concurrency_limited_runs": True,
                        },
                    }
                }
            ) as _:
                pass

        with pytest.raises(DagsterInvalidConfigError):
            with instance_for_test(
                overrides={
                    "run_coordinator": {
                        "module": "dagster._core.run_coordinator",
                        "class": "QueuedRunCoordinator",
                        "config": {
                            "tag_concurrency_limits": [
                                {"key": "backfill"},
                            ],
                        },
                    }
                }
            ) as instance:
                print(instance.run_coordinator)  # noqa: T201

    def test_config_unique_value(self):
        with environ({"MAX_RUNS": "10", "DEQUEUE_INTERVAL": "7"}):
            with instance_for_test(
                overrides={
                    "run_coordinator": {
                        "module": "dagster._core.run_coordinator",
                        "class": "QueuedRunCoordinator",
                        "config": {
                            "max_concurrent_runs": {
                                "env": "MAX_RUNS",
                            },
                            "tag_concurrency_limits": [
                                {
                                    "key": "foo",
                                    "value": {"applyLimitPerUniqueValue": True},
                                    "limit": 3,
                                },
                                {"key": "backfill", "limit": 2},
                            ],
                            "dequeue_interval_seconds": {
                                "env": "DEQUEUE_INTERVAL",
                            },
                        },
                    }
                }
            ) as _:
                pass

    def test_submit_run(self, instance, coordinator, workspace, external_pipeline):
        run = self.create_run_for_test(
            instance, external_pipeline, run_id="foo-1", status=DagsterRunStatus.NOT_STARTED
        )
        returned_run = coordinator.submit_run(SubmitRunContext(run, workspace))
        assert returned_run.run_id == "foo-1"
        assert returned_run.status == DagsterRunStatus.QUEUED

        assert len(instance.run_launcher.queue()) == 0
        stored_run = instance.get_run_by_id("foo-1")
        assert stored_run.status == DagsterRunStatus.QUEUED

    def test_submit_run_checks_status(self, instance, coordinator, workspace, external_pipeline):
        run = self.create_run_for_test(
            instance, external_pipeline, run_id="foo-1", status=DagsterRunStatus.QUEUED
        )
        coordinator.submit_run(SubmitRunContext(run, workspace))

        # check that no enqueue event is reported (the submit run call is a no-op)
        assert (
            len(
                instance.get_records_for_run(
                    "foo-1", of_type=DagsterEventType.PIPELINE_ENQUEUED
                ).records
            )
            == 0
        )

    def test_cancel_run(self, instance, coordinator, workspace, external_pipeline):
        run = self.create_run_for_test(
            instance, external_pipeline, run_id="foo-1", status=DagsterRunStatus.NOT_STARTED
        )

        coordinator.submit_run(SubmitRunContext(run, workspace))

        coordinator.cancel_run(run.run_id)
        stored_run = instance.get_run_by_id("foo-1")
        assert stored_run.status == DagsterRunStatus.CANCELED


def test_thread_config():
    num = 16
    with instance_for_test(
        overrides={
            "run_coordinator": {
                "module": "dagster._core.run_coordinator",
                "class": "QueuedRunCoordinator",
                "config": {
                    "dequeue_use_threads": True,
                    "dequeue_num_workers": num,
                },
            }
        }
    ) as instance:
        assert instance.run_coordinator.dequeue_num_workers == num
