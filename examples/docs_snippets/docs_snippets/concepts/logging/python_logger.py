from dagster import repository


def scope_logged_job():

    from dagster import graph

    # start_python_logger

    import logging
    from dagster import op

    @op
    def ambitious_op():
        my_logger = logging.getLogger("my_logger")
        try:
            x = 1 / 0
            return x
        except ZeroDivisionError:
            my_logger.error("Couldn't divide by zero!")

        return None

    # end_python_logger
    @graph
    def thing():
        ambitious_op()

    return thing


def scope_logged_job2():

    from dagster import graph

    # start_get_logger

    from dagster import get_dagster_logger, op

    @op
    def ambitious_op():
        my_logger = get_dagster_logger()
        try:
            x = 1 / 0
            return x
        except ZeroDivisionError:
            my_logger.error("Couldn't divide by zero!")

        return None

    # end_get_logger
    @graph
    def thing():
        ambitious_op()

    return thing


@repository
def python_logging_repo():
    return [scope_logged_job(), scope_logged_job2()]
