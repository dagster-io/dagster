from dagster import op, job, repository


# start_builtin_logger_marker_0
@op
def hello_logs(context):
    context.log.info("Hello, world!")


@job
def demo_job():
    hello_logs()


# end_builtin_logger_marker_0


# start_builtin_logger_error_marker_0
@op
def hello_logs_error(context):
    raise Exception("Somebody set up us the bomb")


@job
def demo_job_error():
    hello_logs_error()


# end_builtin_logger_error_marker_0


@repository
def repo():
    return [demo_job, demo_job_error]
