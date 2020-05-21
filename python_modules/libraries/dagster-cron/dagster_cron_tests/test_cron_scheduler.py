import os
import re
import subprocess
import sys

import pytest
from dagster_cron import SystemCronScheduler

from dagster import ScheduleDefinition, check, file_relative_path
from dagster.core.definitions import RepositoryDefinition, lambda_solid, pipeline
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.scheduler import Schedule, ScheduleStatus, reconcile_scheduler_state
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.core.storage.schedules import SqliteScheduleStorage
from dagster.seven import TemporaryDirectory


@pytest.fixture(scope='function')
def restore_cron_tab():
    with TemporaryDirectory() as tempdir:
        crontab_backup = os.path.join(tempdir, "crontab_backup.txt")
        with open(crontab_backup, 'wb+') as f:
            try:
                output = subprocess.check_output(['crontab', '-l'])
                f.write(output)
            except subprocess.CalledProcessError:
                # If a crontab hasn't been created yet, the command fails with a
                # non-zero error code
                pass

        try:
            subprocess.check_output(['crontab', '-r'])
        except subprocess.CalledProcessError:
            # If a crontab hasn't been created yet, the command fails with a
            # non-zero error code
            pass

        yield

        subprocess.check_output(['crontab', crontab_backup])


@pytest.fixture(scope='function')
def repository():
    yield define_repo()


schedules_dict = {
    'no_config_pipeline_daily_schedule': ScheduleDefinition(
        name="no_config_pipeline_daily_schedule",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        environment_dict={"storage": {"filesystem": None}},
    ),
    'no_config_pipeline_every_min_schedule': ScheduleDefinition(
        name="no_config_pipeline_every_min_schedule",
        cron_schedule="* * * * *",
        pipeline_name="no_config_pipeline",
        environment_dict={"storage": {"filesystem": None}},
    ),
    'default_config_pipeline_every_min_schedule': ScheduleDefinition(
        name="default_config_pipeline_every_min_schedule",
        cron_schedule="* * * * *",
        pipeline_name="no_config_pipeline",
    ),
}


def define_schedules():
    return list(schedules_dict.values())


@pipeline
def no_config_pipeline():
    @lambda_solid
    def return_hello():
        return 'Hello'

    return return_hello()


def define_repo():
    return RepositoryDefinition(
        name="test", pipeline_defs=[no_config_pipeline], schedule_defs=define_schedules(),
    )


def define_scheduler_instance(tempdir):
    return DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(tempdir),
        run_storage=InMemoryRunStorage(),
        event_storage=InMemoryEventLogStorage(),
        compute_log_manager=NoOpComputeLogManager(tempdir),
        schedule_storage=SqliteScheduleStorage.from_local(os.path.join(tempdir, 'schedules')),
        scheduler=SystemCronScheduler(),
    )


def test_init(restore_cron_tab, repository):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        # Check schedules are saved to disk
        assert 'schedules' in os.listdir(tempdir)

        schedules = instance.all_schedules(repository)

        for schedule in schedules:
            assert "/bin/python" in schedule.python_path


def test_re_init(
    restore_cron_tab, repository
):  #  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        # Start schedule
        schedule = instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")

        # Re-initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        # Check schedules are saved to disk
        assert 'schedules' in os.listdir(tempdir)

        schedules = instance.all_schedules(repository)

        for schedule in schedules:
            assert "/bin/python" in schedule.python_path


def test_start_and_stop_schedule(
    restore_cron_tab, repository
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        schedule_def = repository.get_schedule_def("no_config_pipeline_every_min_schedule")

        schedule = instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")

        check.inst_param(schedule, 'schedule', Schedule)
        assert "/bin/python" in schedule.python_path

        assert 'schedules' in os.listdir(tempdir)

        assert "{}.{}.sh".format(repository.name, schedule_def.name) in os.listdir(
            os.path.join(tempdir, 'schedules', 'scripts')
        )

        instance.stop_schedule(repository, "no_config_pipeline_every_min_schedule")
        assert "{}.{}.sh".format(repository.name, schedule_def.name) not in os.listdir(
            os.path.join(tempdir, 'schedules', 'scripts')
        )


def get_cron_jobs():
    output = subprocess.check_output(['crontab', '-l'])
    return list(filter(None, output.decode('utf-8').strip().split("\n")))


def test_start_schedule_cron_job(
    restore_cron_tab, repository
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")
        instance.start_schedule(repository, "no_config_pipeline_daily_schedule")
        instance.start_schedule(repository, "default_config_pipeline_every_min_schedule")

        # Inspect the cron tab
        cron_jobs = get_cron_jobs()

        assert len(cron_jobs) == 3

        for cron_job in cron_jobs:
            match = re.findall(r"^(.*?) (/.*) > (.*) 2>&1 # dagster-schedule: test\.(.*)", cron_job)
            cron_schedule, command, log_file, schedule_name = match[0]

            schedule_def = schedules_dict[schedule_name]

            # Check cron schedule matches
            if schedule_def.cron_schedule == "0 0 * * *":
                assert cron_schedule == "@daily"
            else:
                assert cron_schedule == schedule_def.cron_schedule

            # Check bash file exists
            assert os.path.isfile(command)

            # Check log file is correct
            assert log_file.endswith("scheduler.log")


def test_start_and_stop_schedule_cron_tab(
    restore_cron_tab, repository
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        # Start schedule
        instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 1

        # Try starting it again
        with pytest.raises(DagsterInvariantViolationError):
            instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 1

        # Start another schedule
        instance.start_schedule(repository, "no_config_pipeline_daily_schedule")
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 2

        # Stop second schedule
        instance.stop_schedule(repository, "no_config_pipeline_daily_schedule")
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 1

        # Try stopping second schedule again
        instance.stop_schedule(repository, "no_config_pipeline_daily_schedule")
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 1

        # Start second schedule
        instance.start_schedule(repository, "no_config_pipeline_daily_schedule")
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 2

        # Reconcile schedule state, should be in the same state
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 2

        instance.start_schedule(repository, "default_config_pipeline_every_min_schedule")
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 3

        # Reconcile schedule state, should be in the same state
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 3

        # Stop all schedules
        instance.stop_schedule(repository, "no_config_pipeline_every_min_schedule")
        instance.stop_schedule(repository, "no_config_pipeline_daily_schedule")
        instance.stop_schedule(repository, "default_config_pipeline_every_min_schedule")

        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 0

        # Reconcile schedule state, should be in the same state
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 0


def test_start_schedule_fails(
    restore_cron_tab, repository
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:

        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        schedule_def = repository.get_schedule_def("no_config_pipeline_every_min_schedule")

        def raises(*args, **kwargs):
            raise Exception('Patch')

        instance._scheduler._start_cron_job = raises  # pylint: disable=protected-access
        with pytest.raises(Exception, match='Patch'):
            instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")

        schedule = instance.get_schedule_by_name(repository, schedule_def.name)

        assert schedule.status == ScheduleStatus.STOPPED


def test_start_schedule_unsuccessful(
    restore_cron_tab, repository
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:

        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        def do_nothing(*_):
            pass

        instance._scheduler._start_cron_job = do_nothing  # pylint: disable=protected-access

        # End schedule
        with pytest.raises(
            DagsterInvariantViolationError,
            match="Attempted to write cron job for schedule no_config_pipeline_every_min_schedule, but failed",
        ):
            instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")


def test_start_schedule_manual_delete_debug(
    restore_cron_tab, repository, snapshot  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:

        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path="fake path",
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")

        # Manually delete the schedule from the crontab
        instance.scheduler._end_cron_job(  # pylint: disable=protected-access
            instance,
            repository,
            instance.get_schedule_by_name(repository, "no_config_pipeline_every_min_schedule"),
        )

        # Check debug command
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 1

        # Reconcile should fix error
        reconcile_scheduler_state(
            python_path="fake path",
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 0


def test_start_schedule_manual_add_debug(
    restore_cron_tab, repository, snapshot  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:

        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path="fake path",
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        # Manually add the schedule from to the crontab
        instance.scheduler._start_cron_job(  # pylint: disable=protected-access
            instance,
            repository,
            instance.get_schedule_by_name(repository, "no_config_pipeline_every_min_schedule"),
        )

        # Check debug command
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 1

        # Reconcile should fix error
        reconcile_scheduler_state(
            python_path="fake path",
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 0


def test_start_schedule_manual_duplicate_schedules_add_debug(
    restore_cron_tab, repository, snapshot  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:

        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path="fake path",
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")

        # Manually add  extra cron tabs
        instance.scheduler._start_cron_job(  # pylint: disable=protected-access
            instance,
            repository,
            instance.get_schedule_by_name(repository, "no_config_pipeline_every_min_schedule"),
        )
        instance.scheduler._start_cron_job(  # pylint: disable=protected-access
            instance,
            repository,
            instance.get_schedule_by_name(repository, "no_config_pipeline_every_min_schedule"),
        )

        # Check debug command
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 1

        # Reconcile should fix error
        reconcile_scheduler_state(
            python_path="fake path",
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 0


def test_stop_schedule_fails(
    restore_cron_tab, repository,  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:

        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        schedule_def = repository.get_schedule_def("no_config_pipeline_every_min_schedule")

        def raises(*args, **kwargs):
            raise Exception('Patch')

        instance._scheduler._end_cron_job = raises  # pylint: disable=protected-access

        schedule = instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")

        check.inst_param(schedule, 'schedule', Schedule)
        assert "/bin/python" in schedule.python_path

        assert 'schedules' in os.listdir(tempdir)

        assert "{}.{}.sh".format(repository.name, schedule_def.name) in os.listdir(
            os.path.join(tempdir, 'schedules', 'scripts')
        )

        # End schedule
        with pytest.raises(Exception, match='Patch'):
            instance.stop_schedule(repository, "no_config_pipeline_every_min_schedule")

        schedule = instance.get_schedule_by_name(repository, schedule_def.name)

        assert schedule.status == ScheduleStatus.RUNNING


def test_stop_schedule_unsuccessful(
    restore_cron_tab, repository
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:

        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        def do_nothing(*_):
            pass

        instance._scheduler._end_cron_job = do_nothing  # pylint: disable=protected-access

        instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")

        # End schedule
        with pytest.raises(
            DagsterInvariantViolationError,
            match="Attempted to remove cron job for schedule no_config_pipeline_every_min_schedule, but failed.",
        ):
            instance.stop_schedule(repository, "no_config_pipeline_every_min_schedule")


def test_wipe(restore_cron_tab, repository):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:

        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        # Start schedule
        instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")

        # Wipe scheduler
        instance.wipe_all_schedules()

        # Check schedules are wiped
        assert instance.all_schedules(repository) == []


def test_log_directory(
    restore_cron_tab, repository
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:

        instance = define_scheduler_instance(tempdir)
        schedule_log_path = instance.logs_path_for_schedule(
            repository, "no_config_pipeline_every_min_schedule"
        )

        assert schedule_log_path.endswith(
            "/schedules/logs/{repository_name}/{schedule_name}/scheduler.log".format(
                repository_name=repository.name,
                schedule_name="no_config_pipeline_every_min_schedule",
            )
        )

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=repository,
            instance=instance,
        )

        # Start schedule
        instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")

        # Wipe scheduler
        instance.wipe_all_schedules()

        # Check schedules are wiped
        assert instance.all_schedules(repository) == []
