import io
import json
import os
import stat
import uuid
from collections import OrderedDict

import six
from crontab import CronTab

from dagster import DagsterInvariantViolationError, ScheduleDefinition, check, seven, utils
from dagster.core.scheduler import RunningSchedule, Scheduler


class SystemCronScheduler(Scheduler):
    def __init__(self, schedule_dir):
        self._schedule_dir = check.str_param(schedule_dir, 'schedule_dir')
        self._schedules = OrderedDict()

        self._load_schedules()

    def all_schedules(self):
        return [s for s in self._schedules.values()]

    def all_schedules_for_pipeline(self, pipeline_name):
        return [
            s
            for s in self.all_schedules()
            if s.execution_params['selector']['name'] == pipeline_name
        ]

    def get_schedule_by_name(self, name):
        return self._schedules.get(name)

    def start_schedule(self, schedule_definition, python_path, repository_path):
        if schedule_definition.name in self._schedules:
            raise DagsterInvariantViolationError(
                ('You have attempted to start schedule {name}, but it is already running.').format(
                    name=schedule_definition.name
                )
            )

        schedule_id = str(uuid.uuid4())

        schedule = RunningSchedule(schedule_id, schedule_definition, python_path, repository_path)

        self._schedules[schedule_definition.name] = schedule
        self._write_schedule_to_file(schedule)

        script_file = self._write_bash_script_to_file(schedule)
        self._start_cron_job(script_file, schedule)

        return schedule

    def end_schedule(self, schedule_definition):
        if schedule_definition.name not in self._schedules:
            raise DagsterInvariantViolationError(
                ('You have attempted to end schedule {name}, but it is not running.').format(
                    name=schedule_definition.name
                )
            )

        schedule = self.get_schedule_by_name(schedule_definition.name)

        self._schedules.pop(schedule_definition.name)
        self._end_cron_job(schedule)

        os.remove(self._get_metadata_file_path(schedule))
        os.remove(self._get_bash_script_file_path(schedule))

        return schedule

    def _start_cron_job(self, script_file, schedule):
        my_cron = CronTab(user=True)
        job = my_cron.new(command=script_file, comment=schedule.schedule_id)
        job.setall(schedule.schedule_definition.cron_schedule)
        my_cron.write()

    def _end_cron_job(self, schedule):
        my_cron = CronTab(user=True)
        my_cron.remove_all(comment=schedule.schedule_id)
        my_cron.write()

    def _get_file_prefix(self, schedule):
        return os.path.join(
            self._schedule_dir,
            '{}_{}'.format(schedule.schedule_definition.name, schedule.schedule_id),
        )

    def _get_metadata_file_path(self, schedule):
        file_prefix = self._get_file_prefix(schedule)
        return '{}.json'.format(file_prefix)

    def _get_bash_script_file_path(self, schedule):
        file_prefix = self._get_file_prefix(schedule)
        return '{}.sh'.format(file_prefix)

    def _get_logs_file_path(self, schedule):
        file_prefix = self._get_file_prefix(schedule)
        return '{}.log'.format(file_prefix)

    def _write_bash_script_to_file(self, schedule):
        script_file = self._get_bash_script_file_path(schedule)
        log_file = self._get_logs_file_path(schedule)

        dagster_graphql_path = os.path.join(
            os.path.dirname(schedule.python_path), 'dagster-graphql'
        )
        dagster_home = os.getenv('DAGSTER_HOME')

        script_contents = '''
            #!/bin/bash
            export DAGSTER_HOME={dagster_home}
            export LANG=en_US.UTF-8
            {env_vars}

            {dagster_graphql_path} -p startPipelineExecution -v '{variables}' -y "{repo_path}" >> {log_file} 2>&1
        '''.format(
            dagster_graphql_path=dagster_graphql_path,
            repo_path=schedule.repository_path,
            variables=json.dumps(
                {"executionParams": schedule.schedule_definition.execution_params}
            ),
            log_file=log_file,
            dagster_home=dagster_home,
            env_vars="\n".join(
                [
                    "export {key}={value}".format(key=key, value=value)
                    for key, value in schedule.schedule_definition.environment_vars.items()
                ]
            ),
        )

        with io.open(script_file, 'w', encoding='utf-8') as f:
            f.write(six.text_type(script_contents))

        st = os.stat(script_file)
        os.chmod(script_file, st.st_mode | stat.S_IEXEC)

        return script_file

    def _write_schedule_to_file(self, schedule):
        metadata_file = self._get_metadata_file_path(schedule)
        schedule_definition = schedule.schedule_definition
        with io.open(metadata_file, 'w', encoding='utf-8') as f:
            json_str = seven.json.dumps(
                {
                    'schedule_id': schedule.schedule_id,
                    'name': schedule_definition.name,
                    'cron_schedule': schedule_definition.cron_schedule,
                    'execution_params': schedule_definition.execution_params,
                    'python_path': schedule.python_path,
                    'repository_path': schedule.repository_path,
                }
            )
            f.write(six.text_type(json_str))

        return metadata_file

    def _load_schedules(self):
        utils.mkdir_p(self._schedule_dir)

        for file in os.listdir(self._schedule_dir):
            if not file.endswith('.json'):
                continue
            file_path = os.path.join(self._schedule_dir, file)
            with open(file_path) as data:
                try:
                    data = json.load(data)
                    schedule = RunningSchedule(
                        data['schedule_id'],
                        ScheduleDefinition(
                            name=data['name'],
                            cron_schedule=data['cron_schedule'],
                            execution_params=data['execution_params'],
                        ),
                        python_path=data['python_path'],
                        repository_path=data['repository_path'],
                    )
                    self._schedules[schedule.schedule_definition.name] = schedule

                except Exception as ex:  # pylint: disable=broad-except
                    six.raise_from(
                        Exception(
                            'Could not parse dagit schedule from {file_name} in {dir_name}. {ex}: {msg}'.format(
                                file_name=file,
                                dir_name=self._schedule_dir,
                                ex=type(ex).__name__,
                                msg=ex,
                            )
                        ),
                        ex,
                    )
