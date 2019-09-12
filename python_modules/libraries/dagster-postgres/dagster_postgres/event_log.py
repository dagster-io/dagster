import multiprocessing
from collections import namedtuple

from dagster_postgres.utils import get_conn

from dagster import check
from dagster.core.events.log import EventRecord
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.core.storage.event_log import WatchableEventLogStorage

from .pynotify import await_pg_notifications

CREATE_EVENT_LOG_SQL = '''
CREATE TABLE IF NOT EXISTS event_log (
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(255) NOT NULL,
    event_body VARCHAR NOT NULL
)
'''

DELETE_EVENT_LOG_SQL = '''DELETE FROM event_log '''

DROP_EVENT_LOG_SQL = 'DROP TABLE IF EXISTS event_log'

CHANNEL_NAME = 'run_events'


class PostgresEventLogStorage(WatchableEventLogStorage):
    def __init__(self, conn_string):
        self.conn_string = check.str_param(conn_string, 'conn_string')

    @staticmethod
    def create_nuked_storage(conn_string):
        check.str_param(conn_string, 'conn_string')

        conn = get_conn(conn_string)
        conn.cursor().execute(DROP_EVENT_LOG_SQL)
        conn.cursor().execute(CREATE_EVENT_LOG_SQL)
        return PostgresEventLogStorage(conn_string)

    def get_logs_for_run(self, run_id, cursor=-1):
        '''Get all of the logs corresponding to a run.

        Args:
            run_id (str): The id of the run for which to fetch logs.
            cursor (Optional[int]): Zero-indexed logs will be returned starting from cursor + 1,
                i.e., if cursor is -1, all logs will be returned. (default: -1)
        '''
        check.str_param(run_id, 'run_id')
        check.int_param(cursor, 'cursor')
        check.invariant(cursor >= -1, 'Cursor must be -1 or greater')

        with get_conn(self.conn_string).cursor() as curs:
            FETCH_SQL = 'SELECT event_body FROM event_log WHERE run_id = %s OFFSET %s;'
            curs.execute(FETCH_SQL, (run_id, cursor + 1))

            rows = curs.fetchall()
            return list(map(lambda r: deserialize_json_to_dagster_namedtuple(r[0]), rows))

    def store_event(self, event):
        '''Store an event corresponding to a pipeline run.

        Args:
            run_id (str): The id of the run that generated the event.
            event (EventRecord): The event to store.
        '''

        check.inst_param(event, 'event', EventRecord)

        with get_conn(self.conn_string).cursor() as curs:
            event_body = serialize_dagster_namedtuple(event)
            curs.execute(
                '''INSERT INTO event_log (run_id, event_body) VALUES (%s, %s);
                NOTIFY {channel}, %s; '''.format(
                    channel=CHANNEL_NAME
                ),
                (event.run_id, event_body, event_body),
            )

    @property
    def is_persistent(self):
        return True

    def wipe(self):
        '''Clear the log storage.'''

        with get_conn(self.conn_string).cursor() as curs:
            curs.execute(DELETE_EVENT_LOG_SQL)

    def new_run(self, run_id):
        pass

    def watch(self, run_id, start_cursor, callback):
        raise NotImplementedError()

    def end_watch(self, run_id, handler):
        raise NotImplementedError()


EventWatcherProcessStartedEvent = namedtuple('EventWatcherProcessStartedEvent', '')
EventWatcherStart = namedtuple('EventWatcherStart', '')
EventWatcherEvent = namedtuple('EventWatcherEvent', 'payload')
EventWatchFailed = namedtuple('EventWatchFailed', 'message')
EventWatcherEnd = namedtuple('EventWatcherEnd', '')


POLLING_CADENCE = 0.25


def _postgres_event_watcher_event_loop(conn_string, queue, run_id_dict):
    init_called = False
    queue.put(EventWatcherProcessStartedEvent())
    try:
        for notif in await_pg_notifications(
            conn_string, channels=[CHANNEL_NAME], timeout=POLLING_CADENCE, yield_on_timeout=True
        ):
            if not init_called:
                init_called = True
                queue.put(EventWatcherStart())

            if notif is not None:
                event_record = deserialize_json_to_dagster_namedtuple(notif.payload)
                if event_record.run_id in run_id_dict:
                    queue.put(EventWatcherEvent(event_record))
            else:
                # The polling window has timed out
                pass

    except Exception as e:  # pylint: disable=broad-except
        queue.put(EventWatchFailed(message=str(e)))
    finally:
        queue.put(EventWatcherEnd())


def create_event_watcher(conn_string):
    check.str_param(conn_string, 'conn_string')

    queue = multiprocessing.Queue()
    m_dict = multiprocessing.Manager().dict()
    process = multiprocessing.Process(
        target=_postgres_event_watcher_event_loop, args=(conn_string, queue, m_dict)
    )

    process.start()

    # block and ensure that the process has actually started. This was required
    # to get processes to start in linux in buildkite.
    check.inst(queue.get(block=True), EventWatcherProcessStartedEvent)

    return PostgresEventWatcher(process, queue, m_dict)


class PostgresEventWatcher:
    def __init__(self, process, queue, run_id_dict):
        self.process = check.inst_param(process, 'process', multiprocessing.Process)
        self.run_id_dict = check.inst_param(
            run_id_dict, 'run_id_dict', multiprocessing.managers.DictProxy
        )
        self.queue = check.inst_param(queue, 'queue', multiprocessing.queues.Queue)

    def has_run_id(self, run_id):
        return run_id in self.run_id_dict

    def watch_run(self, run_id):
        self.run_id_dict[run_id] = True

    def unwatch_run(self, run_id):
        del self.run_id_dict[run_id]

    def close(self):
        self.process.terminate()
