import datetime
import threading
from collections import namedtuple
from contextlib import contextmanager

import sqlalchemy as db

from dagster import check
from dagster.core.definitions.environment_configs import SystemNamedDict
from dagster.core.events.log import EventRecord
from dagster.core.serdes import (
    ConfigurableClass,
    ConfigurableClassData,
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
)
from dagster.core.storage.event_log import (
    SqlEventLogStorage,
    SqlEventLogStorageMetadata,
    SqlEventLogStorageTable,
)
from dagster.core.storage.sql import create_engine, get_alembic_config, run_alembic_upgrade
from dagster.core.types import Field, String

from ..pynotify import await_pg_notifications

CHANNEL_NAME = 'run_events'

# Why? Because this is about as long as we expect a roundtrip to RDS to take.
WATCHER_POLL_INTERVAL = 0.2


class PostgresEventLogStorage(SqlEventLogStorage, ConfigurableClass):
    def __init__(self, postgres_url, inst_data=None):
        self.postgres_url = check.str_param(postgres_url, 'postgres_url')
        self._event_watcher = PostgresEventWatcher(self.postgres_url)
        with self.get_engine() as engine:
            SqlEventLogStorageMetadata.create_all(engine)
        self._inst_data = check.opt_inst_param(inst_data, 'inst_data', ConfigurableClassData)

    @contextmanager
    def get_engine(self):
        engine = create_engine(
            self.postgres_url, isolation_level='AUTOCOMMIT', poolclass=db.pool.NullPool
        )
        try:
            yield engine
        finally:
            engine.dispose()

    def upgrade(self):
        alembic_config = get_alembic_config(__file__)
        with self.get_engine() as engine:
            run_alembic_upgrade(alembic_config, engine)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return SystemNamedDict('PostgresRunStorageConfig', {'postgres_url': Field(String)})

    @staticmethod
    def from_config_value(inst_data, config_value, **kwargs):
        return PostgresEventLogStorage(inst_data=inst_data, **dict(config_value, **kwargs))

    @staticmethod
    def create_clean_storage(conn_string):
        inst = PostgresEventLogStorage(conn_string)
        inst.wipe()
        return inst

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

        with self.connect() as conn:
            # https://stackoverflow.com/a/54386260/324449
            event_insert = SqlEventLogStorageTable.insert().values(  # pylint: disable=no-value-for-parameter
                run_id=run_id,
                event=serialize_dagster_namedtuple(event),
                dagster_event_type=dagster_event_type,
                timestamp=datetime.datetime.fromtimestamp(event.timestamp),
            )
            result_proxy = conn.execute(
                event_insert.returning(
                    SqlEventLogStorageTable.c.run_id, SqlEventLogStorageTable.c.id
                )
            )
            res = result_proxy.fetchone()
            result_proxy.close()
            conn.execute(
                '''NOTIFY {channel}, %s; '''.format(channel=CHANNEL_NAME),
                (res[0] + '_' + str(res[1]),),
            )

    @contextmanager
    def connect(self, run_id=None):
        with self.get_engine() as engine:
            yield engine

    def watch(self, run_id, start_cursor, callback):
        self._event_watcher.watch_run(run_id, start_cursor, callback)

    def end_watch(self, run_id, handler):
        self._event_watcher.unwatch_run(run_id, handler)

    @property
    def event_watcher(self):
        return self._event_watcher

    def __del__(self):
        # Keep the inherent limitations of __del__ in Python in mind!
        self.dispose()

    def dispose(self):
        self._event_watcher.close()


EventWatcherProcessStartedEvent = namedtuple('EventWatcherProcessStartedEvent', '')
EventWatcherStart = namedtuple('EventWatcherStart', '')
EventWatcherEvent = namedtuple('EventWatcherEvent', 'payload')
EventWatchFailed = namedtuple('EventWatchFailed', 'message')
EventWatcherEnd = namedtuple('EventWatcherEnd', '')

EventWatcherThreadEvents = (
    EventWatcherProcessStartedEvent,
    EventWatcherStart,
    EventWatcherEvent,
    EventWatchFailed,
    EventWatcherEnd,
)
EventWatcherThreadNoopEvents = (EventWatcherProcessStartedEvent, EventWatcherStart)
EventWatcherThreadEndEvents = (EventWatchFailed, EventWatcherEnd)

POLLING_CADENCE = 0.25

TERMINATE_EVENT_LOOP = 'TERMINATE_EVENT_LOOP'


def watcher_thread(conn_string, run_id_dict, handlers_dict, dict_lock, watcher_thread_exit):

    for notif in await_pg_notifications(
        conn_string,
        channels=[CHANNEL_NAME],
        timeout=POLLING_CADENCE,
        yield_on_timeout=True,
        exit_event=watcher_thread_exit,
    ):
        if notif is None:
            if watcher_thread_exit.is_set():
                break
        else:
            run_id, index_str = notif.payload.split('_')
            if run_id not in run_id_dict:
                continue

            index = int(index_str)
            with dict_lock:
                handlers = handlers_dict.get(run_id, [])

            engine = create_engine(
                conn_string, isolation_level='AUTOCOMMIT', poolclass=db.pool.NullPool
            )
            try:
                res = engine.execute(
                    db.select([SqlEventLogStorageTable.c.event]).where(
                        SqlEventLogStorageTable.c.id == index
                    ),
                )
                dagster_event = deserialize_json_to_dagster_namedtuple(res.fetchone()[0])
            finally:
                engine.dispose()

            for (cursor, callback) in handlers:
                if index >= cursor:
                    callback(dagster_event)


class PostgresEventWatcher(object):
    def __init__(self, conn_string):
        self._run_id_dict = {}
        self._handlers_dict = {}
        self._dict_lock = threading.Lock()
        self._conn_string = conn_string
        self._watcher_thread_exit = threading.Event()
        self._watcher_thread = threading.Thread(
            target=watcher_thread,
            args=(
                self._conn_string,
                self._run_id_dict,
                self._handlers_dict,
                self._dict_lock,
                self._watcher_thread_exit,
            ),
        )
        self._watcher_thread.daemon = True
        self._watcher_thread.start()

    def has_run_id(self, run_id):
        with self._dict_lock:
            _has_run_id = run_id in self._run_id_dict
        return _has_run_id

    def watch_run(self, run_id, start_cursor, callback):
        with self._dict_lock:
            if run_id in self._run_id_dict:
                self._handlers_dict[run_id].append((start_cursor, callback))
            else:
                # See: https://docs.python.org/2/library/multiprocessing.html#multiprocessing.managers.SyncManager
                run_id_dict = self._run_id_dict
                run_id_dict[run_id] = None
                self._run_id_dict = run_id_dict
                self._handlers_dict[run_id] = [(start_cursor, callback)]

    def unwatch_run(self, run_id, handler):
        with self._dict_lock:
            if run_id in self._run_id_dict:
                self._handlers_dict[run_id] = [
                    (start_cursor, callback)
                    for (start_cursor, callback) in self._handlers_dict[run_id]
                    if callback != handler
                ]
            if not self._handlers_dict[run_id]:
                del self._handlers_dict[run_id]
                run_id_dict = self._run_id_dict
                del run_id_dict[run_id]
                self._run_id_dict = run_id_dict

    def close(self):
        self._watcher_thread_exit.set()
