from dagster import check, InputDefinition, Nothing, solid


def snowflake_solid_for_query(sql, parameters):
    check.str_param(sql, 'sql')
    check.dict_param(parameters, 'parameters')

    @solid(
        input_defs=[InputDefinition('start', Nothing)],
        required_resource_keys={'snowflake'},
        metadata={'kind': 'sql', 'sql': sql},
    )
    def snowflake_solid(context):
        context.resources.snowflake.execute_query(sql, parameters)

    return snowflake_solid


def snowflake_load_parquet_solid_for_table(src, table):
    check.str_param(src, 'src')
    check.str_param(table, 'table')

    @solid(input_defs=[InputDefinition('start', Nothing)], required_resource_keys={'snowflake'})
    def snowflake_load_parquet_solid(context):
        '''Snowflake Load.

        This solid encapsulates loading data into Snowflake. Right now it only supports Parquet-
        based loads, but over time we will add support for the remaining Snowflake load formats.
        '''
        context.resources.snowflake.load_table_from_parquet(src, table)

    return snowflake_load_parquet_solid
