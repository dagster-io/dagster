import psycopg2


def get_conn(conn_string):
    conn = psycopg2.connect(conn_string)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def get_conn_string(username, password, hostname, db_name):
    return 'postgresql://{username}:{password}@{hostname}:5432/{db_name}'.format(
        username=username, password=password, hostname=hostname, db_name=db_name
    )
