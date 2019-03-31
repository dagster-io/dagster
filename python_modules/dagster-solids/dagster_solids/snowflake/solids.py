import sys

from contextlib import closing

import snowflake.connector

from dagster import check, InputDefinition, OutputDefinition, Result, String, SolidDefinition

from .configs import define_snowflake_config


def define_snowflake_transform_fn(context, inputs):
    '''Define Snowflake execution.

    This function defines how we'll execute the Snowflake SQL query.
    '''
    system_context = context.get_system_context()

    # Extract parameters from config
    (
        sql,
        parameters,
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
            'sql',
            'parameters',
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

    system_context.log.info(
        '''Connecting to Snowflake with conn_args %s and
            [warehouse %s database %s schema %s role %s]'''
        % (str(conn_args), warehouse, database, schema, role)
    )

    conn = snowflake.connector.connect(**conn_args)

    with closing(conn.cursor()) as cursor:

        if sys.version_info[0] < 3:
            sql = sql.encode('utf-8')

        system_context.log.info(
            'Executing SQL query %s %s'
            % (sql, 'with parameters ' + str(parameters) if parameters else '')
        )
        cursor.execute(sql, parameters)

        system_context.log.info(str(cursor.fetchall()))

        if not autocommit:
            conn.commit()

        for output_def in system_context.solid_def.output_defs:
            yield Result('ok!', output_def.name)


class SnowflakeSolidDefinition(SolidDefinition):
    def __init__(self, name, description=None):
        name = check.str_param(name, 'name')
        description = check.opt_str_param(
            description,
            'description',
            'This solid is a generic representation of a parameterized Snowflake query.',
        )
        outputs = [
            OutputDefinition(
                name='result', dagster_type=String, description='The Snowflake job results'
            )
        ]

        description = (
            description
            or 'This solid is a generic representation of a parameterized Snowflake query job.'
        )
        super(SnowflakeSolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[],
            outputs=outputs,
            transform_fn=define_snowflake_transform_fn,
            config_field=define_snowflake_config(),
        )
