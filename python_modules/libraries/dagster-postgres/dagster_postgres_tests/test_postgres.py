import datetime

import psycopg2
import psycopg2.extensions
import pytest
from dagster_postgres.test import get_test_conn_string, implement_postgres_fixture

from dagster.utils import script_relative_path


@pytest.fixture(scope='session')
def docker_compose_db():
    with implement_postgres_fixture(script_relative_path('.')):
        yield


CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS run_events (
    message_id varchar(255) NOT NULL,
    run_id varchar(255) NOT NULL,
    timestamp timestamp NOT NULL,
    event_body varchar NOT NULL
)
'''

DROP_TABLE_SQL = 'DROP TABLE IF EXISTS run_events'


def get_conn_with_run_events():
    conn = psycopg2.connect(get_test_conn_string())
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    conn.cursor().execute(DROP_TABLE_SQL)
    conn.cursor().execute(CREATE_TABLE_SQL)
    return conn


def test_insert_select(docker_compose_db):  # pylint: disable=redefined-outer-name,unused-argument
    with get_conn_with_run_events().cursor() as curs:

        dt_now = datetime.datetime.now()

        body = 'contents'

        row_to_insert = ('message_id', 'run_id', dt_now, body)

        curs.execute(
            '''
            INSERT INTO run_events (message_id, run_id, timestamp, event_body)
            VALUES(%s, %s, %s, %s);
            ''',
            row_to_insert,
        )

        curs.execute('SELECT * from run_events')
        rows = curs.fetchall()
        assert len(rows) == 1
        assert rows[0] == row_to_insert
