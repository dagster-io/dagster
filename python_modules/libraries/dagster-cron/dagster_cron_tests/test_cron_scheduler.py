import os
import sys

from dagster_cron import SystemCronScheduler

from dagster import ScheduleDefinition, check
from dagster.core.definitions import RepositoryDefinition
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.scheduler import Schedule, SchedulerHandle
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.core.storage.schedules import SqliteScheduleStorage
from dagster.seven import TemporaryDirectory


class MockSystemCronScheduler(SystemCronScheduler):
    '''Overwrite _start_cron_job and _end_crob_job to prevent polluting
    the user's crontab during tests
    '''

    def _start_cron_job(self, instance, repository, schedule):
        self._write_bash_script_to_file(instance, repository, schedule)

    def _end_cron_job(self, instance, repository, schedule):
        script_file = self._get_bash_script_file_path(instance, repository, schedule)
        if os.path.isfile(script_file):
            os.remove(script_file)


def define_scheduler():
    no_config_pipeline_daily_schedule = ScheduleDefinition(
        name="no_config_pipeline_daily_schedule",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        environment_dict={"storage": {"filesystem": None}},
    )

    no_config_pipeline_every_min_schedule = ScheduleDefinition(
        name="no_config_pipeline_every_min_schedule",
        cron_schedule="* * * * *",
        pipeline_name="no_config_pipeline",
        environment_dict={"storage": {"filesystem": None}},
    )

    default_config_pipeline_every_min_schedule = ScheduleDefinition(
        name="default_config_pipeline_every_min_schedule",
        cron_schedule="* * * * *",
        pipeline_name="no_config_pipeline",
    )

    return SchedulerHandle(
        schedule_defs=[
            default_config_pipeline_every_min_schedule,
            no_config_pipeline_daily_schedule,
            no_config_pipeline_every_min_schedule,
        ],
    )


def define_scheduler_instance(tempdir):
    return DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(tempdir),
        run_storage=InMemoryRunStorage(),
        event_storage=InMemoryEventLogStorage(),
        compute_log_manager=NoOpComputeLogManager(tempdir),
        schedule_storage=SqliteScheduleStorage.from_local(os.path.join(tempdir, 'schedules')),
        scheduler=SystemCronScheduler(os.path.join(tempdir, 'schedules')),
    )


def test_init():
    with TemporaryDirectory() as tempdir:
        repository = RepositoryDefinition(name="test_repository")
        instance = define_scheduler_instance(tempdir)
        scheduler_handle = define_scheduler()

        scheduler_handle = define_scheduler()
        assert scheduler_handle

        # Initialize scheduler
        scheduler_handle.up(
            python_path=sys.executable,
            repository_path="",
            repository=repository,
            instance=instance,
        )

        # Check schedules are saved to disk
        assert 'schedules' in os.listdir(tempdir)

        schedules = instance.all_schedules(repository)

        for schedule in schedules:
            assert "/bin/python" in schedule.python_path


def test_re_init():
    with TemporaryDirectory() as tempdir:
        repository = RepositoryDefinition(name="test_repository")
        instance = define_scheduler_instance(tempdir)
        scheduler_handle = define_scheduler()

        scheduler_handle = define_scheduler()
        assert scheduler_handle

        # Initialize scheduler
        scheduler_handle.up(
            python_path=sys.executable,
            repository_path="",
            repository=repository,
            instance=instance,
        )

        # Start schedule
        schedule = instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")

        # Re-initialize scheduler
        scheduler_handle.up(
            python_path=sys.executable,
            repository_path="",
            repository=repository,
            instance=instance,
        )

        # Check schedules are saved to disk
        assert 'schedules' in os.listdir(tempdir)

        schedules = instance.all_schedules(repository)

        for schedule in schedules:
            assert "/bin/python" in schedule.python_path


def test_start_and_stop_schedule():
    with TemporaryDirectory() as tempdir:
        repository = RepositoryDefinition(name="test_repository")
        instance = define_scheduler_instance(tempdir)
        scheduler_handle = define_scheduler()
        assert scheduler_handle

        # Initialize scheduler
        scheduler_handle.up(
            python_path=sys.executable,
            repository_path="",
            repository=repository,
            instance=instance,
        )

        schedule_def = scheduler_handle.get_schedule_def_by_name(
            "no_config_pipeline_every_min_schedule"
        )

        # Start schedule
        schedule = instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")

        check.inst_param(schedule, 'schedule', Schedule)
        assert "/bin/python" in schedule.python_path

        assert 'schedules' in os.listdir(tempdir)

        assert "{}.{}.sh".format(repository.name, schedule_def.name) in os.listdir(
            os.path.join(tempdir, 'schedules', 'scripts')
        )

        # End schedule
        instance.stop_schedule(repository, "no_config_pipeline_every_min_schedule")
        assert "{}.{}.sh".format(repository.name, schedule_def.name) not in os.listdir(
            os.path.join(tempdir, 'schedules', 'scripts')
        )


def test_wipe():
    with TemporaryDirectory() as tempdir:
        repository = RepositoryDefinition(name="test_repository")
        instance = define_scheduler_instance(tempdir)
        scheduler_handle = define_scheduler()
        assert scheduler_handle

        # Initialize scheduler
        scheduler_handle.up(
            python_path=sys.executable,
            repository_path="",
            repository=repository,
            instance=instance,
        )

        # Start schedule
        instance.start_schedule(repository, "no_config_pipeline_every_min_schedule")

        # Wipe scheduler
        instance.wipe_all_schedules()

        # Check schedules are wiped
        assert instance.all_schedules(repository) == []
