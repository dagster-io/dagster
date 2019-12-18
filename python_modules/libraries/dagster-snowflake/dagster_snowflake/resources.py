import sys
from contextlib import closing, contextmanager

import snowflake.connector

from dagster import check, resource

from .configs import define_snowflake_config


class SnowflakeConnection(object):
    def __init__(self, context):  # pylint: disable=too-many-locals
        # Extract parameters from resource config. Note that we can't pass None values to
        # snowflake.connector.connect() because they will override the default values set within the
        # connector; remove them from the conn_args dict.
        self.conn_args = {
            k: context.resource_config.get(k)
            for k in (
                'account',
                'user',
                'password',
                'database',
                'schema',
                'role',
                'warehouse',
                'autocommit',
                'client_prefetch_threads',
                'client_session_keep_alive',
                'login_timeout',
                'network_timeout',
                'ocsp_response_cache_filename',
                'validate_default_parameters',
                'paramstyle',
                'timezone',
            )
            if context.resource_config.get(k) is not None
        }

        self.autocommit = self.conn_args.get('autocommit', False)
        self.log = context.log_manager

    @contextmanager
    def get_connection(self):
        conn = snowflake.connector.connect(**self.conn_args)
        yield conn
        if not self.autocommit:
            conn.commit()
        conn.close()

    def execute_query(self, sql, parameters=None, fetch_results=False):
        check.str_param(sql, 'sql')
        check.opt_dict_param(parameters, 'parameters')
        check.bool_param(fetch_results, 'fetch_results')

        with self.get_connection() as conn:
            with closing(conn.cursor()) as cursor:
                if sys.version_info[0] < 3:
                    sql = sql.encode('utf-8')

                self.log.info('[snowflake] Executing query: ' + sql)
                cursor.execute(sql, parameters)  # pylint: disable=E1101
                if fetch_results:
                    return cursor.fetchall()  # pylint: disable=E1101

    def execute_queries(self, sql_queries, parameters=None, fetch_results=False):
        check.list_param(sql_queries, 'sql_queries', of_type=str)
        check.opt_dict_param(parameters, 'parameters')
        check.bool_param(fetch_results, 'fetch_results')

        results = []
        with self.get_connection() as conn:
            with closing(conn.cursor()) as cursor:
                for sql in sql_queries:
                    if sys.version_info[0] < 3:
                        sql = sql.encode('utf-8')
                    self.log.info('[snowflake] Executing query: ' + sql)
                    cursor.execute(sql, parameters)  # pylint: disable=E1101
                    if fetch_results:
                        results.append(cursor.fetchall())  # pylint: disable=E1101

        return results if fetch_results else None

    def load_table_from_local_parquet(self, src, table):
        check.str_param(src, 'src')
        check.str_param(table, 'table')

        sql_queries = [
            'CREATE OR REPLACE TABLE {table} ( data VARIANT DEFAULT NULL);'.format(table=table),
            'CREATE OR REPLACE FILE FORMAT parquet_format TYPE = \'parquet\';',
            'PUT {src} @%{table};'.format(src=src, table=table),
            'COPY INTO {table} FROM @%{table} FILE_FORMAT = (FORMAT_NAME = \'parquet_format\');'.format(
                table=table
            ),
        ]

        self.execute_queries(sql_queries)


@resource(
    config=define_snowflake_config(),
    description='This resource is for connecting to the Snowflake data warehouse',
)
def snowflake_resource(context):
    return SnowflakeConnection(context)


def _filter_password(args):
    '''Remove password from connection args for logging'''
    return {k: v for k, v in args.items() if k != 'password'}
