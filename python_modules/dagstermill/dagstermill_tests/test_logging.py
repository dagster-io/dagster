from dagster import execute_pipeline, ModeDefinition, PipelineDefinition
from dagster.utils.log import construct_single_handler_logger

from dagstermill.examples.repository import define_hello_logging_solid

from .test_logger import LogTestHandler


def test_logging():
    records = []
    critical_records = []

    pipeline_def = PipelineDefinition(
        name='hello_logging_pipeline',
        solid_defs=[define_hello_logging_solid()],
        mode_definitions=[
            ModeDefinition(
                loggers={
                    'test': construct_single_handler_logger(
                        'test', 'debug', LogTestHandler(records)
                    ),
                    'critical': construct_single_handler_logger(
                        'critical', 'critical', LogTestHandler(critical_records)
                    ),
                }
            )
        ],
    )

    execute_pipeline(pipeline_def, {'loggers': {'test': {}, 'critical': {}}})

    messages = [x.dagster_meta['orig_message'] for x in records]

    assert 'Hello, there!' in messages

    critical_messages = [x.dagster_meta['orig_message'] for x in critical_records]

    assert 'Hello, there!' not in critical_messages
