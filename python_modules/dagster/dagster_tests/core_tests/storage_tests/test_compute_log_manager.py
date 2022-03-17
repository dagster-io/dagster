import tempfile
from contextlib import contextmanager

from dagster import check, job, op
from dagster.core.instance import DagsterInstance, InstanceRef, InstanceType
from dagster.core.launcher import DefaultRunLauncher
from dagster.core.run_coordinator import DefaultRunCoordinator
from dagster.core.storage.compute_log_manager import (
    MAX_BYTES_FILE_READ,
    ComputeLogFileData,
    ComputeLogManager,
)
from dagster.core.storage.event_log import SqliteEventLogStorage
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import SqliteRunStorage
from dagster.core.test_utils import environ, instance_for_test


def test_compute_log_manager_instance():
    with instance_for_test() as instance:
        assert instance.compute_log_manager
        assert instance.compute_log_manager._instance  # pylint: disable=protected-access


class BrokenComputeLogManager(ComputeLogManager):
    def __init__(self, fail_on_setup=False, fail_on_teardown=False):
        self._fail_on_setup = check.opt_bool_param(fail_on_setup, "fail_on_setup")
        self._fail_on_teardown = check.opt_bool_param(fail_on_teardown, "fail_on_teardown")

    @contextmanager
    def _watch_logs(self, pipeline_run, step_key=None):
        yield

    def is_watch_completed(self, run_id, key):
        return True

    def on_watch_start(self, pipeline_run, step_key):
        if self._fail_on_setup:
            raise Exception("wahhh")

    def on_watch_finish(self, pipeline_run, step_key):
        if self._fail_on_teardown:
            raise Exception("blahhh")

    def download_url(self, run_id, key, io_type):
        return None

    def read_logs_file(self, run_id, key, io_type, cursor=0, max_bytes=MAX_BYTES_FILE_READ):
        return ComputeLogFileData(
            path="{}.{}".format(key, io_type), data=None, cursor=0, size=0, download_url=None
        )

    def on_subscribe(self, subscription):
        pass


@contextmanager
def broken_compute_log_manager_instance(fail_on_setup=False, fail_on_teardown=False):
    with tempfile.TemporaryDirectory() as temp_dir:
        with environ({"DAGSTER_HOME": temp_dir}):
            yield DagsterInstance(
                instance_type=InstanceType.PERSISTENT,
                local_artifact_storage=LocalArtifactStorage(temp_dir),
                run_storage=SqliteRunStorage.from_local(temp_dir),
                event_storage=SqliteEventLogStorage(temp_dir),
                compute_log_manager=BrokenComputeLogManager(
                    fail_on_setup=fail_on_setup, fail_on_teardown=fail_on_teardown
                ),
                run_coordinator=DefaultRunCoordinator(),
                run_launcher=DefaultRunLauncher(),
                ref=InstanceRef.from_dir(temp_dir),
            )


def _has_setup_exception(execute_result):
    return any(
        [
            "Exception while setting up compute log capture" in str(event)
            for event in execute_result.all_events
        ]
    )


def _has_teardown_exception(execute_result):
    return any(
        [
            "Exception while cleaning up compute log capture" in str(event)
            for event in execute_result.all_events
        ]
    )


def test_broken_compute_log_manager():
    @op
    def yay(context):
        context.log.info("yay")
        print("HELLOOO")  # pylint: disable=print-call
        return "yay"

    @op
    def boo(context):
        context.log.info("boo")
        print("HELLOOO")  # pylint: disable=print-call
        raise Exception("booo")

    @job
    def yay_job():
        yay()

    @job
    def boo_job():
        boo()

    with broken_compute_log_manager_instance(fail_on_setup=True) as instance:
        yay_result = yay_job.execute_in_process(instance=instance)
        assert yay_result.success
        assert _has_setup_exception(yay_result)

        boo_result = boo_job.execute_in_process(instance=instance, raise_on_error=False)
        assert not boo_result.success
        assert _has_setup_exception(boo_result)

    with broken_compute_log_manager_instance(fail_on_teardown=True) as instance:
        yay_result = yay_job.execute_in_process(instance=instance)
        assert yay_result.success
        assert _has_teardown_exception(yay_result)

        boo_result = boo_job.execute_in_process(instance=instance, raise_on_error=False)

        assert not boo_result.success
        assert _has_teardown_exception(boo_result)

    with broken_compute_log_manager_instance() as instance:
        yay_result = yay_job.execute_in_process(instance=instance)
        assert yay_result.success
        assert not _has_setup_exception(yay_result)
        assert not _has_teardown_exception(yay_result)

        boo_result = boo_job.execute_in_process(instance=instance, raise_on_error=False)
        assert not boo_result.success
        assert not _has_setup_exception(boo_result)
        assert not _has_teardown_exception(boo_result)
