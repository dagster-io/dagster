from dagster import check
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.storage.runs import RunStorage

from .utils import get_conn

CREATE_RUN_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS runs (
    run_id VARCHAR(255) NOT NULL,
    pipeline_name VARCHAR NOT NULL,
    status VARCHAR(63) NOT NULL,
    run_body VARCHAR NOT NULL
)
'''

DROP_RUN_TABLE_SQL = '''
DROP TABLE IF EXISTS runs
'''

INSERT_RUN_SQL = '''
INSERT INTO runs (run_id, pipeline_name, status, run_body)
VALUES (%s, %s, %s, %s)
'''

DELETE_FROM_SQL = 'DELETE FROM runs'


class PostgresRunStorage(RunStorage):
    def __init__(self, conn_string):
        self.conn_string = conn_string

    @staticmethod
    def create_nuked_storage(conn_string):
        check.str_param(conn_string, 'conn_string')

        conn = get_conn(conn_string)
        conn.cursor().execute(DROP_RUN_TABLE_SQL)
        conn.cursor().execute(CREATE_RUN_TABLE_SQL)
        return PostgresRunStorage(conn_string)

    def add_run(self, pipeline_run):
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

        conn = get_conn(self.conn_string)
        with conn.cursor() as curs:
            curs.execute(
                INSERT_RUN_SQL,
                (
                    pipeline_run.run_id,
                    pipeline_run.pipeline_name,
                    str(pipeline_run.status),
                    serialize_dagster_namedtuple(pipeline_run),
                ),
            )

    def handle_run_event(self, run_id, event):
        check.str_param(run_id, 'run_id')
        check.inst_param(event, 'event', DagsterEvent)

        lookup = {
            DagsterEventType.PIPELINE_START: PipelineRunStatus.STARTED,
            DagsterEventType.PIPELINE_SUCCESS: PipelineRunStatus.SUCCESS,
            DagsterEventType.PIPELINE_FAILURE: PipelineRunStatus.FAILURE,
        }

        if event.event_type not in lookup:
            return

        run = self.get_run_by_id(run_id)
        if not run:
            # TODO log?
            return

        SQL_UPDATE = '''
        UPDATE runs
        SET status = %s, run_body = %s
        WHERE run_id = %s
        '''
        conn = get_conn(self.conn_string)
        new_pipeline_status = lookup[event.event_type]
        with conn.cursor() as curs:
            curs.execute(
                SQL_UPDATE,
                (
                    str(new_pipeline_status),
                    serialize_dagster_namedtuple(run.run_with_status(new_pipeline_status)),
                    run_id,
                ),
            )

    def _rows_to_runs(self, rows):
        return list(map(lambda r: deserialize_json_to_dagster_namedtuple(r[0]), rows))

    def all_runs(self):
        '''Return all the runs present in the storage.

        Returns:
            Iterable[(str, PipelineRun)]: Tuples of run_id, pipeline_run.
        '''

        conn = get_conn(self.conn_string)
        with conn.cursor() as curs:
            curs.execute('SELECT run_body FROM runs')
            rows = curs.fetchall()
            return self._rows_to_runs(rows)

    def all_runs_for_pipeline(self, pipeline_name):
        '''Return all the runs present in the storage for a given pipeline.

        Args:
            pipeline_name (str): The pipeline to index on

        Returns:
            Iterable[(str, PipelineRun)]: Tuples of run_id, pipeline_run.
        '''
        check.str_param(pipeline_name, 'pipeline_name')

        conn = get_conn(self.conn_string)
        with conn.cursor() as curs:
            curs.execute('SELECT run_body FROM runs WHERE pipeline_name = %s', (pipeline_name,))
            rows = curs.fetchall()
            return self._rows_to_runs(rows)

    def get_run_by_id(self, run_id):
        '''Get a run by its id.

        Args:
            run_id (str): THe id of the run

        Returns:
            Optional[PipelineRun]
        '''
        check.str_param(run_id, 'run_id')

        conn = get_conn(self.conn_string)
        with conn.cursor() as curs:
            curs.execute('SELECT run_body FROM runs WHERE run_id = %s', (run_id,))
            rows = curs.fetchall()
            return deserialize_json_to_dagster_namedtuple(rows[0][0]) if len(rows) else None

    def has_run(self, run_id):
        check.str_param(run_id, 'run_id')
        return bool(self.get_run_by_id(run_id))

    def wipe(self):
        '''Clears the run storage.'''
        conn = get_conn(self.conn_string)
        with conn.cursor() as curs:
            curs.execute(DELETE_FROM_SQL)

    def is_persistent(self):
        return True
