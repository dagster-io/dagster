from dagster import SourceHashVersionStrategy, job, op


@op(config_schema=str)
def emit_op(context):
    return context.op_config


@op(config_schema=str)
def consume_op(context, inp):
    return inp + context.op_config


@job(version_strategy=SourceHashVersionStrategy())
def memoization_job():
    consume_op(emit_op())
    consume_op(emit_op())
