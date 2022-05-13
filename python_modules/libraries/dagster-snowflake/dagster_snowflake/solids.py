from dagster import InputDefinition, Nothing
from dagster import _check as check
from dagster import op, solid


def _core_create_snowflake_command(dagster_decorator, decorator_name, sql, parameters=None):
    check.str_param(sql, "sql")
    check.opt_dict_param(parameters, "parameters")

    @dagster_decorator(
        name=f"snowflake_{decorator_name}",
        input_defs=[InputDefinition("start", Nothing)],
        required_resource_keys={"snowflake"},
        tags={"kind": "sql", "sql": sql},
    )
    def snowflake_fn(context):
        context.resources.snowflake.execute_query(sql=sql, parameters=parameters)

    return snowflake_fn


def snowflake_solid_for_query(sql, parameters=None):
    """This function is a solid factory that constructs solids to execute a snowflake query.

    Note that you can only use `snowflake_solid_for_query` if you know the query you'd like to
    execute at pipeline construction time. If you'd like to execute queries dynamically during
    pipeline execution, you should manually execute those queries in your custom solid using the
    snowflake resource.

    Args:
        sql (str): The sql query that will execute against the provided snowflake resource.
        parameters (dict): The parameters for the sql query.

    Returns:
        SolidDefinition: Returns the constructed solid definition.
    """
    return _core_create_snowflake_command(solid, "solid", sql, parameters)


def snowflake_op_for_query(sql, parameters=None):
    """This function is an op factory that constructs an op to execute a snowflake query.

    Note that you can only use `snowflake_op_for_query` if you know the query you'd like to
    execute at graph construction time. If you'd like to execute queries dynamically during
    job execution, you should manually execute those queries in your custom op using the
    snowflake resource.

    Args:
        sql (str): The sql query that will execute against the provided snowflake resource.
        parameters (dict): The parameters for the sql query.

    Returns:
        OpDefinition: Returns the constructed op definition.
    """
    return _core_create_snowflake_command(op, "op", sql, parameters)
