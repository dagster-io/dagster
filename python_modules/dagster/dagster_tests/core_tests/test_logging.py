import json
import logging
import re

from contextlib import contextmanager

import pytest

from dagster import check, execute_solid, pipeline, solid, ModeDefinition
from dagster.core.definitions import SolidHandle
from dagster.core.events import DagsterEvent
from dagster.core.execution.plan.objects import StepFailureData
from dagster.core.execution.context.logger import InitLoggerContext
from dagster.core.log_manager import DagsterLogManager
from dagster.loggers import colored_console_logger, json_console_logger
from dagster.utils.error import SerializableErrorInfo

REGEX_UUID = r'[a-z-0-9]{8}\-[a-z-0-9]{4}\-[a-z-0-9]{4}\-[a-z-0-9]{4}\-[a-z-0-9]{12}'
REGEX_TS = r'\d{4}\-\d{2}\-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}'

DAGSTER_DEFAULT_LOGGER = 'dagster'


@contextmanager
def _setup_logger(name, log_levels=None):
    '''Test helper that creates a new logger.

    Args:
        name (str): The name of the logger.
        log_levels (Optional[Dict[str, int]]): Any non-standard log levels to expose on the logger
            (e.g., logger.success)
    '''
    log_levels = check.opt_dict_param(log_levels, 'log_levels')

    class TestLogger(logging.Logger):  # py27 compat
        pass

    logger = TestLogger(name)

    captured_results = []

    def log_fn(msg, *args, **kwargs):  # pylint:disable=unused-argument
        captured_results.append(msg)

    def int_log_fn(lvl, msg, *args, **kwargs):  # pylint:disable=unused-argument
        captured_results.append(msg)

    for level in ['debug', 'info', 'warning', 'error', 'critical'] + list(
        [x.lower() for x in log_levels.keys()]
    ):
        setattr(logger, level, log_fn)
        setattr(logger, 'log', int_log_fn)

    yield (captured_results, logger)


def _regex_match_kv_pair(regex, kv_pairs):
    return any([re.match(regex, kv_pair) for kv_pair in kv_pairs])


def _validate_basic(kv_pairs):
    assert 'orig_message="test"' in kv_pairs
    assert _regex_match_kv_pair(r'log_message_id="{0}"'.format(REGEX_UUID), kv_pairs)
    assert _regex_match_kv_pair(r'log_timestamp="{0}"'.format(REGEX_TS), kv_pairs)


def test_logging_no_loggers_registered():
    dl = DagsterLogManager('none', {}, [])
    dl.debug('test')
    dl.info('test')
    dl.warning('test')
    dl.error('test')
    dl.critical('test')


def test_logging_basic():
    with _setup_logger('test') as (captured_results, logger):

        dl = DagsterLogManager('123', {}, [logger])
        dl.debug('test')
        dl.info('test')
        dl.warning('test')
        dl.error('test')
        dl.critical('test')

        kv_pairs = captured_results[0].replace(' ', '').split('\n')[1:]
        _validate_basic(kv_pairs)


def test_logging_custom_log_levels():
    with _setup_logger('test', {'FOO': 3}) as (_captured_results, logger):

        dl = DagsterLogManager('123', {}, [logger])
        with pytest.raises(AttributeError):
            dl.foo('test')  # pylint: disable=no-member


def test_logging_integer_log_levels():
    with _setup_logger('test', {'FOO': 3}) as (_captured_results, logger):

        dl = DagsterLogManager('123', {}, [logger])
        with pytest.raises(AttributeError):
            dl.log(3, 'test')  # pylint: disable=no-member


def test_logging_bad_custom_log_levels():
    with _setup_logger('test') as (_, logger):

        dl = DagsterLogManager('123', {}, [logger])
        with pytest.raises(check.CheckError):
            dl._log('test', 'foobar', {})  # pylint: disable=protected-access


def test_multiline_logging_complex():
    msg = 'DagsterEventType.STEP_FAILURE for step start.materialization.output.result.0'
    kwargs = {
        'pipeline': 'example',
        'pipeline_name': 'example',
        'step_key': 'start.materialization.output.result.0',
        'solid': 'start',
        'solid_definition': 'emit_num',
        'dagster_event': DagsterEvent(
            event_type_value='STEP_FAILURE',
            pipeline_name='error_monster',
            step_key='start.materialization.output.result.0',
            solid_handle=SolidHandle('start', 'emit_num', None),
            step_kind_value='MATERIALIZATION_THUNK',
            logging_tags={
                'pipeline': 'error_monster',
                'step_key': 'start.materialization.output.result.0',
                'solid': 'start',
                'solid_definition': 'emit_num',
            },
            event_specific_data=StepFailureData(
                error=SerializableErrorInfo(
                    message="FileNotFoundError: [Errno 2] No such file or directory: '/path/to/file'\n",
                    stack=[
                        '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/errors.py", line 186, in user_code_error_boundary\n    yield\n',
                        '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/execution_plan/simple_engine.py", line 365, in _event_sequence_for_step_compute_fn\n    for step_output in gen:\n',
                        '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/execution_plan/materialization_thunk.py", line 28, in _fn\n    runtime_type.output_materialization_config.materialize_runtime_value(config_spec, runtime_value)\n',
                        '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/types/config_schema.py", line 93, in materialize_runtime_value\n    return func(config_value, runtime_value)\n',
                        '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/types/config_schema.py", line 110, in _selector\n    return func(selector_key, selector_value, runtime_value)\n',
                        '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/types/builtin_config_schemas.py", line 59, in _builtin_output_schema\n    with open(json_file_path, \'w\') as ff:\n',
                    ],
                    cls_name='FileNotFoundError',
                ),
                user_failure_data=None,
            ),
        ),
    }

    with _setup_logger(DAGSTER_DEFAULT_LOGGER) as (captured_results, logger):

        dl = DagsterLogManager('123', {}, [logger])
        dl.info(msg, **kwargs)

        kv_pairs = set(captured_results[0].split('\n')[1:])

    expected_pairs = [
        '        orig_message = "DagsterEventType.STEP_FAILURE for step start.materialization.output.result.0"',
        '              run_id = "123"',
        '            pipeline = "example"',
        '    solid_definition = "emit_num"',
        '       pipeline_name = "example"',
        '               solid = "start"',
        '            step_key = "start.materialization.output.result.0"',
    ]
    for e in expected_pairs:
        assert e in kv_pairs

    assert _regex_match_kv_pair(r'      log_message_id = "{0}"'.format(REGEX_UUID), kv_pairs)
    assert _regex_match_kv_pair(r'       log_timestamp = "{0}"'.format(REGEX_TS), kv_pairs)

    expected_dagster_event = {
        'event_specific_data': [
            [
                "FileNotFoundError: [Errno 2] No such file or directory: '/path/to/file'\n",
                [
                    '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/errors.py", line 186, in user_code_error_boundary\n    yield\n',
                    '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/execution_plan/simple_engine.py", line 365, in _event_sequence_for_step_compute_fn\n    for step_output in gen:\n',
                    '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/execution_plan/materialization_thunk.py", line 28, in _fn\n    runtime_type.output_materialization_config.materialize_runtime_value(config_spec, runtime_value)\n',
                    '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/types/config_schema.py", line 93, in materialize_runtime_value\n    return func(config_value, runtime_value)\n',
                    '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/types/config_schema.py", line 110, in _selector\n    return func(selector_key, selector_value, runtime_value)\n',
                    '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/types/builtin_config_schemas.py", line 59, in _builtin_output_schema\n    with open(json_file_path, \'w\') as ff:\n',
                ],
                'FileNotFoundError',
            ],
            None,  # user_failure_data
        ],
        'event_type_value': 'STEP_FAILURE',
        'pipeline_name': 'error_monster',
        'solid_handle': ['start', 'emit_num', None],
        'step_key': 'start.materialization.output.result.0',
        'step_kind_value': 'MATERIALIZATION_THUNK',
        'logging_tags': {
            'pipeline': 'error_monster',
            'solid': 'start',
            'solid_definition': 'emit_num',
            'step_key': 'start.materialization.output.result.0',
        },
    }
    dagster_event = json.loads(
        [pair for pair in kv_pairs if 'dagster_event' in pair][0].strip('       dagster_event = ')
    )
    assert dagster_event == expected_dagster_event


def test_default_context_logging():
    called = {}

    @solid(input_defs=[], output_defs=[])
    def default_context_solid(context):
        called['yes'] = True
        for logger in context.log.loggers:
            assert logger.level == logging.INFO

    execute_solid(default_context_solid)

    assert called['yes']


def test_colored_console_logger_with_integer_log_level():
    @pipeline
    def pipe():
        pass

    colored_console_logger.logger_fn(
        InitLoggerContext({'name': 'dagster', 'log_level': 4}, pipe, colored_console_logger, '')
    )


def test_json_console_logger(capsys):
    @solid
    def hello_world(context):
        context.log.info('Hello, world!')

    execute_solid(
        hello_world,
        mode_def=ModeDefinition(logger_defs={'json': json_console_logger}),
        environment_dict={'loggers': {'json': {'config': {}}}},
    )

    captured = capsys.readouterr()

    found_msg = False
    for line in captured.err.split('\n'):
        if line:
            parsed = json.loads(line)
            if parsed['dagster_meta']['orig_message'] == 'Hello, world!':
                found_msg = True

    assert found_msg
