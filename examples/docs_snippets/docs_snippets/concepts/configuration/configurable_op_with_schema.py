from dagster import job, op


@op(config_schema={"iterations": int})
def configurable_with_schema(context):
    for _ in range(context.op_config["iterations"]):
        context.log.info(context.op_config["word"])


@job
def nests_configurable():
    configurable_with_schema()
