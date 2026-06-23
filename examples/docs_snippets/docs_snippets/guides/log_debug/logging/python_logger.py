import dagster as dg


def scope_logged_job():
    # start_python_logger
    import logging

    @dg.op
    def ambitious_op():
        my_logger = logging.getLogger("my_logger")
        try:
            x = 1 / 0
            return x
        except ZeroDivisionError:
            my_logger.error("Couldn't divide by zero!")

        return None

    # end_python_logger
    @dg.graph
    def thing_one():
        ambitious_op()

    return thing_one


def scope_logged_job2():
    # start_get_logger

    @dg.op
    def ambitious_op():
        my_logger = dg.get_dagster_logger()
        try:
            x = 1 / 0
            return x
        except ZeroDivisionError:
            my_logger.error("Couldn't divide by zero!")

        return None

    # end_get_logger
    @dg.graph
    def thing_two():
        ambitious_op()

    return thing_two


@dg.repository
def python_logging_repo():
    return [scope_logged_job(), scope_logged_job2()]
