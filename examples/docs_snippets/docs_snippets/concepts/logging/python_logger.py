from dagster import repository


def scope_logged_pipeline():

    from dagster import pipeline

    # start_python_logger

    import logging
    from dagster import solid

    my_logger = logging.getLogger("my_logger")

    @solid
    def ambitious_solid():

        try:
            x = 1 / 0
            return x
        except ZeroDivisionError:
            my_logger.error("Couldn't divide by zero!")

        return None

    # end_python_logger
    @pipeline
    def my_pipeline():
        ambitious_solid()

    return my_pipeline


@repository
def python_logging_repo():
    return [scope_logged_pipeline()]
