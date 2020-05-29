import os
import subprocess
import sys

import pytest
import yaml
from dagster_cron import SystemCronScheduler

from dagster import ScheduleDefinition, check
from dagster.core.definitions import RepositoryDefinition, lambda_solid, pipeline
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.scheduler import Schedule, ScheduleStatus, reconcile_scheduler_state
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.core.storage.schedules import SqliteScheduleStorage
from dagster.seven import TemporaryDirectory
from dagster.utils import file_relative_path


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
def unset_dagster_home():
    old_env = os.getenv('DAGSTER_HOME')
    if old_env is not None:
        del os.environ['DAGSTER_HOME']
    yield
    if old_env is not None:
        os.environ['DAGSTER_HOME'] = old_env


@pipeline
def no_config_pipeline():
    @lambda_solid
    def return_hello():
        return 'Hello'

    return return_hello()


def define_schedules():
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

    return [
        default_config_pipeline_every_min_schedule,
        no_config_pipeline_daily_schedule,
        no_config_pipeline_every_min_schedule,
    ]


def define_repository():
    return RepositoryDefinition(
        name="test_repository", pipeline_defs=[no_config_pipeline], schedule_defs=define_schedules()
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
        run_launcher=SyncInMemoryRunLauncher(),
    )


def test_init(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        repository = RepositoryDefinition(name="test_repository", schedule_defs=define_schedules())
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path="",
            repository=repository,
            instance=instance,
        )

        # Check schedules are saved to disk
        assert 'schedules' in os.listdir(tempdir)

        schedules = instance.all_schedules(repository.name)

        for schedule in schedules:
            assert "/bin/python" in schedule.python_path


def test_re_init(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        repository = RepositoryDefinition(name="test_repository", schedule_defs=define_schedules())
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path="",
            repository=repository,
            instance=instance,
        )

        # Start schedule
        schedule = instance.start_schedule(repository.name, "no_config_pipeline_every_min_schedule")

        # Re-initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path="",
            repository=repository,
            instance=instance,
        )

        # Check schedules are saved to disk
        assert 'schedules' in os.listdir(tempdir)

        schedules = instance.all_schedules(repository.name)

        for schedule in schedules:
            assert "/bin/python" in schedule.python_path


def test_start_and_stop_schedule(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:

        repository = RepositoryDefinition(name="test_repository", schedule_defs=define_schedules())
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path="",
            repository=repository,
            instance=instance,
        )

        schedule_def = repository.get_schedule_def("no_config_pipeline_every_min_schedule")

        schedule = instance.start_schedule(repository.name, "no_config_pipeline_every_min_schedule")

        check.inst_param(schedule, 'schedule', Schedule)
        assert "/bin/python" in schedule.python_path

        assert 'schedules' in os.listdir(tempdir)

        assert "{}.{}.sh".format(repository.name, schedule_def.name) in os.listdir(
            os.path.join(tempdir, 'schedules', 'scripts')
        )

        instance.stop_schedule(repository.name, "no_config_pipeline_every_min_schedule")
        assert "{}.{}.sh".format(repository.name, schedule_def.name) not in os.listdir(
            os.path.join(tempdir, 'schedules', 'scripts')
        )


def test_script_execution(
    restore_cron_tab, unset_dagster_home
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        os.environ["DAGSTER_HOME"] = tempdir
        config = {
            'scheduler': {'module': 'dagster_cron', 'class': 'SystemCronScheduler', 'config': {}},
            # This needs to synchronously execute to completion when
            # the generated bash script is invoked
            'run_launcher': {
                'module': 'dagster.core.launcher.sync_in_memory_run_launcher',
                'class': 'SyncInMemoryRunLauncher',
                'config': {'hijack_start': True},
            },
        }

        with open(os.path.join(tempdir, 'dagster.yaml'), 'w+') as f:
            f.write(yaml.dump(config))

        instance = DagsterInstance.get()
        repository = define_repository()

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, './repository.yaml'),
            repository=repository,
            instance=instance,
        )

        instance.start_schedule(repository.name, "no_config_pipeline_every_min_schedule")

        schedule_def = repository.get_schedule_def("no_config_pipeline_every_min_schedule")
        script = instance.scheduler._get_bash_script_file_path(  # pylint: disable=protected-access
            instance, repository.name, schedule_def
        )

        subprocess.check_output([script], shell=True, env={"DAGSTER_HOME": tempdir})

        runs = instance.get_runs()
        assert len(runs) == 1
        assert runs[0].status == PipelineRunStatus.SUCCESS


def test_start_schedule_fails(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        repository = RepositoryDefinition(name="test_repository", schedule_defs=define_schedules())
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path="",
            repository=repository,
            instance=instance,
        )

        schedule_def = repository.get_schedule_def("no_config_pipeline_every_min_schedule")

        def raises(*args, **kwargs):
            raise Exception('Patch')

        instance._scheduler._start_cron_job = raises  # pylint: disable=protected-access
        with pytest.raises(Exception, match='Patch'):
            instance.start_schedule(repository.name, "no_config_pipeline_every_min_schedule")

        schedule = instance.get_schedule_by_name(repository.name, schedule_def.name)

        assert schedule.status == ScheduleStatus.STOPPED


def test_start_schedule_unsuccessful(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        repository = RepositoryDefinition(name="test_repository", schedule_defs=define_schedules())
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path="",
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
            instance.start_schedule(repository.name, "no_config_pipeline_every_min_schedule")


def test_start_schedule_manual_delete_debug(
    restore_cron_tab, snapshot  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:
        repository = RepositoryDefinition(name="test_repository", schedule_defs=define_schedules())
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path="fake path", repository_path="", repository=repository, instance=instance,
        )

        instance.start_schedule(repository.name, "no_config_pipeline_every_min_schedule")

        # Manually delete the schedule from the crontab
        instance.scheduler._end_cron_job(  # pylint: disable=protected-access
            instance,
            repository.name,
            instance.get_schedule_by_name(repository.name, "no_config_pipeline_every_min_schedule"),
        )

        # Check debug command
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 1

        # Reconcile should fix error
        reconcile_scheduler_state(
            python_path="fake path", repository_path="", repository=repository, instance=instance,
        )
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 0


def test_start_schedule_manual_add_debug(
    restore_cron_tab, snapshot  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:
        repository = RepositoryDefinition(name="test_repository", schedule_defs=define_schedules())
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path="fake path", repository_path="", repository=repository, instance=instance,
        )

        # Manually add the schedule from to the crontab
        instance.scheduler._start_cron_job(  # pylint: disable=protected-access
            instance,
            repository.name,
            instance.get_schedule_by_name(repository.name, "no_config_pipeline_every_min_schedule"),
        )

        # Check debug command
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 1

        # Reconcile should fix error
        reconcile_scheduler_state(
            python_path="fake path", repository_path="", repository=repository, instance=instance,
        )
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 0


def test_start_schedule_manual_duplicate_schedules_add_debug(
    restore_cron_tab, snapshot  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:
        repository = RepositoryDefinition(name="test_repository", schedule_defs=define_schedules())
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path="fake path", repository_path="", repository=repository, instance=instance,
        )

        instance.start_schedule(repository.name, "no_config_pipeline_every_min_schedule")

        # Manually add  extra cron tabs
        instance.scheduler._start_cron_job(  # pylint: disable=protected-access
            instance,
            repository.name,
            instance.get_schedule_by_name(repository.name, "no_config_pipeline_every_min_schedule"),
        )
        instance.scheduler._start_cron_job(  # pylint: disable=protected-access
            instance,
            repository.name,
            instance.get_schedule_by_name(repository.name, "no_config_pipeline_every_min_schedule"),
        )

        # Check debug command
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 1

        # Reconcile should fix error
        reconcile_scheduler_state(
            python_path="fake path", repository_path="", repository=repository, instance=instance,
        )
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 0


def test_stop_schedule_fails(
    restore_cron_tab,  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:
        repository = RepositoryDefinition(name="test_repository", schedule_defs=define_schedules())
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path="",
            repository=repository,
            instance=instance,
        )

        schedule_def = repository.get_schedule_def("no_config_pipeline_every_min_schedule")

        def raises(*args, **kwargs):
            raise Exception('Patch')

        instance._scheduler._end_cron_job = raises  # pylint: disable=protected-access

        schedule = instance.start_schedule(repository.name, "no_config_pipeline_every_min_schedule")

        check.inst_param(schedule, 'schedule', Schedule)
        assert "/bin/python" in schedule.python_path

        assert 'schedules' in os.listdir(tempdir)

        assert "{}.{}.sh".format(repository.name, schedule_def.name) in os.listdir(
            os.path.join(tempdir, 'schedules', 'scripts')
        )

        # End schedule
        with pytest.raises(Exception, match='Patch'):
            instance.stop_schedule(repository.name, "no_config_pipeline_every_min_schedule")

        schedule = instance.get_schedule_by_name(repository.name, schedule_def.name)

        assert schedule.status == ScheduleStatus.RUNNING


def test_stop_schedule_unsuccessful(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        repository = RepositoryDefinition(name="test_repository", schedule_defs=define_schedules())
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path="",
            repository=repository,
            instance=instance,
        )

        def do_nothing(*_):
            pass

        instance._scheduler._end_cron_job = do_nothing  # pylint: disable=protected-access

        instance.start_schedule(repository.name, "no_config_pipeline_every_min_schedule")

        # End schedule
        with pytest.raises(
            DagsterInvariantViolationError,
            match="Attempted to remove cron job for schedule no_config_pipeline_every_min_schedule, but failed.",
        ):
            instance.stop_schedule(repository.name, "no_config_pipeline_every_min_schedule")


def test_wipe(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        repository = RepositoryDefinition(name="test_repository", schedule_defs=define_schedules())
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path="",
            repository=repository,
            instance=instance,
        )

        # Start schedule
        instance.start_schedule(repository.name, "no_config_pipeline_every_min_schedule")

        # Wipe scheduler
        instance.wipe_all_schedules()

        # Check schedules are wiped
        assert instance.all_schedules(repository.name) == []
