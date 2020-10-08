from dagster import InputDefinition, Nothing, check, solid


def snowflake_solid_for_query(sql, parameters=None):
    check.str_param(sql, "sql")
    check.opt_dict_param(parameters, "parameters")

    @solid(
        input_defs=[InputDefinition("start", Nothing)],
        required_resource_keys={"snowflake"},
        tags={"kind": "sql", "sql": sql},
    )
    def snowflake_solid(context):
        context.resources.snowflake.execute_query(sql=sql, parameters=parameters)

    return snowflake_solid
