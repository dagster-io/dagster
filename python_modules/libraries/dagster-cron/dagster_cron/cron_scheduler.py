import io
import os
import stat

import six
from crontab import CronTab

from dagster import DagsterInvariantViolationError, check, seven, utils
from dagster.core.scheduler import ScheduleStatus, Scheduler
from dagster.core.scheduler.storage import ScheduleStorage


class SystemCronScheduler(Scheduler):
    '''Scheduler class for system cron-backed scheduling.

    Pass this class as the ``scheduler`` argument to the :py:func:`@schedules <dagster.schedules>`
    API -- do not instantiate it directly.

    '''

    def __init__(self, artifacts_dir, schedule_storage):
        check.inst_param(schedule_storage, 'schedule_storage', ScheduleStorage)
        check.str_param(artifacts_dir, 'artifacts_dir')
        self._storage = schedule_storage
        self._artifacts_dir = artifacts_dir

    def all_schedules(self, repository_name):
        return self._storage.all_schedules(repository_name)

    def get_schedule_by_name(self, repository_name, schedule_name):
        return self._storage.get_schedule_by_name(repository_name, schedule_name)

    def start_schedule(self, repository_name, schedule_name):
        schedule = self.get_schedule_by_name(repository_name, schedule_name)
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
        self._storage.update_schedule(repository_name, started_schedule)
        self._start_cron_job(repository_name, started_schedule)

        return started_schedule

    def stop_schedule(self, repository_name, schedule_name):
        schedule = self.get_schedule_by_name(repository_name, schedule_name)
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
        self._storage.update_schedule(repository_name, stopped_schedule)
        self._end_cron_job(repository_name, schedule)

        return stopped_schedule

    def end_schedule(self, repository_name, schedule_name):
        schedule = self.get_schedule_by_name(repository_name, schedule_name)
        if not schedule:
            raise DagsterInvariantViolationError(
                'You have attempted to end schedule {name}, but it is not running.'.format(
                    name=schedule_name
                )
            )

        self._storage.delete_schedule(schedule)
        self._end_cron_job(repository_name, schedule)

        return schedule

    def log_path_for_schedule(self, repository_name, schedule_name):
        schedule = self.get_schedule_by_name(repository_name, schedule_name)
        if not schedule:
            raise DagsterInvariantViolationError(
                'You have attempted to get the logs for schedule {name}, but it is not '
                'running'.format(name=schedule_name)
            )

        log_dir = self._storage.get_log_path(repository_name, schedule)
        return log_dir

    def wipe(self):
        self._storage.wipe()

        # Delete any other crontabs that are from dagster
        cron = CronTab(user=True)
        for job in cron:
            if 'dagster-schedule:' in job.comment:
                cron.remove_all(comment=job.comment)

        cron.write()

    def _get_file_prefix(self, repository_name, schedule):
        return os.path.join(self._artifacts_dir, '{}.{}'.format(repository_name, schedule.name))

    def _get_bash_script_file_path(self, repository_name, schedule):
        file_prefix = self._get_file_prefix(repository_name, schedule)
        return '{}.sh'.format(file_prefix)

    def _start_cron_job(self, repository_name, schedule):
        script_file = self._write_bash_script_to_file(repository_name, schedule)

        my_cron = CronTab(user=True)
        job = my_cron.new(
            command=script_file,
            comment='dagster-schedule: {repository_name}.{schedule_name}'.format(
                repository_name=repository_name, schedule_name=schedule.name
            ),
        )
        job.setall(schedule.cron_schedule)
        my_cron.write()

    def _end_cron_job(self, repository_name, schedule):
        my_cron = CronTab(user=True)
        my_cron.remove_all(comment='dagster-schedule: ' + schedule.name)
        my_cron.write()

        script_file = self._get_bash_script_file_path(repository_name, schedule)
        if os.path.isfile(script_file):
            os.remove(script_file)

    def _write_bash_script_to_file(self, repository_name, schedule):
        script_file = self._get_bash_script_file_path(repository_name, schedule)

        log_dir = self.log_path_for_schedule(repository_name, schedule.name)
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
