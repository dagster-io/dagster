import datetime
from abc import abstractmethod

import six
import sqlalchemy as db

from dagster import check, seven
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.utils import datetime_as_float

from ..pipeline_run import PipelineRunStatsSnapshot
from .base import DagsterEventLogInvalidForRun, EventLogStorage
from .schema import SqlEventLogStorageTable


class SqlEventLogStorage(EventLogStorage):
    @abstractmethod
    def connect(self, run_id=None):
        '''Context manager yielding a connection.

        Args:
            run_id (Optional[str]): Enables those storages which shard based on run_id, e.g.,
                SqliteEventLogStorage, to connect appropriately.
        '''

    @abstractmethod
    def upgrade(self):
        '''This method should perform any schema or data migrations necessary to bring an
        out-of-date instance of the storage up to date.
        '''

    def store_event(self, event):
        '''Store an event corresponding to a pipeline run.

        Args:
            event (EventRecord): The event to store.
        '''
        check.inst_param(event, 'event', EventRecord)

        dagster_event_type = None
        if event.is_dagster_event:
            dagster_event_type = event.dagster_event.event_type_value

        run_id = event.run_id

        # https://stackoverflow.com/a/54386260/324449
        event_insert = SqlEventLogStorageTable.insert().values(  # pylint: disable=no-value-for-parameter
            run_id=run_id,
            event=serialize_dagster_namedtuple(event),
            dagster_event_type=dagster_event_type,
            timestamp=datetime.datetime.fromtimestamp(event.timestamp),
        )

        with self.connect(run_id) as conn:
            conn.execute(event_insert)

    def get_logs_for_run(self, run_id, cursor=-1):
        '''Get all of the logs corresponding to a run.

        Args:
            run_id (str): The id of the run for which to fetch logs.
            cursor (Optional[int]): Zero-indexed logs will be returned starting from cursor + 1,
                i.e., if cursor is -1, all logs will be returned. (default: -1)
        '''
        check.str_param(run_id, 'run_id')
        check.int_param(cursor, 'cursor')
        check.invariant(
            cursor >= -1,
            'Don\'t know what to do with negative cursor {cursor}'.format(cursor=cursor),
        )

        query = (
            db.select([SqlEventLogStorageTable.c.event])
            .where(SqlEventLogStorageTable.c.run_id == run_id)
            .where(SqlEventLogStorageTable.c.id >= cursor)
            .order_by(SqlEventLogStorageTable.c.id.asc())
        )

        with self.connect(run_id) as conn:
            results = conn.execute(query).fetchall()

        events = []

        try:
            for (json_str,) in results:
                events.append(
                    check.inst_param(
                        deserialize_json_to_dagster_namedtuple(json_str), 'event', EventRecord
                    )
                )
        except (seven.JSONDecodeError, check.CheckError) as err:
            six.raise_from(DagsterEventLogInvalidForRun(run_id=run_id), err)

        return events

    def get_stats_for_run(self, run_id):
        check.str_param(run_id, 'run_id')

        query = (
            db.select(
                [
                    SqlEventLogStorageTable.c.dagster_event_type,
                    db.func.count().label('n_events_of_type'),
                    db.func.max(SqlEventLogStorageTable.c.timestamp).label('last_event_timestamp'),
                ]
            )
            .where(SqlEventLogStorageTable.c.run_id == run_id)
            .group_by('dagster_event_type')
        )

        with self.connect(run_id) as conn:
            results = conn.execute(query).fetchall()

        try:
            counts = {}
            times = {}
            for result in results:
                if result[0]:
                    counts[result[0]] = result[1]
                    times[result[0]] = result[2]

            start_time = times.get(DagsterEventType.PIPELINE_START.value, None)
            end_time = times.get(
                DagsterEventType.PIPELINE_SUCCESS.value,
                times.get(DagsterEventType.PIPELINE_FAILURE.value, None),
            )

            return PipelineRunStatsSnapshot(
                run_id=run_id,
                steps_succeeded=counts.get(DagsterEventType.STEP_SUCCESS.value, 0),
                steps_failed=counts.get(DagsterEventType.STEP_FAILURE.value, 0),
                materializations=counts.get(DagsterEventType.STEP_MATERIALIZATION.value, 0),
                expectations=counts.get(DagsterEventType.STEP_EXPECTATION_RESULT.value, 0),
                start_time=datetime_as_float(start_time) if start_time else None,
                end_time=datetime_as_float(end_time) if end_time else None,
            )
        except (seven.JSONDecodeError, check.CheckError) as err:
            six.raise_from(DagsterEventLogInvalidForRun(run_id=run_id), err)

    def wipe(self):
        '''Clears the event log storage.'''
        # Should be overridden by SqliteEventLogStorage and other storages that shard based on
        # run_id
        # https://stackoverflow.com/a/54386260/324449
        with self.connect() as conn:
            conn.execute(SqlEventLogStorageTable.delete())  # pylint: disable=no-value-for-parameter

    def delete_events(self, run_id):
        check.str_param(run_id, 'run_id')

        statement = SqlEventLogStorageTable.delete().where(  # pylint: disable=no-value-for-parameter
            SqlEventLogStorageTable.c.run_id == run_id
        )

        with self.connect(run_id) as conn:
            conn.execute(statement)

    @property
    def is_persistent(self):
        return True
