import os
import sys

from dagster_cron import SystemCronScheduler

from dagster import RepositoryDefinition, ScheduleDefinition, check, lambda_solid, pipeline
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler import RunningSchedule
from dagster.seven import TemporaryDirectory, mock


class MockSystemCronScheduler(SystemCronScheduler):
    '''Overwrite _start_cron_job and _end_crob_job to prevent polluting
    the user's crontab during tests
    '''

    def _start_cron_job(self, script_file, schedule):
        pass

    def _end_cron_job(self, schedule):
        pass


def define_scheduler(artifacts_dir):

    no_config_pipeline_hourly_schedule = ScheduleDefinition(
        name="no_config_pipeline_hourly_schedule",
        cron_schedule="0 0 * * *",
        execution_params={
            "environmentConfigData": {"storage": {"filesystem": None}},
            "selector": {"name": "no_config_pipeline", "solidSubset": None},
            "mode": "default",
        },
    )

    return MockSystemCronScheduler(
        schedule_defs=[no_config_pipeline_hourly_schedule], artifacts_dir=artifacts_dir
    )


def create_repository():
    @pipeline
    def no_config_pipeline():
        @lambda_solid
        def return_hello():
            return 'Hello'

        return return_hello()

    return RepositoryDefinition(name='test', pipeline_defs=[no_config_pipeline])


@mock.patch.dict(os.environ, {"DAGSTER_HOME": "~/dagster"})
def test_start_and_end_schedule():
    with TemporaryDirectory() as tempdir:

        instance = DagsterInstance.local_temp(tempdir=tempdir, features=['scheduler'])
        scheduler = define_scheduler(instance.schedules_directory())
        assert scheduler

        # Start schedule
        schedule_def = scheduler.get_schedule_def("no_config_pipeline_hourly_schedule")
        schedule = scheduler.start_schedule(schedule_def, sys.executable, "")

        check.inst_param(schedule, 'schedule', RunningSchedule)
        assert schedule.schedule_definition == schedule_def
        assert "/bin/python" in schedule.python_path

        assert 'schedules' in os.listdir(tempdir)

        assert "{}_{}.json".format(schedule_def.name, schedule.schedule_id) in os.listdir(
            os.path.join(tempdir, 'schedules')
        )
        assert "{}_{}.sh".format(schedule_def.name, schedule.schedule_id) in os.listdir(
            os.path.join(tempdir, 'schedules')
        )

        # End schedule
        scheduler.end_schedule(schedule_def)
        assert "{}_{}.json".format(schedule_def.name, schedule.schedule_id) not in os.listdir(
            tempdir
        )
        assert "{}_{}.sh".format(schedule_def.name, schedule.schedule_id) not in os.listdir(tempdir)
