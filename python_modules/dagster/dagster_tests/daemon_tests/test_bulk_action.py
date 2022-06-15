import time

from dagster.core.execution.bulk_actions import (
    BulkAction,
    BulkActionStatus,
    BulkActionType,
    RunTerminationAction,
)
from dagster.core.launcher.base import RunLauncher
from dagster.core.storage.pipeline_run import DagsterRunStatus, RunsFilter
from dagster.core.test_utils import create_run_for_test, instance_for_test
from dagster.core.utils import make_new_run_id
from dagster.daemon import get_default_daemon_logger
from dagster.daemon.bulk_action import execute_bulk_action_iteration
from dagster.serdes.config_class import ConfigurableClass


class TestRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data=None):
        self._inst_data = inst_data
        self.launch_run_calls = 0
        self.resume_run_calls = 0
        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return TestRunLauncher(inst_data=inst_data)

    def launch_run(self, context):
        raise NotImplementedError()

    def resume_run(self, context):
        raise NotImplementedError()

    def join(self, timeout=30):
        pass

    def terminate(self, run_id):
        self._instance.report_run_canceled(self._instance.get_run_by_id(run_id))

    @property
    def supports_resume_run(self):
        return True

    @property
    def supports_check_run_worker_health(self):
        return True

    def check_run_worker_health(self, _run):
        raise NotImplementedError()


def test_bulk_action():
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_tests.daemon_tests.test_bulk_action",
                "class": "TestRunLauncher",
            }
        }
    ) as instance:
        list(
            execute_bulk_action_iteration(instance, get_default_daemon_logger("BulkActionsDaemon"))
        )

        instance.run_storage.add_bulk_action(
            BulkAction(
                "foo",
                BulkActionType.RUN_TERMINATION,
                BulkActionStatus.REQUESTED,
                time.time(),
                RunTerminationAction(RunsFilter(statuses=[DagsterRunStatus.QUEUED])),
            )
        )

        list(
            execute_bulk_action_iteration(instance, get_default_daemon_logger("BulkActionsDaemon"))
        )

        assert instance.run_storage.get_bulk_action("foo").status == BulkActionStatus.COMPLETED

        starting_runs = [
            create_run_for_test(
                instance, make_new_run_id(), status=DagsterRunStatus.STARTING
            ).run_id
            for _ in range(20)
        ]

        started_runs = [
            create_run_for_test(instance, make_new_run_id(), status=DagsterRunStatus.STARTED).run_id
            for _ in range(20)
        ]

        instance.run_storage.add_bulk_action(
            BulkAction(
                "bar",
                BulkActionType.RUN_TERMINATION,
                BulkActionStatus.REQUESTED,
                time.time(),
                RunTerminationAction(RunsFilter(statuses=[DagsterRunStatus.STARTED])),
            )
        )

        list(
            execute_bulk_action_iteration(instance, get_default_daemon_logger("BulkActionsDaemon"))
        )

        assert instance.run_storage.get_bulk_action("bar").status == BulkActionStatus.COMPLETED

        assert all(
            instance.get_run_by_id(run_id).status == DagsterRunStatus.STARTING
            for run_id in starting_runs
        )
        assert all(
            instance.get_run_by_id(run_id).status == DagsterRunStatus.CANCELED
            for run_id in started_runs
        )
