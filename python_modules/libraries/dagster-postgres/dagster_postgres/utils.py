import time

import psycopg2


def get_conn(conn_string):
    conn = psycopg2.connect(conn_string)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def get_conn_string(username, password, hostname, db_name, port='5432'):
    return 'postgresql://{username}:{password}@{hostname}:{port}/{db_name}'.format(
        username=username, password=password, hostname=hostname, db_name=db_name, port=port
    )


def wait_for_connection(conn_string):
    retry_limit = 20

    while retry_limit:
        try:
            psycopg2.connect(conn_string)
            return True
        except psycopg2.OperationalError:
            pass

        time.sleep(0.2)
        retry_limit -= 1

    assert retry_limit == 0
    raise Exception('too many retries for db at {conn_string}'.format(conn_string=conn_string))
