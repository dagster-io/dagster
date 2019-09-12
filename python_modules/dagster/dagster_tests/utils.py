import uuid
from collections import OrderedDict

from dagster import DagsterInvariantViolationError, check
from dagster.core.scheduler import RunningSchedule, Scheduler


class MockScheduler(Scheduler):
    def __init__(self, schedule_defs, artifacts_dir):
        self._artifacts_dir = artifacts_dir
        self._schedule_defs = {}
        for defn in schedule_defs:
            check.invariant(
                defn.name not in self._schedule_defs,
                'Duplicate schedules named {name}'.format(name=defn.name),
            )
            self._schedule_defs[defn.name] = defn

        self._schedules = OrderedDict()

    def get_all_schedule_defs(self):
        return [self._schedule_defs[name] for name in sorted(self._schedule_defs.keys())]

    def get_schedule_def(self, name):
        check.str_param(name, 'name')

        if name in self._schedule_defs:
            return self._schedule_defs[name]
        else:
            raise DagsterInvariantViolationError(
                'Could not find schedule "{name}". Found: {schedule_names}.'.format(
                    name=name,
                    schedule_names=', '.join(
                        [
                            '"{schedule_name}"'.format(schedule_name=schedule_name)
                            for schedule_name in self._schedule_defs.keys()
                        ]
                    ),
                )
            )

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
                'You have attempted to start schedule {name}, but it is already running.'.format(
                    name=schedule_definition.name
                )
            )

        schedule_id = str(uuid.uuid4())
        schedule = RunningSchedule(schedule_id, schedule_definition, python_path, repository_path)

        self._schedules[schedule_definition.name] = schedule
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

        return schedule
