import glob
import os
import sqlite3
from contextlib import contextmanager

import six
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from dagster import check, seven
from dagster.core.definitions.environment_configs import SystemNamedDict
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.core.serdes import (
    ConfigurableClass,
    ConfigurableClassData,
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
)
from dagster.core.types import Field, String
from dagster.utils import mkdir_p

from ...pipeline_run import PipelineRunStatsSnapshot, PipelineRunStatus
from ..event_log import EventLogInvalidForRun, EventLogStorage

CREATE_EVENT_LOG_SQL = '''
CREATE TABLE IF NOT EXISTS event_logs (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    dagster_event_type TEXT,
    timestamp TEXT
)
'''

FETCH_EVENTS_SQL = '''
SELECT event FROM event_logs WHERE row_id > ? ORDER BY row_id ASC
'''

FETCH_STATS_SQL = '''
SELECT dagster_event_type, COUNT(1), MAX(timestamp) FROM event_logs GROUP BY dagster_event_type
'''

INSERT_EVENT_SQL = '''
INSERT INTO event_logs (event, dagster_event_type, timestamp) VALUES (?, ?, ?)
'''


class SqliteEventLogStorage(EventLogStorage, ConfigurableClass):
    def __init__(self, base_dir, inst_data=None):
        '''Note that idempotent initialization of the SQLite database is done on a per-run_id
        basis in the body of store_event, since each run is stored in a separate database.'''
        self._base_dir = check.str_param(base_dir, 'base_dir')
        mkdir_p(self._base_dir)

        self._known_run_ids = set([])
        self._watchers = {}
        self._obs = Observer()
        self._obs.start()
        self._inst_data = check.opt_inst_param(inst_data, 'inst_data', ConfigurableClassData)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return SystemNamedDict('SqliteEventLogStorageConfig', {'base_dir': Field(String)})

    @staticmethod
    def from_config_value(inst_data, config_value, **kwargs):
        return SqliteEventLogStorage(inst_data=inst_data, **dict(config_value, **kwargs))

    @contextmanager
    def _connect(self, run_id):
        try:
            with sqlite3.connect(self.filepath_for_run_id(run_id)) as conn:
                yield conn
        finally:
            conn.close()

    def filepath_for_run_id(self, run_id):
        check.str_param(run_id, 'run_id')
        return os.path.join(self._base_dir, '{run_id}.db'.format(run_id=run_id))

    def store_event(self, event):
        check.inst_param(event, 'event', EventRecord)
        run_id = event.run_id
        if not run_id in self._known_run_ids:
            with self._connect(run_id) as conn:
                conn.cursor().execute(CREATE_EVENT_LOG_SQL)
                conn.cursor().execute('PRAGMA journal_mode=WAL;')
                self._known_run_ids.add(run_id)
        with self._connect(run_id) as conn:
            dagster_event_type = None
            if event.is_dagster_event:
                dagster_event_type = event.dagster_event.event_type_value

            conn.cursor().execute(
                INSERT_EVENT_SQL,
                (serialize_dagster_namedtuple(event), dagster_event_type, event.timestamp),
            )

    def get_logs_for_run(self, run_id, cursor=-1):
        check.str_param(run_id, 'run_id')
        check.int_param(cursor, 'cursor')
        check.invariant(
            cursor >= -1,
            'Don\'t know what to do with negative cursor {cursor}'.format(cursor=cursor),
        )

        events = []
        if not os.path.exists(self.filepath_for_run_id(run_id)):
            return events

        cursor += 1  # adjust from 0 based offset to 1
        try:
            with self._connect(run_id) as conn:
                results = conn.cursor().execute(FETCH_EVENTS_SQL, (str(cursor),)).fetchall()
        except sqlite3.Error as err:
            six.raise_from(EventLogInvalidForRun(run_id=run_id), err)

        try:
            for (json_str,) in results:
                events.append(
                    check.inst_param(
                        deserialize_json_to_dagster_namedtuple(json_str), 'event', EventRecord
                    )
                )
        except (seven.JSONDecodeError, check.CheckError) as err:
            six.raise_from(EventLogInvalidForRun(run_id=run_id), err)

        return events

    def get_stats_for_run(self, run_id):
        if not os.path.exists(self.filepath_for_run_id(run_id)):
            return None

        try:
            with self._connect(run_id) as conn:
                results = conn.cursor().execute(FETCH_STATS_SQL).fetchall()
        except sqlite3.Error as err:
            six.raise_from(EventLogInvalidForRun(run_id=run_id), err)

        try:
            counts = {}
            times = {}
            for result in results:
                if result[0]:
                    counts[result[0]] = result[1]
                    times[result[0]] = result[2]

            return PipelineRunStatsSnapshot(
                run_id=run_id,
                steps_succeeded=counts.get(DagsterEventType.STEP_SUCCESS.value, 0),
                steps_failed=counts.get(DagsterEventType.STEP_FAILURE.value, 0),
                materializations=counts.get(DagsterEventType.STEP_MATERIALIZATION.value, 0),
                expectations=counts.get(DagsterEventType.STEP_EXPECTATION_RESULT.value, 0),
                start_time=float(times.get(DagsterEventType.PIPELINE_START.value, 0.0)),
                end_time=float(
                    times.get(
                        DagsterEventType.PIPELINE_SUCCESS.value,
                        times.get(DagsterEventType.PIPELINE_FAILURE.value, 0.0),
                    )
                ),
            )
        except (seven.JSONDecodeError, check.CheckError) as err:
            six.raise_from(EventLogInvalidForRun(run_id=run_id), err)

    def wipe(self):
        for filename in glob.glob(os.path.join(self._base_dir, '*.db')):
            os.unlink(filename)

    def delete_events(self, run_id):
        path = self.filepath_for_run_id(run_id)
        if os.path.exists(path):
            os.unlink(path)

    @property
    def is_persistent(self):
        return True

    def watch(self, run_id, start_cursor, callback):
        watchdog = EventLogStorageWatchdog(self, run_id, callback, start_cursor)
        self._watchers[run_id] = self._obs.schedule(watchdog, self._base_dir, True)

    def end_watch(self, run_id, handler):
        self._obs.remove_handler_for_watch(handler, self._watchers[run_id])
        del self._watchers[run_id]


class EventLogStorageWatchdog(PatternMatchingEventHandler):
    def __init__(self, event_log_storage, run_id, callback, start_cursor, **kwargs):
        self._event_log_storage = check.inst_param(
            event_log_storage, 'event_log_storage', EventLogStorage
        )
        self._run_id = check.str_param(run_id, 'run_id')
        self._cb = check.callable_param(callback, 'callback')
        self._log_path = event_log_storage.filepath_for_run_id(run_id)
        self._cursor = start_cursor
        super(EventLogStorageWatchdog, self).__init__(patterns=[self._log_path], **kwargs)

    def _process_log(self):
        events = self._event_log_storage.get_logs_for_run(self._run_id, self._cursor)
        self._cursor += len(events)
        for event in events:
            status = self._cb(event)

            if status == PipelineRunStatus.SUCCESS or status == PipelineRunStatus.FAILURE:
                self._event_log_storage.end_watch(self._run_id, self)

    def on_created(self, event):
        check.invariant(event.src_path == self._log_path)
        self._process_log()

    def on_modified(self, event):
        check.invariant(event.src_path == self._log_path)
        self._process_log()
