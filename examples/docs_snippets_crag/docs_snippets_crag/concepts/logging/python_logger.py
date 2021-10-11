from dagster import job, op, repository


def scope_logged_job():

    # start_python_logger

    import logging

    my_logger = logging.getLogger("my_logger")

    @op
    def ambitious_op():
        try:
            x = 1 / 0
            return x
        except ZeroDivisionError:
            my_logger.error("Couldn't divide by zero!")

        return None

    # end_python_logger
    @job
    def my_job():
        ambitious_op()

    return my_job


@repository
def python_logging_repo():
    return [scope_logged_job()]
