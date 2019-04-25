import json
import logging
import re

from contextlib import contextmanager

from dagster import check
from dagster.core.definitions import SolidHandle
from dagster.core.events import DagsterEvent
from dagster.core.execution_plan.objects import StepFailureData
from dagster.core.log import DagsterLogManager, DAGSTER_DEFAULT_LOGGER
from dagster.utils.error import SerializableErrorInfo

REGEX_UUID = r'[a-z-0-9]{8}\-[a-z-0-9]{4}\-[a-z-0-9]{4}\-[a-z-0-9]{4}\-[a-z-0-9]{12}'
REGEX_TS = r'\d{4}\-\d{2}\-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}'


@contextmanager
def _setup_logger(name, log_levels=None, register_levels=True):
    log_levels = check.opt_dict_param(log_levels, 'log_levels')

    def add_log_level(value, name):
        logging.addLevelName(value, name)
        setattr(logging, name, value)

    def rm_log_level(value, name):
        # pylint: disable=protected-access
        if hasattr(logging, '_nameToLevel'):
            if name in logging._nameToLevel:
                del logging._nameToLevel[name]

        if hasattr(logging, '_levelToName'):
            if value in logging._levelToName:
                del logging._levelToName[value]

        if hasattr(logging, '_levelNames'):
            # pylint: disable=no-member
            if name in logging._levelNames:
                del logging._levelNames[name]
            if value in logging._levelNames and logging._levelNames[value] == name:
                del logging._levelNames[value]

    if register_levels:
        for level_name, value in log_levels.items():
            add_log_level(value, level_name)

    class TestLogger(logging.Logger):
        def __init__(self, name):
            super(TestLogger, self).__init__(name)

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

    if register_levels:
        for level_name, value in log_levels.items():
            rm_log_level(value, level_name)


def _regex_match_kv_pair(regex, kv_pairs):
    return any([re.match(regex, kv_pair) for kv_pair in kv_pairs])


def _validate_basic(kv_pairs):
    assert 'orig_message="test"' in kv_pairs
    assert _regex_match_kv_pair(r'log_message_id="{0}"'.format(REGEX_UUID), kv_pairs)
    assert _regex_match_kv_pair(r'log_timestamp="{0}"'.format(REGEX_TS), kv_pairs)


def test_logging_basic():
    with _setup_logger('test') as (captured_results, logger):

        dl = DagsterLogManager('123', {}, [logger])
        dl.debug('test')
        dl.info('test')
        dl.warning('test')
        dl.error('test')
        dl.critical('test')

        for captured_result in captured_results:
            kv_pairs = set(captured_result.strip().split())
            _validate_basic(kv_pairs)


def test_logging_custom_log_levels():
    with _setup_logger('test', {'FOO': 3}) as (captured_results, logger):

        dl = DagsterLogManager('123', {}, [logger])
        dl.foo('test')

        kv_pairs = set(captured_results[0].strip().split())
        _validate_basic(kv_pairs)


def test_logging_integer_log_levels():
    with _setup_logger('test', {'FOO': 3}) as (captured_results, logger):

        dl = DagsterLogManager('123', {}, [logger])
        dl.log(3, 'test')
        dl.log(51, 'test')

        kv_pairs = set(captured_results[0].strip().split())
        _validate_basic(kv_pairs)


def test_logging_bad_custom_log_levels():
    with _setup_logger('test') as (captured_results, logger):

        dl = DagsterLogManager('123', {}, [logger])
        dl.foo('test')

        kv_pairs = set(captured_results[0].strip().split())

        assert _regex_match_kv_pair(r'log_message_id="{0}"'.format(REGEX_UUID), kv_pairs)
        assert _regex_match_kv_pair(r'log_timestamp="{0}"'.format(REGEX_TS), kv_pairs)

        assert (
            'orig_message="Unexpected log level: User code attempted to log at level \'foo\', but '
            'that level has not been registered with the Python logging library. Original message: '
            '\'test\''
        ) in captured_results[0]


def test_logging_unregistered_custom_log_levels():
    with _setup_logger('test', {'FOO': 3}, register_levels=False) as (captured_results, logger):

        dl = DagsterLogManager('123', {}, [logger])
        dl.foo('test')

        kv_pairs = set(captured_results[0].strip().split())

        assert _regex_match_kv_pair(r'log_message_id="{0}"'.format(REGEX_UUID), kv_pairs)
        assert _regex_match_kv_pair(r'log_timestamp="{0}"'.format(REGEX_TS), kv_pairs)

        assert (
            'orig_message="Unexpected log level: User code attempted to log at level \'foo\', but '
            'that level has not been registered with the Python logging library. Original message: '
            '\'test\''
        ) in captured_results[0]


def test_multiline_logging_basic():
    with _setup_logger(DAGSTER_DEFAULT_LOGGER) as (captured_results, logger):

        dl = DagsterLogManager('123', {}, [logger])
        dl.info('test')

        kv_pairs = captured_results[0].replace(' ', '').split('\n')[1:]
        _validate_basic(kv_pairs)


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
            solid_handle=SolidHandle('start', 'emit_num'),
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
                        '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/execution_plan/simple_engine.py", line 365, in _iterate_step_outputs_within_boundary\n    for step_output in gen:\n',
                        '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/execution_plan/materialization_thunk.py", line 28, in _fn\n    runtime_type.output_schema.materialize_runtime_value(config_spec, runtime_value)\n',
                        '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/types/config_schema.py", line 93, in materialize_runtime_value\n    return func(config_value, runtime_value)\n',
                        '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/types/config_schema.py", line 110, in _selector\n    return func(selector_key, selector_value, runtime_value)\n',
                        '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/types/builtin_config_schemas.py", line 59, in _builtin_output_schema\n    with open(json_file_path, \'w\') as ff:\n',
                    ],
                    cls_name='FileNotFoundError',
                )
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
                    '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/execution_plan/simple_engine.py", line 365, in _iterate_step_outputs_within_boundary\n    for step_output in gen:\n',
                    '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/execution_plan/materialization_thunk.py", line 28, in _fn\n    runtime_type.output_schema.materialize_runtime_value(config_spec, runtime_value)\n',
                    '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/types/config_schema.py", line 93, in materialize_runtime_value\n    return func(config_value, runtime_value)\n',
                    '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/types/config_schema.py", line 110, in _selector\n    return func(selector_key, selector_value, runtime_value)\n',
                    '  File "/Users/nate/src/dagster/python_modules/dagster/dagster/core/types/builtin_config_schemas.py", line 59, in _builtin_output_schema\n    with open(json_file_path, \'w\') as ff:\n',
                ],
                'FileNotFoundError',
            ]
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
