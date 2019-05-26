from contextlib import contextmanager

import snowflake.connector

from dagster import resource

from .configs import define_snowflake_config


class SnowflakeConnection:
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

    @contextmanager
    def get_connection(self, log):
        log.info(
            '''Connecting to Snowflake with conn_args %s ''' % str(_filter_password(self.conn_args))
        )

        conn = snowflake.connector.connect(**self.conn_args)
        yield conn
        if not self.autocommit:
            conn.commit()
        conn.close()


@resource(
    config_field=define_snowflake_config(),
    description='This resource is for connecting to the Snowflake data warehouse',
)
def snowflake_resource(context):
    return SnowflakeConnection(context)


def _filter_password(args):
    '''Remove password from connection args for logging'''
    return {k: v for k, v in args.items() if k != 'password'}
