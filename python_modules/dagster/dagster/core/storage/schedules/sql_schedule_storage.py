from abc import abstractmethod

import six
import sqlalchemy as db

from dagster import check
from dagster.core.definitions.repository import RepositoryDefinition
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.scheduler import Schedule
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple

from .base import ScheduleStorage
from .schema import ScheduleTable


class SqlScheduleStorage(ScheduleStorage):
    @abstractmethod
    def connect(self):
        '''Context manager yielding a sqlalchemy.engine.Connection.'''

    def execute(self, query):
        with self.connect() as conn:
            result_proxy = conn.execute(query)
            res = result_proxy.fetchall()
            result_proxy.close()

        return res

    def _rows_to_schedules(self, rows):
        return list(map(lambda r: deserialize_json_to_dagster_namedtuple(r[0]), rows))

    def all_schedules(self, repository=None):
        check.opt_inst_param(repository, 'repository', RepositoryDefinition)

        base_query = db.select([ScheduleTable.c.schedule_body]).select_from(ScheduleTable)

        if repository:
            query = base_query.where(ScheduleTable.c.repository_name == repository.name)

        rows = self.execute(query)
        return self._rows_to_schedules(rows)

    def get_schedule_by_name(self, repository, schedule_name):
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.str_param(schedule_name, 'schedule_name')

        query = (
            db.select([ScheduleTable.c.schedule_body])
            .select_from(ScheduleTable)
            .where(ScheduleTable.c.repository_name == repository.name)
            .where(ScheduleTable.c.schedule_name == schedule_name)
        )

        rows = self.execute(query)
        return deserialize_json_to_dagster_namedtuple(rows[0][0]) if len(rows) else None

    def add_schedule(self, repository, schedule):
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.inst_param(schedule, 'schedule', Schedule)

        with self.connect() as conn:
            try:
                schedule_insert = ScheduleTable.insert().values(  # pylint: disable=no-value-for-parameter
                    repository_name=repository.name,
                    schedule_name=schedule.name,
                    status=schedule.status.value,
                    schedule_body=serialize_dagster_namedtuple(schedule),
                )
                conn.execute(schedule_insert)
            except db.exc.IntegrityError as exc:
                six.raise_from(
                    DagsterInvariantViolationError(
                        'Schedule {schedule_name} for repository {repository_name} is already present '
                        'in storage'.format(
                            schedule_name=schedule.name, repository_name=repository.name
                        )
                    ),
                    exc,
                )

        return schedule

    def update_schedule(self, repository, schedule):
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.inst_param(schedule, 'schedule', Schedule)

        if not self.get_schedule_by_name(repository, schedule.name):
            raise DagsterInvariantViolationError(
                'Schedule {name} for repository {repository_name} is not present in storage'.format(
                    name=schedule.name, repository_name=repository.name
                )
            )

        with self.connect() as conn:
            conn.execute(
                ScheduleTable.update()  # pylint: disable=no-value-for-parameter
                .where(ScheduleTable.c.repository_name == repository.name)
                .where(ScheduleTable.c.schedule_name == schedule.name)
                .values(
                    status=schedule.status.value,
                    schedule_body=serialize_dagster_namedtuple(schedule),
                )
            )

    def delete_schedule(self, repository, schedule):
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.inst_param(schedule, 'schedule', Schedule)

        if not self.get_schedule_by_name(repository, schedule.name):
            raise DagsterInvariantViolationError(
                'Schedule {name} for repository {repository_name} is not present in storage'.format(
                    name=schedule.name, repository_name=repository.name
                )
            )

        with self.connect() as conn:
            conn.execute(
                ScheduleTable.delete()  # pylint: disable=no-value-for-parameter
                .where(ScheduleTable.c.repository_name == repository.name)
                .where(ScheduleTable.c.schedule_name == schedule.name)
            )

    def wipe(self):
        '''Clears the schedule storage.'''
        with self.connect() as conn:
            # https://stackoverflow.com/a/54386260/324449
            conn.execute(ScheduleTable.delete())  # pylint: disable=no-value-for-parameter
