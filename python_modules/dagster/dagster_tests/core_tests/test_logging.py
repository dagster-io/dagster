import json
import logging
import re

from dagster.core.definitions import SolidHandle
from dagster.core.events import DagsterEvent
from dagster.core.execution_plan.objects import StepFailureData
from dagster.core.log import DAGSTER_DEFAULT_LOGGER, DagsterLog
from dagster.utils.error import SerializableErrorInfo

REGEX_UUID = r'[a-z-0-9]{8}\-[a-z-0-9]{4}\-[a-z-0-9]{4}\-[a-z-0-9]{4}\-[a-z-0-9]{12}'
REGEX_TS = r'\d{4}\-\d{2}\-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}'


def _setup_logger(name):
    class TestLogger(logging.Logger):
        def __init__(self, name):
            super(TestLogger, self).__init__(name)

    logger = TestLogger(name)

    captured_results = []

    def log_fn(msg, *args, **kwargs):  # pylint:disable=unused-argument
        captured_results.append(msg)

    for level in ['debug', 'info', 'warning', 'error', 'critical']:
        setattr(logger, level, log_fn)

    return captured_results, logger


def _regex_match_kv_pair(regex, kv_pairs):
    return any([re.match(regex, kv_pair) for kv_pair in kv_pairs])


def _validate_basic(kv_pairs):
    assert 'orig_message="test"' in kv_pairs
    assert _regex_match_kv_pair(r'log_message_id="{0}"'.format(REGEX_UUID), kv_pairs)
    assert _regex_match_kv_pair(r'log_timestamp="{0}"'.format(REGEX_TS), kv_pairs)


def test_logging_basic():
    captured_results, logger = _setup_logger('test')

    dl = DagsterLog('123', {}, [logger])
    dl.info('test')

    kv_pairs = set(captured_results[0].strip().split())
    _validate_basic(kv_pairs)


def test_multiline_logging_basic():
    captured_results, logger = _setup_logger(DAGSTER_DEFAULT_LOGGER)

    dl = DagsterLog('123', {}, [logger])
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

    captured_results, logger = _setup_logger(DAGSTER_DEFAULT_LOGGER)

    dl = DagsterLog('123', {}, [logger])
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
