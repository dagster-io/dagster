# isort: skip_file
import json
import logging

from dagster import Field, logger, job, op

# start_custom_logger_marker_0


@logger(
    {
        "log_level": Field(str, is_required=False, default_value="INFO"),
        "name": Field(str, is_required=False, default_value="dagster"),
    },
    description="A JSON-formatted console logger",
)
def json_console_logger(init_context):
    level = init_context.logger_config["log_level"]
    name = init_context.logger_config["name"]

    klass = logging.getLoggerClass()
    logger_ = klass(name, level=level)

    handler = logging.StreamHandler()

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            return json.dumps(record.__dict__)

    handler.setFormatter(JsonFormatter())
    logger_.addHandler(handler)

    return logger_


@op
def hello_logs(context):
    context.log.info("Hello, world!")


@job(logger_defs={"my_json_logger": json_console_logger})
def demo_job():
    hello_logs()


# end_custom_logger_marker_0

# start_custom_logger_testing


def test_init_json_console_logger():
    logger_ = json_console_logger(None)
    assert logger_.level == 20
    assert logger_.name == "dagster"


# end_custom_logger_testing

# start_custom_logger_testing_context
from dagster import build_init_logger_context


def test_init_json_console_logger_with_context():
    logger_ = json_console_logger(
        build_init_logger_context(logger_config={"name": "my_logger"})
    )
    assert logger_.level == 20
    assert logger_.name == "my_logger"


# end_custom_logger_testing_context
