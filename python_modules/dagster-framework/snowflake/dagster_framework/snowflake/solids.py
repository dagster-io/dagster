import sys

from contextlib import closing

import pandas as pd
import snowflake.connector

import dagster_pandas as dagster_pd
from dagster import check, OutputDefinition, List, Result, SolidDefinition

from .configs import define_snowflake_config


class SnowflakeSolidDefinition(SolidDefinition):
    '''SnowflakeSolidDefinition wraps execution of a list of Snowflake SQL queries.
    '''

    def __init__(self, name, sql_queries, parameters=None, description=None):
        name = check.str_param(name, 'name')
        sql_queries = check.list_param(sql_queries, 'sql queries', of_type=str)

        description = check.opt_str_param(
            description,
            'description',
            'This solid is a generic representation of a parameterized Snowflake query.',
        )

        description = (
            description
            or 'This solid is a generic representation of a parameterized Snowflake query job.'
        )

        def _define_snowflake_transform_fn(context, _):
            '''Define Snowflake execution.

            This function defines how we'll execute the Snowflake SQL query.
            '''
            system_context = context.get_system_context()

            # Extract parameters from config
            (
                account,
                user,
                password,
                database,
                schema,
                role,
                warehouse,
                autocommit,
                client_prefetch_threads,
                client_session_keep_alive,
                login_timeout,
                network_timeout,
                validate_default_parameters,
                paramstyle,
                timezone,
            ) = [
                context.solid_config.get(k)
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
                    'validate_default_parameters',
                    'paramstyle',
                    'timezone',
                )
            ]

            conn_args = {
                'user': user,
                'password': password,
                'account': account,
                'schema': schema,
                'database': database,
                'role': role,
                'warehouse': warehouse,
                'autocommit': autocommit,
                'client_prefetch_threads': client_prefetch_threads,
                'client_session_keep_alive': client_session_keep_alive,
                'login_timeout': login_timeout,
                'network_timeout': network_timeout,
                'validate_default_parameters': validate_default_parameters,
                'paramstyle': paramstyle,
                'timezone': timezone,
            }

            # We can't pass None values to snowflake.connector.connect() because they will override the
            # default values set within the connector; remove them from the conn_args dict
            conn_args = {k: v for k, v in conn_args.items() if v}

            def _filter_password(conn_args):
                '''Remove password from connection args for logging'''
                return {k: v for k, v in conn_args.items() if k != 'password'}

            system_context.log.info(
                '''Connecting to Snowflake with conn_args %s and
                    [warehouse %s database %s schema %s role %s]'''
                % (str(_filter_password(conn_args)), warehouse, database, schema, role)
            )

            conn = snowflake.connector.connect(**conn_args)

            with closing(conn.cursor()) as cursor:
                results = []
                for query in sql_queries:
                    if sys.version_info[0] < 3:
                        query = query.encode('utf-8')

                    system_context.log.info(
                        'Executing SQL query %s %s'
                        % (query, 'with parameters ' + str(parameters) if parameters else '')
                    )
                    cursor.execute(query, parameters)
                    results.append(pd.DataFrame(cursor.fetchall()))

                if not autocommit:
                    conn.commit()

                system_context.log.info(str(results))
                yield Result(results)

        super(SnowflakeSolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[],
            outputs=[OutputDefinition(List(dagster_pd.DataFrame))],
            transform_fn=_define_snowflake_transform_fn,
            config_field=define_snowflake_config(),
        )
