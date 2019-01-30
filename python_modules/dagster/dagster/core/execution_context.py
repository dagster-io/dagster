import itertools
import json
import logging
import uuid

from collections import namedtuple

from dagster import check
from dagster.utils import merge_dicts
from dagster.utils.logging import CompositeLogger, INFO, define_colored_console_logger

from .events import ExecutionEvents
from .types.marshal import PersistenceStrategy


def _kv_message(all_items):
    return ' '.join(
        ['{key}={value}'.format(key=key, value=json.dumps(value)) for key, value in all_items]
    )


DAGSTER_META_KEY = 'dagster_meta'


class ExecutionContext(namedtuple('_ExecutionContext', 'loggers resources tags')):
    def __new__(cls, loggers=None, resources=None, tags=None):
        return super(ExecutionContext, cls).__new__(
            cls,
            loggers=check.opt_list_param(loggers, 'loggers', logging.Logger),
            resources=resources,
            tags=check.opt_dict_param(tags, 'tags'),
        )

    @staticmethod
    def console_logging(log_level=INFO, resources=None):
        return ExecutionContext(
            loggers=[define_colored_console_logger('dagster', log_level)], resources=resources
        )


class RuntimeExecutionContext:
    '''
    A context object flowed through the entire scope of single execution of a
    pipeline of solids. This is used by both framework and user code to log
    messages and metrics. It also maintains a stack of context values so that
    logs, metrics, and any future reporting are reported with a minimal, consistent
    level of context so that developers do not have to repeatedly log well-known
    information (e.g. the name of the solid, the name of the pipeline, etc) when
    logging. Additionally tool author may add their own context values to assist
    reporting.


    Args:
        loggers (List[logging.Logger]):
            The list of loggers that will be invoked whenever the context logging
            functions are called.

        resources(Any):
            An arbitrary user-defined object that can be passed in by a user and
            then access during pipeline execution. This exists so that a user can
            inject their own objects into the context without having to subclass
            ExecutionContext.
    '''

    def __init__(
        self,
        run_id,
        loggers=None,
        resources=None,
        event_callback=None,
        environment_config=None,
        tags=None,
        persistence_policy=None,
    ):

        if loggers is None:
            loggers = [define_colored_console_logger('dagster')]

        self._logger = CompositeLogger(loggers=loggers)
        self.resources = resources
        self._run_id = check.str_param(run_id, 'run_id')
        self._tags = check.opt_dict_param(tags, 'tags')
        self.events = ExecutionEvents(self)

        # For re-construction purposes later on
        self._event_callback = check.opt_callable_param(event_callback, 'event_callback')
        self._environment_config = environment_config
        self.persistence_policy = check.opt_inst_param(
            persistence_policy, 'persistence_policy', PersistenceStrategy
        )

    def for_step(self, step):
        return RuntimeExecutionContext(
            run_id=self.run_id,
            loggers=self._logger.loggers,
            resources=self.resources,
            tags=merge_dicts(step.tags, self._tags),
            environment_config=self.environment_config,
            event_callback=self.event_callback,
            persistence_policy=self.persistence_policy,
        )

    def _log(self, method, orig_message, message_props):
        check.str_param(method, 'method')
        check.str_param(orig_message, 'orig_message')
        check.dict_param(message_props, 'message_props')

        check.invariant(
            'extra' not in message_props, 'do not allow until explicit support is handled'
        )
        check.invariant(
            'exc_info' not in message_props, 'do not allow until explicit support is handled'
        )

        check.invariant('orig_message' not in message_props, 'orig_message reserved value')
        check.invariant('message' not in message_props, 'message reserved value')
        check.invariant('log_message_id' not in message_props, 'log_message_id reserved value')

        log_message_id = str(uuid.uuid4())

        synth_props = {
            'orig_message': orig_message,
            'log_message_id': log_message_id,
            'run_id': self._run_id,
        }

        # We first generate all props for the purpose of producing the semi-structured
        # log message via _kv_messsage
        all_props = dict(
            itertools.chain(synth_props.items(), self._tags.items(), message_props.items())
        )

        message_with_structured_props = _kv_message(all_props.items())

        # So here we use the arbitrary key DAGSTER_META_KEY to store a dictionary of
        # all the meta information that dagster injects into log message.
        # The python logging module, in its infinite wisdom, actually takes all the
        # keys in extra and unconditionally smashes them into the internal dictionary
        # of the logging.LogRecord class. We used a reserved key here to avoid naming
        # collisions with internal variables of the LogRecord class.
        # See __init__.py:363 (makeLogRecord) in the python 3.6 logging module source
        # for the gory details.
        getattr(self._logger, method)(
            message_with_structured_props, extra={DAGSTER_META_KEY: all_props}
        )

    def debug(self, msg, **kwargs):
        '''
        Debug level logging directive. Ends up invoking loggers with DEBUG error level.

        The message will be automatically adorned with context information about the name
        of the pipeline, the name of the solid, and so forth. The use can also add
        context values during execution using the value() method of ExecutionContext.
        Therefore it is generally unnecessary to include this type of information
        (solid name, pipeline name, etc) in the log message unless it is critical
        for the readability/fluency of the log message text itself.

        You can optionally additional context key-value pairs to an individual log
        message using the keyword args to this message

        Args:
            msg (str): The core string
            **kwargs (Dict[str, Any]): Additional context values for only this log message.
        '''
        return self._log('debug', msg, kwargs)

    def info(self, msg, **kwargs):
        '''Log at INFO level

        See debug()'''
        return self._log('info', msg, kwargs)

    def warning(self, msg, **kwargs):
        '''Log at WARNING level

        See debug()'''
        return self._log('warning', msg, kwargs)

    def error(self, msg, **kwargs):
        '''Log at ERROR level

        See debug()'''
        return self._log('error', msg, kwargs)

    def critical(self, msg, **kwargs):
        '''Log at CRITICAL level

        See debug()'''
        return self._log('critical', msg, kwargs)

    def has_tag(self, key):
        check.str_param(key, 'key')
        return key in self._tags

    def get_tag(self, key):
        check.str_param(key, 'key')
        return self._tags[key]

    @property
    def run_id(self):
        return self._run_id

    @property
    def event_callback(self):
        return self._event_callback

    @property
    def has_event_callback(self):
        return self._event_callback is not None

    @property
    def environment_config(self):
        return self._environment_config


class ExecutionMetadata(namedtuple('_ExecutionMetadata', 'run_id tags event_callback loggers')):
    def __new__(cls, run_id=None, tags=None, event_callback=None, loggers=None):
        return super(ExecutionMetadata, cls).__new__(
            cls,
            run_id=check.str_param(run_id, 'run_id') if run_id else str(uuid.uuid4()),
            tags=check.opt_dict_param(tags, 'tags', key_type=str, value_type=str),
            event_callback=check.opt_callable_param(event_callback, 'event_callback'),
            loggers=check.opt_list_param(loggers, 'loggers'),
        )
