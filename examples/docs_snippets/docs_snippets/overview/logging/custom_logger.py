import json
import logging

from dagster import Field, ModeDefinition, execute_pipeline, logger, pipeline, solid


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


@solid
def hello_logs(context):
    context.log.info("Hello, world!")


@pipeline(mode_defs=[ModeDefinition(logger_defs={"my_json_logger": json_console_logger})])
def demo_pipeline():
    hello_logs()


if __name__ == "__main__":
    execute_pipeline(
        demo_pipeline,
        run_config={"loggers": {"my_json_logger": {"config": {"log_level": "INFO"}}}},
    )
