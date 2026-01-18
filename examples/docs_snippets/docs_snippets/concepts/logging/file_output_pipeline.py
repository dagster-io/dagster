import dagster as dg


@dg.op
def file_log_op(context: dg.OpExecutionContext):
    context.log.info("Hello world!")


@dg.job
def file_log_job():
    file_log_op()
