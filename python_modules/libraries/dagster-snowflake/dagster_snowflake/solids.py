from dagster import InputDefinition, Nothing, check, solid


def snowflake_solid_for_query(sql, parameters):
    check.str_param(sql, 'sql')
    check.dict_param(parameters, 'parameters')

    @solid(
        input_defs=[InputDefinition('start', Nothing)],
        required_resource_keys={'snowflake'},
        metadata={'kind': 'sql', 'sql': sql},
    )
    def snowflake_solid(context):
        context.resources.snowflake.execute_query(sql, parameters, context.log)

    return snowflake_solid
