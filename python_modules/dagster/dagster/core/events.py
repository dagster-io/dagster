from enum import Enum
import json

from dagster import check

from dagster.utils.error import serializable_error_info_from_exc_info, SerializableErrorInfo

from dagster.utils.logging import (
    DEBUG,
    StructuredLoggerHandler,
    StructuredLoggerMessage,
    check_valid_level_param,
    construct_single_handler_logger,
)


class EventType(Enum):
    PIPELINE_START = 'PIPELINE_START'
    PIPELINE_SUCCESS = 'PIPELINE_SUCCESS'
    PIPELINE_FAILURE = 'PIPELINE_FAILURE'

    PIPELINE_PROCESS_START = 'PIPELINE_PROCESS_START'
    PIPELINE_PROCESS_STARTED = 'PIPELINE_PROCESS_STARTED'

    EXECUTION_PLAN_STEP_SUCCESS = 'EXECUTION_PLAN_STEP_SUCCESS'
    EXECUTION_PLAN_STEP_START = 'EXECUTION_PLAN_STEP_START'
    EXECUTION_PLAN_STEP_FAILURE = 'EXECUTION_PLAN_STEP_FAILURE'

    UNCATEGORIZED = 'UNCATEGORIZED'


class ExecutionEvents:
    def __init__(self, context):
        self.context = context

    def pipeline_start(self):
        self.check_pipeline_in_context()
        self.context.info(
            'Beginning execution of pipeline {pipeline}'.format(pipeline=self.pipeline_name()),
            event_type=EventType.PIPELINE_START.value,
        )

    def pipeline_success(self):
        self.check_pipeline_in_context()
        self.context.info(
            'Completing successful execution of pipeline {pipeline}'.format(
                pipeline=self.pipeline_name()
            ),
            event_type=EventType.PIPELINE_SUCCESS.value,
        )

    def pipeline_failure(self):
        self.check_pipeline_in_context()
        self.context.info(
            'Completing failing execution of pipeline {pipeline}'.format(
                pipeline=self.pipeline_name()
            ),
            event_type=EventType.PIPELINE_FAILURE.value,
        )

    def execution_plan_step_start(self, step_key):
        check.str_param(step_key, 'step_key')
        self.context.info(
            'Beginning execution of {step_key}'.format(step_key=step_key),
            event_type=EventType.EXECUTION_PLAN_STEP_START.value,
            step_key=step_key,
        )

    def execution_plan_step_success(self, step_key, millis):
        check.str_param(step_key, 'step_key')
        check.float_param(millis, 'millis')

        self.context.info(
            'Execution of {step_key} succeeded in {millis}'.format(
                step_key=step_key, millis=millis
            ),
            event_type=EventType.EXECUTION_PLAN_STEP_SUCCESS.value,
            millis=millis,
            step_key=step_key,
        )

    def execution_plan_step_failure(self, step_key, exc_info):
        check.str_param(step_key, 'step_key')
        self.context.info(
            'Execution of {step_key} failed'.format(step_key=step_key),
            event_type=EventType.EXECUTION_PLAN_STEP_FAILURE.value,
            step_key=step_key,
            # We really need a better serialization story here
            error_info=json.dumps(serializable_error_info_from_exc_info(exc_info)),
        )

    def pipeline_name(self):
        return self.context.get_context_value('pipeline')

    def check_pipeline_in_context(self):
        check.invariant(
            self.context.has_context_value('pipeline'), 'Must have pipeline context value'
        )


EVENT_TYPE_VALUES = {item.value for item in EventType}


def valid_event_type(event_type):
    check.opt_str_param(event_type, 'event_type')
    return event_type in EVENT_TYPE_VALUES


def construct_event_type(event_type):
    check.opt_str_param(event_type, 'event_type')
    return EventType(event_type) if valid_event_type(event_type) else EventType.UNCATEGORIZED


class EventRecord(object):
    def __init__(self, error_info, message, level, user_message, event_type, run_id, timestamp):
        self._error_info = check.opt_inst_param(error_info, 'error_info', SerializableErrorInfo)
        self._message = check.str_param(message, 'message')
        self._level = check_valid_level_param(level)
        self._user_message = check.str_param(user_message, 'user_message')
        self._event_type = check.inst_param(event_type, 'event_type', EventType)
        self._run_id = check.str_param(run_id, 'run_id')
        self._timestamp = check.float_param(timestamp, 'timestamp')

    @property
    def message(self):
        return self._message

    @property
    def level(self):
        return self._level

    @property
    def user_message(self):
        return self._user_message

    @property
    def event_type(self):
        return self._event_type

    @property
    def run_id(self):
        return self._run_id

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def error_info(self):
        return self._error_info

    def to_dict(self):
        return {
            'run_id': self.run_id,
            'message': self.message,
            'level': self.level,
            'user_message': self.user_message,
            'event_type': str(self.event_type),
            'timestamp': self.timestamp,
            'error_info': self._error_info,
        }


class PipelineEventRecord(EventRecord):
    def __init__(self, pipeline_name, **kwargs):
        super(PipelineEventRecord, self).__init__(**kwargs)
        self._pipeline_name = check.str_param(pipeline_name, 'pipeline_name')

    @property
    def pipeline_name(self):
        return self._pipeline_name

    def to_dict(self):
        orig = super(PipelineEventRecord, self).to_dict()
        orig['pipeline_name'] = self.pipeline_name
        return orig


class ExecutionStepEventRecord(EventRecord):
    def __init__(self, step_key, pipeline_name, solid_name, solid_definition_name, **kwargs):
        super(ExecutionStepEventRecord, self).__init__(**kwargs)
        self._step_key = check.str_param(step_key, 'step_key')
        self._pipeline_name = check.str_param(pipeline_name, 'pipeline_name')
        self._solid_name = check.str_param(solid_name, 'solid_name')
        self._solid_definition_name = check.str_param(
            solid_definition_name, 'solid_definition_name'
        )

    @property
    def step_key(self):
        return self._step_key

    @property
    def pipeline_name(self):
        return self._pipeline_name

    @property
    def solid_name(self):
        return self._solid_name

    @property
    def solid_definition_name(self):
        return self._solid_definition_name

    def to_dict(self):
        orig = super(ExecutionStepEventRecord, self).to_dict()
        orig.update(
            {
                'pipeline_name': self.pipeline_name,
                'step_key': self.step_key,
                'solid_name': self.solid_name,
                'solid_definition_name': self.solid_definition_name,
            }
        )
        return orig


class ExecutionStepSuccessRecord(ExecutionStepEventRecord):
    def __init__(self, millis, **kwargs):
        super(ExecutionStepSuccessRecord, self).__init__(**kwargs)
        self._millis = check.float_param(millis, 'millis')

    @property
    def millis(self):
        return self._millis

    def to_dict(self):
        orig = super(ExecutionStepSuccessRecord, self).to_dict()
        orig['millis'] = self.millis
        return orig


class LogMessageRecord(EventRecord):
    pass


EVENT_CLS_LOOKUP = {
    EventType.EXECUTION_PLAN_STEP_FAILURE: ExecutionStepEventRecord,
    EventType.EXECUTION_PLAN_STEP_START: ExecutionStepEventRecord,
    EventType.EXECUTION_PLAN_STEP_SUCCESS: ExecutionStepSuccessRecord,
    EventType.PIPELINE_FAILURE: PipelineEventRecord,
    EventType.PIPELINE_START: PipelineEventRecord,
    EventType.PIPELINE_SUCCESS: PipelineEventRecord,
    EventType.UNCATEGORIZED: LogMessageRecord,
}

PIPELINE_EVENTS = {EventType.PIPELINE_FAILURE, EventType.PIPELINE_START, EventType.PIPELINE_SUCCESS}


def construct_error_info(logger_message):
    if 'error_info' not in logger_message.meta:
        return None

    raw_error_info = logger_message.meta['error_info']

    message, stack = json.loads(raw_error_info)

    return SerializableErrorInfo(message, stack)


def merge_two_dicts(left, right):
    result = left.copy()
    result.update(right)
    return result


def is_pipeline_event_type(event_type):
    event_cls = EVENT_CLS_LOOKUP[event_type]
    return issubclass(event_cls, PipelineEventRecord)


def logger_to_kwargs(logger_message):
    event_type = construct_event_type(logger_message.meta.get('event_type'))

    base_args = {
        'message': logger_message.message,
        'level': logger_message.level,
        'user_message': logger_message.meta['orig_message'],
        'event_type': event_type,
        'run_id': logger_message.meta['run_id'],
        'timestamp': logger_message.record.created,
    }

    event_cls = EVENT_CLS_LOOKUP[event_type]
    if issubclass(event_cls, PipelineEventRecord):
        return merge_two_dicts(base_args, {'pipeline_name': logger_message.meta['pipeline']})
    elif issubclass(event_cls, ExecutionStepEventRecord):
        step_args = {
            'step_key': logger_message.meta['step_key'],
            'pipeline_name': logger_message.meta['pipeline'],
            'solid_name': logger_message.meta['solid'],
            'solid_definition_name': logger_message.meta['solid_definition'],
        }
        if event_cls == ExecutionStepSuccessRecord:
            step_args['millis'] = logger_message.meta['millis']

        return merge_two_dicts(base_args, step_args)
    else:
        return base_args


def construct_event_record(logger_message):
    check.inst_param(logger_message, 'logger_message', StructuredLoggerMessage)
    event_type = construct_event_type(logger_message.meta.get('event_type'))
    log_record_cls = EVENT_CLS_LOOKUP[event_type]

    kwargs = logger_to_kwargs(logger_message)
    return log_record_cls(error_info=construct_error_info(logger_message), **kwargs)


def construct_event_logger(event_record_callback):
    '''
    Callback receives a stream of event_records
    '''
    check.callable_param(event_record_callback, 'event_record_callback')

    return construct_single_handler_logger(
        'event-logger',
        DEBUG,
        StructuredLoggerHandler(
            lambda logger_message: event_record_callback(construct_event_record(logger_message))
        ),
    )
