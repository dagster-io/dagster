from dagster import Nothing
from dagster import _check as check
from dagster import op
from dagster._legacy import InputDefinition


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

    check.str_param(sql, "sql")
    check.opt_dict_param(parameters, "parameters")

    @op(
        name="snowflake_op",
        input_defs=[InputDefinition("start", Nothing)],
        required_resource_keys={"snowflake"},
        tags={"kind": "sql", "sql": sql},
    )
    def snowflake_fn(context):
        context.resources.snowflake.execute_query(sql=sql, parameters=parameters)

    return snowflake_fn
