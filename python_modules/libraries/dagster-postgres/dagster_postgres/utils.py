import time

import psycopg2

from dagster.config import Field, Selector
from dagster.core.instance.source_types import StringSource
from dagster.seven import quote_plus as urlquote


def get_conn(conn_string):
    conn = psycopg2.connect(conn_string)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def pg_config():
    return Selector(
        {
            'postgres_url': str,
            'postgres_db': {
                'username': str,
                'password': StringSource,
                'hostname': str,
                'db_name': str,
                'port': Field(int, is_required=False, default_value=5432),
            },
        }
    )


def pg_url_from_config(config_value):
    if config_value.get('postgres_url'):
        return config_value['postgres_url']

    return get_conn_string(**config_value['postgres_db'])


def get_conn_string(username, password, hostname, db_name, port='5432'):
    return 'postgresql://{username}:{password}@{hostname}:{port}/{db_name}'.format(
        username=username,
        password=urlquote(password),
        hostname=hostname,
        db_name=db_name,
        port=port,
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
