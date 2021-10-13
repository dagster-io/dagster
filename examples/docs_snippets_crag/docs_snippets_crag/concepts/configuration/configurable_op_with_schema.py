from dagster import graph, op


@op(config_schema={"iterations": int})
def configurable_with_schema(context):
    for _ in range(context.op_config["iterations"]):
        context.log.info(context.op_config["word"])


@graph
def nests_configurable():
    configurable_with_schema()
