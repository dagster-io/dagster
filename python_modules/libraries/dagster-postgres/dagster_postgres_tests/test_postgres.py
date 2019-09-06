import datetime
import os

import psycopg2
import psycopg2.extensions

CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS run_events (
    message_id varchar(255) NOT NULL,
    run_id varchar(255) NOT NULL,
    timestamp timestamp NOT NULL,
    event_body varchar NOT NULL
)
'''

DROP_TABLE_SQL = 'DROP TABLE IF EXISTS run_events'


def get_hostname():
    env_name = 'POSTGRES_TEST_DB_HOST'
    return os.environ.get(env_name, 'localhost')


def conn_string():
    username = 'test'
    password = 'test'
    hostname = get_hostname()
    db_name = 'test'
    return 'postgresql://{username}:{password}@{hostname}:5432/{db_name}'.format(
        username=username, password=password, hostname=hostname, db_name=db_name
    )


def get_conn_with_run_events():
    conn = psycopg2.connect(conn_string())
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    conn.cursor().execute(DROP_TABLE_SQL)
    conn.cursor().execute(CREATE_TABLE_SQL)
    return conn


def test_insert_select():
    conn = get_conn_with_run_events()
    with conn.cursor() as curs:

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
