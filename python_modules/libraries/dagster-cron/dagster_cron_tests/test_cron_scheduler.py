import os
import re
import subprocess
import sys
from contextlib import contextmanager
from tempfile import TemporaryDirectory

import pytest
import yaml
from dagster import ScheduleDefinition
from dagster.core.definitions import lambda_solid, pipeline, repository
from dagster.core.host_representation import ManagedGrpcPythonEnvRepositoryLocationOrigin
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.run_coordinator import DefaultRunCoordinator
from dagster.core.scheduler.job import JobState, JobStatus, JobType, ScheduleJobData
from dagster.core.scheduler.scheduler import (
    DagsterScheduleDoesNotExist,
    DagsterScheduleReconciliationError,
    DagsterSchedulerError,
)
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.core.storage.schedules import SqliteScheduleStorage
from dagster.core.test_utils import environ
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.seven import get_current_datetime_in_utc, get_timestamp_from_utc_datetime
from dagster_cron import SystemCronScheduler
from freezegun import freeze_time


@pytest.fixture(scope="function")
def restore_cron_tab():
    with TemporaryDirectory() as tempdir:
        crontab_backup = os.path.join(tempdir, "crontab_backup.txt")
        with open(crontab_backup, "wb+") as f:
            try:
                output = subprocess.check_output(["crontab", "-l"])
                f.write(output)
            except subprocess.CalledProcessError:
                # If a crontab hasn't been created yet, the command fails with a
                # non-zero error code
                pass

        try:
            subprocess.check_output(["crontab", "-r"])
        except subprocess.CalledProcessError:
            # If a crontab hasn't been created yet, the command fails with a
            # non-zero error code
            pass

        yield

        subprocess.check_output(["crontab", crontab_backup])


@pytest.fixture(scope="function")
def unset_dagster_home():
    old_env = os.getenv("DAGSTER_HOME")
    if old_env is not None:
        del os.environ["DAGSTER_HOME"]
    yield
    if old_env is not None:
        os.environ["DAGSTER_HOME"] = old_env


@pipeline
def no_config_pipeline():
    @lambda_solid
    def return_hello():
        return "Hello"

    return return_hello()


schedules_dict = {
    "no_config_pipeline_daily_schedule": ScheduleDefinition(
        name="no_config_pipeline_daily_schedule",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        run_config={"intermediate_storage": {"filesystem": None}},
    ),
    "no_config_pipeline_every_min_schedule": ScheduleDefinition(
        name="no_config_pipeline_every_min_schedule",
        cron_schedule="* * * * *",
        pipeline_name="no_config_pipeline",
        run_config={"intermediate_storage": {"filesystem": None}},
    ),
    "default_config_pipeline_every_min_schedule": ScheduleDefinition(
        name="default_config_pipeline_every_min_schedule",
        cron_schedule="* * * * *",
        pipeline_name="no_config_pipeline",
    ),
}


def define_schedules():
    return list(schedules_dict.values())


@repository
def test_repository():
    if os.getenv("DAGSTER_TEST_SMALL_REPO"):
        return [no_config_pipeline] + list(
            filter(
                lambda x: not x.name == "default_config_pipeline_every_min_schedule",
                define_schedules(),
            )
        )

    return [no_config_pipeline] + define_schedules()


@contextmanager
def get_test_external_repo():
    with ManagedGrpcPythonEnvRepositoryLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            python_file=__file__,
            attribute="test_repository",
        ),
        location_name="test_location",
    ).create_handle() as handle:
        yield handle.create_location().get_repository("test_repository")


@contextmanager
def get_smaller_external_repo():
    with environ({"DAGSTER_TEST_SMALL_REPO": "1"}):
        with get_test_external_repo() as repo:
            yield repo


def get_cron_jobs():
    output = subprocess.check_output(["crontab", "-l"])
    return list(filter(None, output.decode("utf-8").strip().split("\n")))


def define_scheduler_instance(tempdir):
    return DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(tempdir),
        run_storage=InMemoryRunStorage(),
        event_storage=InMemoryEventLogStorage(),
        compute_log_manager=NoOpComputeLogManager(),
        schedule_storage=SqliteScheduleStorage.from_local(os.path.join(tempdir, "schedules")),
        scheduler=SystemCronScheduler(),
        run_coordinator=DefaultRunCoordinator(),
        run_launcher=SyncInMemoryRunLauncher(),
    )


def test_init(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repository:
            # Initialize scheduler
            instance.reconcile_scheduler_state(external_repository)

            # Check schedules are saved to disk
            assert "schedules" in os.listdir(tempdir)

            assert instance.all_stored_job_state(job_type=JobType.SCHEDULE)


@freeze_time("2019-02-27")
def test_re_init(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:

            now = get_current_datetime_in_utc()
            # Start schedule
            schedule_state = instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
            )

            assert (
                schedule_state.job_specific_data.start_timestamp
                == get_timestamp_from_utc_datetime(now)
            )

            # Check schedules are saved to disk
            assert "schedules" in os.listdir(tempdir)

            schedule_states = instance.all_stored_job_state(job_type=JobType.SCHEDULE)

            for state in schedule_states:
                assert state.job_specific_data.scheduler == "SystemCronScheduler"
                if state.name == "no_config_pipeline_every_min_schedule":
                    assert state == schedule_state


@pytest.mark.parametrize("do_initial_reconcile", [True, False])
def test_start_and_stop_schedule(
    restore_cron_tab,
    do_initial_reconcile,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:

            if do_initial_reconcile:
                instance.reconcile_scheduler_state(external_repo)

            schedule = external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
            schedule_origin_id = schedule.get_external_origin_id()

            instance.start_schedule_and_update_storage_state(schedule)

            assert "schedules" in os.listdir(tempdir)

            assert "{}.sh".format(schedule_origin_id) in os.listdir(
                os.path.join(tempdir, "schedules", "scripts")
            )

            instance.stop_schedule_and_update_storage_state(schedule_origin_id)

            assert "{}.sh".format(schedule_origin_id) not in os.listdir(
                os.path.join(tempdir, "schedules", "scripts")
            )


def test_start_non_existent_schedule(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        with pytest.raises(DagsterScheduleDoesNotExist):
            instance.stop_schedule_and_update_storage_state("asdf")


@pytest.mark.parametrize("do_initial_reconcile", [True, False])
def test_start_schedule_cron_job(
    do_initial_reconcile,
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:

            if do_initial_reconcile:
                instance.reconcile_scheduler_state(external_repo)

            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
            )
            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_daily_schedule")
            )
            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("default_config_pipeline_every_min_schedule")
            )

            # Inspect the cron tab
            cron_jobs = get_cron_jobs()

            assert len(cron_jobs) == 3

            external_schedules_dict = {
                external_repo.get_external_schedule(name).get_external_origin_id(): schedule_def
                for name, schedule_def in schedules_dict.items()
            }

            for cron_job in cron_jobs:
                match = re.findall(r"^(.*?) (/.*) > (.*) 2>&1 # dagster-schedule: (.*)", cron_job)
                cron_schedule, command, log_file, schedule_origin_id = match[0]

                schedule_def = external_schedules_dict[schedule_origin_id]

                # Check cron schedule matches
                if schedule_def.cron_schedule == "0 0 * * *":
                    assert cron_schedule == "@daily"
                else:
                    assert cron_schedule == schedule_def.cron_schedule

                # Check bash file exists
                assert os.path.isfile(command)

                # Check log file is correct
                assert log_file.endswith("scheduler.log")


def test_remove_schedule_def(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:
            instance.reconcile_scheduler_state(external_repo)

            assert len(instance.all_stored_job_state(job_type=JobType.SCHEDULE)) == 3
            with get_smaller_external_repo() as smaller_repo:
                instance.reconcile_scheduler_state(smaller_repo)

            assert len(instance.all_stored_job_state(job_type=JobType.SCHEDULE)) == 2


def test_add_schedule_def(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_smaller_external_repo() as external_repo:

            # Start all schedule and verify cron tab, schedule storage, and errors
            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_daily_schedule")
            )
            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
            )

            assert len(instance.all_stored_job_state(job_type=JobType.SCHEDULE)) == 2
            assert len(get_cron_jobs()) == 2
            assert len(instance.scheduler_debug_info().errors) == 0

        with get_test_external_repo() as external_repo:

            # Reconcile with an additional schedule added
            instance.reconcile_scheduler_state(external_repo)

            assert len(instance.all_stored_job_state(job_type=JobType.SCHEDULE)) == 3
            assert len(get_cron_jobs()) == 2
            assert len(instance.scheduler_debug_info().errors) == 0

            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("default_config_pipeline_every_min_schedule")
            )

            assert len(instance.all_stored_job_state(job_type=JobType.SCHEDULE)) == 3
            assert len(get_cron_jobs()) == 3
            assert len(instance.scheduler_debug_info().errors) == 0


def test_start_and_stop_schedule_cron_tab(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:
            # Start schedule
            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
            )
            cron_jobs = get_cron_jobs()
            assert len(cron_jobs) == 1

            # Try starting it again
            with pytest.raises(DagsterSchedulerError):
                instance.start_schedule_and_update_storage_state(
                    external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
                )
            cron_jobs = get_cron_jobs()
            assert len(cron_jobs) == 1

            # Start another schedule
            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_daily_schedule")
            )
            cron_jobs = get_cron_jobs()
            assert len(cron_jobs) == 2

            # Stop second schedule
            instance.stop_schedule_and_update_storage_state(
                external_repo.get_external_schedule(
                    "no_config_pipeline_daily_schedule"
                ).get_external_origin_id()
            )
            cron_jobs = get_cron_jobs()
            assert len(cron_jobs) == 1

            # Try stopping second schedule again
            instance.stop_schedule_and_update_storage_state(
                external_repo.get_external_schedule(
                    "no_config_pipeline_daily_schedule"
                ).get_external_origin_id()
            )
            cron_jobs = get_cron_jobs()
            assert len(cron_jobs) == 1

            # Start second schedule
            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_daily_schedule")
            )
            cron_jobs = get_cron_jobs()
            assert len(cron_jobs) == 2

            # Reconcile schedule state, should be in the same state
            instance.reconcile_scheduler_state(external_repo)
            cron_jobs = get_cron_jobs()
            assert len(cron_jobs) == 2

            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("default_config_pipeline_every_min_schedule")
            )
            cron_jobs = get_cron_jobs()
            assert len(cron_jobs) == 3

            # Reconcile schedule state, should be in the same state
            instance.reconcile_scheduler_state(external_repo)
            cron_jobs = get_cron_jobs()
            assert len(cron_jobs) == 3

            # Stop all schedules
            instance.stop_schedule_and_update_storage_state(
                external_repo.get_external_schedule(
                    "no_config_pipeline_every_min_schedule"
                ).get_external_origin_id()
            )
            instance.stop_schedule_and_update_storage_state(
                external_repo.get_external_schedule(
                    "no_config_pipeline_daily_schedule"
                ).get_external_origin_id()
            )
            instance.stop_schedule_and_update_storage_state(
                external_repo.get_external_schedule(
                    "default_config_pipeline_every_min_schedule"
                ).get_external_origin_id()
            )

            cron_jobs = get_cron_jobs()
            assert len(cron_jobs) == 0

            # Reconcile schedule state, should be in the same state
            instance.reconcile_scheduler_state(external_repo)
            cron_jobs = get_cron_jobs()
            assert len(cron_jobs) == 0


def test_script_execution(
    restore_cron_tab, unset_dagster_home
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        os.environ["DAGSTER_HOME"] = tempdir
        config = {
            "scheduler": {"module": "dagster_cron", "class": "SystemCronScheduler", "config": {}},
            # This needs to synchronously execute to completion when
            # the generated bash script is invoked
            "run_launcher": {
                "module": "dagster.core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            },
        }

        with open(os.path.join(tempdir, "dagster.yaml"), "w+") as f:
            f.write(yaml.dump(config))

        instance = DagsterInstance.get()
        with get_test_external_repo() as external_repo:
            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
            )

            schedule_origin_id = external_repo.get_external_schedule(
                "no_config_pipeline_every_min_schedule"
            ).get_external_origin_id()
            script = (
                instance.scheduler._get_bash_script_file_path(  # pylint: disable=protected-access
                    instance, schedule_origin_id
                )
            )

            subprocess.check_output([script], shell=True, env={"DAGSTER_HOME": tempdir})

            runs = instance.get_runs()
            assert len(runs) == 1
            assert runs[0].status == PipelineRunStatus.SUCCESS


def test_start_schedule_fails(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:

            def raises(*args, **kwargs):
                raise Exception("Patch")

            instance._scheduler._start_cron_job = raises  # pylint: disable=protected-access
            with pytest.raises(Exception, match="Patch"):
                instance.start_schedule_and_update_storage_state(
                    external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
                )

            schedule = instance.get_job_state(
                external_repo.get_external_schedule(
                    "no_config_pipeline_every_min_schedule"
                ).get_external_origin_id()
            )

            assert schedule.status == JobStatus.STOPPED


def test_start_schedule_unsuccessful(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:

            def do_nothing(*_):
                pass

            instance._scheduler._start_cron_job = do_nothing  # pylint: disable=protected-access

            # End schedule
            with pytest.raises(
                DagsterSchedulerError,
                match="Attempted to write cron job for schedule no_config_pipeline_every_min_schedule, "
                "but failed. The scheduler is not running no_config_pipeline_every_min_schedule.",
            ):
                instance.start_schedule_and_update_storage_state(
                    external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
                )


def test_start_schedule_manual_delete_debug(
    restore_cron_tab, snapshot  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:

            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
            )

            # Manually delete the schedule from the crontab
            instance.scheduler._end_cron_job(  # pylint: disable=protected-access
                instance,
                external_repo.get_external_schedule(
                    "no_config_pipeline_every_min_schedule"
                ).get_external_origin_id(),
            )

            # Check debug command
            debug_info = instance.scheduler_debug_info()
            assert len(debug_info.errors) == 1

            # Reconcile should fix error
            instance.reconcile_scheduler_state(external_repo)
            debug_info = instance.scheduler_debug_info()
            assert len(debug_info.errors) == 0


def test_start_schedule_manual_add_debug(
    restore_cron_tab, snapshot  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:

            # Initialize scheduler
            instance.reconcile_scheduler_state(external_repo)

            # Manually add the schedule from to the crontab
            instance.scheduler._start_cron_job(  # pylint: disable=protected-access
                instance,
                external_repo.get_external_schedule("no_config_pipeline_every_min_schedule"),
            )

            # Check debug command
            debug_info = instance.scheduler_debug_info()
            assert len(debug_info.errors) == 1

            # Reconcile should fix error
            instance.reconcile_scheduler_state(external_repo)
            debug_info = instance.scheduler_debug_info()
            assert len(debug_info.errors) == 0


def test_start_schedule_manual_duplicate_schedules_add_debug(
    restore_cron_tab, snapshot  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:

            external_schedule = external_repo.get_external_schedule(
                "no_config_pipeline_every_min_schedule"
            )

            instance.start_schedule_and_update_storage_state(external_schedule)

            # Manually add  extra cron tabs
            instance.scheduler._start_cron_job(  # pylint: disable=protected-access
                instance,
                external_schedule,
            )
            instance.scheduler._start_cron_job(  # pylint: disable=protected-access
                instance,
                external_schedule,
            )

            # Check debug command
            debug_info = instance.scheduler_debug_info()
            assert len(debug_info.errors) == 1

            # Reconcile should fix error
            instance.reconcile_scheduler_state(external_repo)
            debug_info = instance.scheduler_debug_info()
            assert len(debug_info.errors) == 0


def test_stop_schedule_fails(
    restore_cron_tab,  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:

            external_schedule = external_repo.get_external_schedule(
                "no_config_pipeline_every_min_schedule"
            )
            schedule_origin_id = external_schedule.get_external_origin_id()

            def raises(*args, **kwargs):
                raise Exception("Patch")

            instance._scheduler._end_cron_job = raises  # pylint: disable=protected-access

            instance.start_schedule_and_update_storage_state(external_schedule)

            assert "schedules" in os.listdir(tempdir)

            assert "{}.sh".format(schedule_origin_id) in os.listdir(
                os.path.join(tempdir, "schedules", "scripts")
            )

            # End schedule
            with pytest.raises(Exception, match="Patch"):
                instance.stop_schedule_and_update_storage_state(schedule_origin_id)

            schedule = instance.get_job_state(schedule_origin_id)

            assert schedule.status == JobStatus.RUNNING


def test_stop_schedule_unsuccessful(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:

            def do_nothing(*_):
                pass

            instance._scheduler._end_cron_job = do_nothing  # pylint: disable=protected-access

            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
            )

            # End schedule
            with pytest.raises(
                DagsterSchedulerError,
                match="Attempted to remove existing cron job for schedule "
                "no_config_pipeline_every_min_schedule, but failed. There are still 1 jobs running for "
                "the schedule.",
            ):
                instance.stop_schedule_and_update_storage_state(
                    external_repo.get_external_schedule(
                        "no_config_pipeline_every_min_schedule"
                    ).get_external_origin_id()
                )


def test_wipe(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:

            # Start schedule
            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
            )

            # Wipe scheduler
            instance.wipe_all_schedules()

            # Check schedules are wiped
            assert instance.all_stored_job_state(job_type=JobType.SCHEDULE) == []


def test_log_directory(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:

        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:
            external_schedule = external_repo.get_external_schedule(
                "no_config_pipeline_every_min_schedule"
            )
            schedule_log_path = instance.logs_path_for_schedule(
                external_schedule.get_external_origin_id()
            )

            assert schedule_log_path.endswith(
                "/schedules/logs/{schedule_origin_id}/scheduler.log".format(
                    schedule_origin_id=external_schedule.get_external_origin_id()
                )
            )

            # Start schedule
            instance.start_schedule_and_update_storage_state(external_schedule)

            # Wipe scheduler
            instance.wipe_all_schedules()

            # Check schedules are wiped
            assert instance.all_stored_job_state(job_type=JobType.SCHEDULE) == []


def test_reconcile_failure(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:

            instance.reconcile_scheduler_state(external_repo)
            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
            )

            def failed_start_job(*_):
                raise DagsterSchedulerError("Failed to start")

            def failed_end_job(*_):
                raise DagsterSchedulerError("Failed to stop")

            instance._scheduler.start_schedule = (  # pylint: disable=protected-access
                failed_start_job
            )
            instance._scheduler.stop_schedule = failed_end_job  # pylint: disable=protected-access

            with pytest.raises(
                DagsterScheduleReconciliationError,
                match="Error 1: Failed to stop\n    Error 2: Failed to stop\n    Error 3: Failed to stop",
            ):
                instance.reconcile_scheduler_state(external_repo)


@freeze_time("2019-02-27")
def test_reconcile_schedule_without_start_time():
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:
            external_schedule = external_repo.get_external_schedule(
                "no_config_pipeline_daily_schedule"
            )

            legacy_schedule_state = JobState(
                external_schedule.get_external_origin(),
                JobType.SCHEDULE,
                JobStatus.RUNNING,
                ScheduleJobData(external_schedule.cron_schedule, None, "SystemCronScheduler"),
            )

            instance.add_job_state(legacy_schedule_state)

            instance.reconcile_scheduler_state(external_repository=external_repo)

            reconciled_schedule_state = instance.get_job_state(
                external_schedule.get_external_origin_id()
            )

            assert reconciled_schedule_state.status == JobStatus.RUNNING
            assert (
                reconciled_schedule_state.job_specific_data.start_timestamp
                == get_timestamp_from_utc_datetime(get_current_datetime_in_utc())
            )


def test_reconcile_failure_when_deleting_schedule_def(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        with get_test_external_repo() as external_repo:

            instance.reconcile_scheduler_state(external_repo)

            assert len(instance.all_stored_job_state(job_type=JobType.SCHEDULE)) == 3

            def failed_end_job(*_):
                raise DagsterSchedulerError("Failed to stop")

            instance._scheduler.stop_schedule_and_delete_from_storage = (  # pylint: disable=protected-access
                failed_end_job
            )

            with pytest.raises(
                DagsterScheduleReconciliationError,
                match="Error 1: Failed to stop",
            ):
                with get_smaller_external_repo() as smaller_repo:
                    instance.reconcile_scheduler_state(smaller_repo)
