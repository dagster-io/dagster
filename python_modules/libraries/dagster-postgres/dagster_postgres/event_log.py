from dagster_postgres.utils import get_conn

from dagster import check
from dagster.core.events.log import EventRecord
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.core.storage.event_log import WatchableEventLogStorage

CREATE_EVENT_LOG_SQL = '''
CREATE TABLE IF NOT EXISTS event_log (
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(255) NOT NULL,
    event_body VARCHAR NOT NULL
)
'''

DELETE_EVENT_LOG_SQL = '''DELETE FROM event_log '''

DROP_EVENT_LOG_SQL = 'DROP TABLE IF EXISTS event_log'


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
            curs.execute(
                'INSERT INTO event_log (run_id, event_body) VALUES (%s, %s)',
                (event.run_id, serialize_dagster_namedtuple(event)),
            )

    @property
    def is_persistent(self):
        return True

    def wipe(self):
        '''Clear the log storage.'''

        with get_conn(self.conn_string).cursor() as curs:
            curs.execute(DELETE_EVENT_LOG_SQL)

    def watch(self, run_id, start_cursor, callback):
        raise NotImplementedError()

    def end_watch(self, run_id, handler):
        raise NotImplementedError()
