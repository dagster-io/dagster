import glob
import io
import os
import stat

import six
from crontab import CronTab

from dagster import DagsterInvariantViolationError, check, seven, utils
from dagster.core.definitions import RepositoryDefinition
from dagster.core.scheduler import ScheduleStatus, Scheduler
from dagster.core.serdes import ConfigurableClass


class SystemCronScheduler(Scheduler, ConfigurableClass):
    '''Scheduler class for system cron-backed scheduling.

    Pass this class as the ``scheduler`` argument to the :py:func:`@schedules <dagster.schedules>`
    API -- do not instantiate it directly.

    '''

    def __init__(self, artifacts_dir, inst_data=None):
        check.str_param(artifacts_dir, 'artifacts_dir')
        self._artifacts_dir = artifacts_dir
        self._inst_data = inst_data

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {'artifacts_dir': str}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return SystemCronScheduler(artifacts_dir=config_value['artifacts_dir'], inst_data=inst_data)

    def start_schedule(self, instance, repository, schedule_name):
        schedule = instance.get_schedule_by_name(repository, schedule_name)
        if not schedule:
            raise DagsterInvariantViolationError(
                'You have attempted to start schedule {name}, but it does not exist.'.format(
                    name=schedule_name
                )
            )

        if schedule.status == ScheduleStatus.RUNNING:
            raise DagsterInvariantViolationError(
                'You have attempted to start schedule {name}, but it is already running'.format(
                    name=schedule_name
                )
            )

        started_schedule = schedule.with_status(ScheduleStatus.RUNNING)
        instance.update_schedule(repository, started_schedule)
        self._start_cron_job(instance, repository, started_schedule)

        return started_schedule

    def stop_schedule(self, instance, repository, schedule_name):
        schedule = instance.get_schedule_by_name(repository, schedule_name)
        if not schedule:
            raise DagsterInvariantViolationError(
                'You have attempted to stop schedule {name}, but was never initialized.'
                'Use `schedule up` to initialize schedules'.format(name=schedule_name)
            )

        if schedule.status == ScheduleStatus.STOPPED:
            raise DagsterInvariantViolationError(
                'You have attempted to stop schedule {name}, but it is already stopped'.format(
                    name=schedule_name
                )
            )

        stopped_schedule = schedule.with_status(ScheduleStatus.STOPPED)
        instance.update_schedule(repository, stopped_schedule)
        self._end_cron_job(repository, schedule)

        return stopped_schedule

    def end_schedule(self, instance, repository, schedule_name):
        schedule = instance.get_schedule_by_name(repository, schedule_name)
        if not schedule:
            raise DagsterInvariantViolationError(
                'You have attempted to end schedule {name}, but it is not running.'.format(
                    name=schedule_name
                )
            )

        instance.delete_schedule(schedule)
        self._end_cron_job(repository, schedule)

        return schedule

    def wipe(self):

        bash_files = glob.glob(os.path.join(self._artifacts_dir, "*.sh"))
        for bash_file in bash_files:
            os.remove(bash_file)

        # Delete any other crontabs that are from dagster
        cron = CronTab(user=True)
        for job in cron:
            if 'dagster-schedule:' in job.comment:
                cron.remove_all(comment=job.comment)

        cron.write()

    def _get_file_prefix(self, repository, schedule):
        return os.path.join(self._artifacts_dir, '{}.{}'.format(repository.name, schedule.name))

    def _get_bash_script_file_path(self, repository, schedule):
        file_prefix = self._get_file_prefix(repository, schedule)
        return '{}.sh'.format(file_prefix)

    def _start_cron_job(self, instance, repository, schedule):
        script_file = self._write_bash_script_to_file(instance, repository, schedule)

        my_cron = CronTab(user=True)
        job = my_cron.new(
            command=script_file,
            comment='dagster-schedule: {repository_name}.{schedule_name}'.format(
                repository_name=repository.name, schedule_name=schedule.name
            ),
        )
        job.setall(schedule.cron_schedule)
        my_cron.write()

    def _end_cron_job(self, repository, schedule):
        my_cron = CronTab(user=True)
        my_cron.remove_all(
            comment='dagster-schedule: {repository_name}.{schedule_name}'.format(
                repository_name=repository.name, schedule_name=schedule.name
            ),
        )
        my_cron.write()

        script_file = self._get_bash_script_file_path(repository, schedule)
        if os.path.isfile(script_file):
            os.remove(script_file)

    def get_log_path(self, repository, schedule_name):
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.str_param(schedule_name, 'schedule_name')
        return os.path.join(
            self._artifacts_dir, repository.name, 'logs', '{}'.format(schedule_name)
        )

    def _write_bash_script_to_file(self, instance, repository, schedule):
        script_file = self._get_bash_script_file_path(repository, schedule)

        log_dir = instance.log_path_for_schedule(repository, schedule.name)
        utils.mkdir_p(log_dir)
        result_file = os.path.join(log_dir, "{}_{}.result".format("${RUN_DATE}", schedule.name))

        dagster_graphql_path = os.path.join(
            os.path.dirname(schedule.python_path), 'dagster-graphql'
        )
        dagster_home = os.getenv('DAGSTER_HOME')

        script_contents = '''
            #!/bin/bash
            export DAGSTER_HOME={dagster_home}
            export LANG=en_US.UTF-8
            {env_vars}

            export RUN_DATE=$(date "+%Y%m%dT%H%M%S")

            {dagster_graphql_path} -p startScheduledExecution -v '{variables}' -y "{repo_path}" --output "{result_file}"
        '''.format(
            dagster_graphql_path=dagster_graphql_path,
            repo_path=schedule.repository_path,
            variables=seven.json.dumps({"scheduleName": schedule.name}),
            result_file=result_file,
            dagster_home=dagster_home,
            env_vars="\n".join(
                [
                    "export {key}={value}".format(key=key, value=value)
                    for key, value in schedule.environment_vars.items()
                ]
            ),
        )

        with io.open(script_file, 'w', encoding='utf-8') as f:
            f.write(six.text_type(script_contents))

        st = os.stat(script_file)
        os.chmod(script_file, st.st_mode | stat.S_IEXEC)

        return script_file
