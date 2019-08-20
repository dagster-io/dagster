import io
import uuid

import json
import os
import stat

from collections import OrderedDict

import six

from dagster import check, seven, utils

from dagster.utils import dagster_home_dir
from .scheduler import Scheduler, RunSchedule
from crontab import CronTab


class SystemCronScheduler(Scheduler):
    def __init__(self, schedule_dir):
        self._schedule_dir = check.str_param(schedule_dir, 'schedule_dir')
        self._schedules = OrderedDict()

        self._load_schedules()

    def create_schedule(self, *args, **kwargs):
        schedule_id = str(uuid.uuid4())
        schedule = RunSchedule(schedule_id=schedule_id, *args, **kwargs)

        self._write_schedule_to_file(schedule)
        self._schedules[schedule_id] = schedule

        return schedule

    def remove_schedule(self, id_):
        schedule = self._schedules.pop(id_)
        os.remove(self._get_metadata_file_path(schedule))

        return schedule

    def all_schedules(self):
        return [s for s in self._schedules.values()]

    def all_schedules_for_pipeline(self, pipeline_name):
        return [
            s
            for s in self.all_schedules()
            if s.execution_params['selector']['name'] == pipeline_name
        ]

    def get_schedule_by_id(self, id_):
        return self._schedules.get(id_)

    def start_schedule(self, id_, python_path, repository_path):
        schedule = self.get_schedule_by_id(id_)
        started_schedule = schedule.start_schedule(python_path, repository_path)

        self._schedules[id_] = started_schedule
        self._write_schedule_to_file(started_schedule)

        script_file = self._write_bash_script_to_file(started_schedule)
        self._start_cron_job(script_file, started_schedule)

        return started_schedule

    def end_schedule(self, id_):
        schedule = self.get_schedule_by_id(id_)
        ended_schedule = schedule.end_schedule()

        self._schedules[id_] = ended_schedule

        self._end_cron_job(ended_schedule)
        self._write_schedule_to_file(ended_schedule)

        os.remove(self._get_bash_script_file_path(ended_schedule))

        return ended_schedule

    def _start_cron_job(self, script_file, schedule):
        my_cron = CronTab(user=True)
        job = my_cron.new(command=script_file, comment=schedule.schedule_id)
        job.setall(schedule.cron_schedule)
        my_cron.write()

    def _end_cron_job(self, schedule):
        my_cron = CronTab(user=True)
        my_cron.remove_all(comment=schedule.schedule_id)
        my_cron.write()

    def _get_file_prefix(self, schedule):
        return os.path.join(self._schedule_dir, '{}_{}'.format(schedule.name, schedule.schedule_id))

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

        dagster_graphql_path = schedule.python_path.replace("/bin/python", "/bin/dagster-graphql")
        dagster_home = dagster_home_dir()

        script_contents = '''
            #!/bin/bash
            export DAGSTER_HOME={dagster_home}
            export LANG=en_US.UTF-8

            {dagster_graphql_path} -p startPipelineExecution -v '{variables}' --log -y "{repo_path}" >> {log_file} 2>&1
        '''.format(
            dagster_graphql_path=dagster_graphql_path,
            repo_path=schedule.repository_path,
            variables=json.dumps({"executionParams": schedule.execution_params}),
            log_file=log_file,
            dagster_home=dagster_home,
        )

        with io.open(script_file, 'w', encoding='utf-8') as f:
            f.write(six.text_type(script_contents))

        st = os.stat(script_file)
        os.chmod(script_file, st.st_mode | stat.S_IEXEC)

        return script_file

    def _write_schedule_to_file(self, schedule):
        metadata_file = self._get_metadata_file_path(schedule)
        with io.open(metadata_file, 'w', encoding='utf-8') as f:
            json_str = seven.json.dumps(
                {
                    'schedule_id': schedule.schedule_id,
                    'name': schedule.name,
                    'cron_schedule': schedule.cron_schedule,
                    'python_path': schedule.python_path,
                    'repository_path': schedule.repository_path,
                    'execution_params': schedule.execution_params,
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
                    schedule = RunSchedule(
                        schedule_id=data['schedule_id'],
                        name=data['name'],
                        cron_schedule=data['cron_schedule'],
                        python_path=data['python_path'],
                        repository_path=data['repository_path'],
                        execution_params=data['execution_params'],
                    )
                    self._schedules[schedule.schedule_id] = schedule

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
