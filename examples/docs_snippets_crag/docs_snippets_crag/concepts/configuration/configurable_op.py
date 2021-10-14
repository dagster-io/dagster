from dagster import graph, op


@op
def uses_config(context):
    for _ in range(context.op_config["iterations"]):
        context.log.info("hello")


@graph
def config_example():
    uses_config()
