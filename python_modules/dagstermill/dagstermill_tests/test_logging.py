import json
import logging
import tempfile

from dagster import (
    Dict,
    execute_pipeline,
    Field,
    logger,
    ModeDefinition,
    PipelineDefinition,
    seven,
    String,
)
from dagster.cli.load_handle import handle_for_pipeline_cli_args
from dagster.utils import script_relative_path

from dagstermill.examples.repository import define_hello_logging_solid


class LogTestFileHandler(logging.Handler):
    def __init__(self, file_path):
        self.file_path = file_path
        super(LogTestFileHandler, self).__init__()

    def emit(self, record):
        with open(self.file_path, 'a') as fd:
            fd.write(seven.json.dumps(record.__dict__) + '\n')


@logger(
    config_field=Field(
        Dict({'name': Field(String), 'log_level': Field(String), 'file_path': Field(String)})
    )
)
def test_file_logger(init_context):
    klass = logging.getLoggerClass()
    logger_ = klass(
        init_context.logger_config['name'], level=init_context.logger_config['log_level']
    )
    handler = LogTestFileHandler(init_context.logger_config['file_path'])
    logger_.addHandler(handler)
    handler.setLevel(init_context.logger_config['log_level'])
    return logger_


def define_hello_logging_pipeline():
    return PipelineDefinition(
        name='hello_logging_pipeline',
        solid_defs=[define_hello_logging_solid()],
        mode_defs=[
            ModeDefinition(logger_defs={'test': test_file_logger, 'critical': test_file_logger})
        ],
    )


def test_logging():

    handle = handle_for_pipeline_cli_args(
        {
            'python_file': script_relative_path('./test_logging.py'),
            'fn_name': 'define_hello_logging_pipeline',
        }
    )

    pipeline_def = handle.build_pipeline_definition()

    with tempfile.NamedTemporaryFile() as test_file:
        with tempfile.NamedTemporaryFile() as critical_file:
            execute_pipeline(
                pipeline_def,
                {
                    'loggers': {
                        'test': {
                            'config': {
                                'name': 'test',
                                'file_path': test_file.name,
                                'log_level': 'DEBUG',
                            }
                        },
                        'critical': {
                            'config': {
                                'name': 'critical',
                                'file_path': critical_file.name,
                                'log_level': 'CRITICAL',
                            }
                        },
                    }
                },
            )

            test_file.seek(0)
            critical_file.seek(0)

            records = [
                json.loads(line)
                for line in test_file.read().decode('utf-8').strip('\n').split('\n')
                if line
            ]
            critical_records = [
                json.loads(line)
                for line in critical_file.read().decode('utf-8').strip('\n').split('\n')
                if line
            ]

    messages = [x['dagster_meta']['orig_message'] for x in records]

    assert 'Hello, there!' in messages

    critical_messages = [x['dagster_meta']['orig_message'] for x in critical_records]

    assert 'Hello, there!' not in critical_messages
