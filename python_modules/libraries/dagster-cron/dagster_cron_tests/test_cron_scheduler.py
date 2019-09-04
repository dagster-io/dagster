import os
import sys

from dagster_cron import SystemCronScheduler

from dagster import RepositoryDefinition, ScheduleDefinition, check, lambda_solid, pipeline
from dagster.core.scheduler import RunningSchedule
from dagster.seven import TemporaryDirectory, mock


class TestSystemCronScheduler(SystemCronScheduler):
    '''Overwrite _start_cron_job and _end_crob_job to prevent polluting
    the user's crontab during tests
    '''

    def _start_cron_job(self, script_file, schedule):
        pass

    def _end_cron_job(self, schedule):
        pass


def create_repository():
    no_config_pipeline_hourly_schedule = ScheduleDefinition(
        name="no_config_pipeline_hourly_schedule",
        cron_schedule="0 0 * * *",
        execution_params={
            "environmentConfigData": {"storage": {"filesystem": None}},
            "selector": {"name": "no_config_pipeline", "solidSubset": None},
            "mode": "default",
        },
    )

    @pipeline
    def no_config_pipeline():
        @lambda_solid
        def return_hello():
            return 'Hello'

        return return_hello()

    return RepositoryDefinition(
        name='test',
        pipeline_defs=[no_config_pipeline],
        experimental={
            'schedule_defs': [no_config_pipeline_hourly_schedule],
            'scheduler': TestSystemCronScheduler,
        },
    )


@mock.patch.dict(os.environ, {"DAGSTER_HOME": "~/dagster"})
def test_start_and_end_schedule():
    with TemporaryDirectory() as schedule_dir:

        repository = create_repository()

        # Start schedule
        schedule_def = repository.get_schedule("no_config_pipeline_hourly_schedule")

        scheduler = repository.build_scheduler(schedule_dir=schedule_dir)
        assert scheduler

        schedule = scheduler.start_schedule(schedule_def, sys.executable, "")

        check.inst_param(schedule, 'schedule', RunningSchedule)
        assert schedule.schedule_definition == schedule_def
        assert "/bin/python" in schedule.python_path

        assert "{}_{}.json".format(schedule_def.name, schedule.schedule_id) in os.listdir(
            schedule_dir
        )
        assert "{}_{}.sh".format(schedule_def.name, schedule.schedule_id) in os.listdir(
            schedule_dir
        )

        # End schedule
        scheduler.end_schedule(schedule_def)
        assert "{}_{}.json".format(schedule_def.name, schedule.schedule_id) not in os.listdir(
            schedule_dir
        )
        assert "{}_{}.sh".format(schedule_def.name, schedule.schedule_id) not in os.listdir(
            schedule_dir
        )
