from dagster import job, op


@op
def uses_config(context):
    for _ in range(context.op_config["iterations"]):
        context.log.info("hello")


@job
def config_example():
    uses_config()
