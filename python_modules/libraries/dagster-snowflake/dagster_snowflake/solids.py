import sys

from contextlib import closing

import pandas as pd

from dagster import check, InputDefinition, List, OutputDefinition, Output, SolidDefinition, Nothing

import dagster_pandas as dagster_pd


class SnowflakeSolidDefinition(SolidDefinition):
    '''SnowflakeSolidDefinition wraps execution of a list of Snowflake SQL queries.

    Per the Snowflake docs, executing multiple SQL statements separated by a semicolon in a single
    execute call is not supported, and so here we iterate over a list of SQL queries and call
    connector.execute() on each.

    Attributes:

        name (str): Name of the solid.
        sql_queries (List[str]): A list of SQL queries to execute together. If auto-commit is
            enabled, will commit after each query, otherwise will only commit after the last query
            is completed.
        parameters (Dict[str, str]): Query parameters to bind to the parameterized query (expects
            query to be parameterized). Note that the parameters will be shared across all of the
            queries provided in the sql_queries argument. See the Snowflake docs at
            https://bit.ly/2JZBr6C for how to format these parameters.
        description (str): Description of the solid.

    Examples:
        .. code-block:: python

            s = SnowflakeSolidDefinition(
                name="select_1",
                sql_queries=['select 1;']
            )
    '''

    def __init__(self, name, sql_queries, parameters=None, description=None):
        name = check.str_param(name, 'name')
        sql_queries = check.list_param(sql_queries, 'sql queries', of_type=str)

        description = check.opt_str_param(
            description,
            'description',
            'This solid is a generic representation of a parameterized Snowflake query.',
        )

        def _snowflake_compute_fn(context, _):  # pylint: disable=too-many-locals
            '''Define Snowflake execution.

            This function defines how we'll execute the Snowflake SQL query.
            '''
            with context.resources.snowflake.get_connection(context.log) as conn:
                with closing(conn.cursor()) as cursor:
                    results = []
                    for query in sql_queries:
                        if sys.version_info[0] < 3:
                            query = query.encode('utf-8')

                        context.log.info(
                            'Executing SQL query %s %s'
                            % (query, 'with parameters ' + str(parameters) if parameters else '')
                        )
                        cursor.execute(query, parameters)  # pylint: disable=E1101
                        fetchall_results = cursor.fetchall()  # pylint: disable=E1101
                        results.append(pd.DataFrame(fetchall_results))

                    yield Output(results)

        super(SnowflakeSolidDefinition, self).__init__(
            name=name,
            description=description,
            input_defs=[InputDefinition('start', Nothing)],
            output_defs=[OutputDefinition(List[dagster_pd.DataFrame])],
            compute_fn=_snowflake_compute_fn,
            metadata={'kind': 'sql', 'sql': '\n'.join(sql_queries)},
        )


class SnowflakeLoadSolidDefinition(SnowflakeSolidDefinition):
    '''Snowflake Load.

    This solid encapsulates loading data into Snowflake. Right now it only supports Parquet-based
    loads, but over time we will add support for the remaining Snowflake load formats.
    '''

    def __init__(self, name, src, table, description=None):

        sql_queries = [
            'CREATE OR REPLACE TABLE {table} ( data VARIANT DEFAULT NULL);'.format(table=table),
            'CREATE OR REPLACE FILE FORMAT parquet_format TYPE = \'parquet\';',
            'PUT {src} @%{table};'.format(src=src, table=table),
            'COPY INTO {table} FROM @%{table} FILE_FORMAT = (FORMAT_NAME = \'parquet_format\');'.format(
                table=table
            ),
        ]

        super(SnowflakeLoadSolidDefinition, self).__init__(
            name=name, sql_queries=sql_queries, description=description
        )
