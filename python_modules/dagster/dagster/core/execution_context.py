import itertools
import json
import uuid

from collections import (
    OrderedDict,
    namedtuple,
)
from contextlib import contextmanager

from dagster import check
from dagster.utils.logging import (
    CompositeLogger,
    INFO,
    define_colored_console_logger,
)

Metric = namedtuple('Metric', 'context_dict metric_name value')


def _kv_message(all_items):
    return ' '.join(
        ['{key}={value}'.format(key=key, value=json.dumps(value)) for key, value in all_items]
    )


class ExecutionContext(object):
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

    def __init__(self, loggers=None, resources=None):
        self._logger = CompositeLogger(loggers=loggers)
        self._context_dict = OrderedDict()
        self.resources = resources

    @staticmethod
    def console_logging(log_level=INFO, resources=None):
        return ExecutionContext(
            loggers=[define_colored_console_logger('dagster', log_level)],
            resources=resources,
        )

    def _log(self, method, orig_message, message_props):
        check.str_param(method, 'method')
        check.str_param(orig_message, 'orig_message')
        check.dict_param(message_props, 'message_props')

        check.invariant(
            'extra' not in message_props,
            'do not allow until explicit support is handled',
        )
        check.invariant(
            'exc_info' not in message_props,
            'do not allow until explicit support is handled',
        )

        check.invariant('orig_message' not in message_props, 'orig_message reserved value')
        check.invariant('message' not in message_props, 'message reserved value')
        check.invariant('log_message_id' not in message_props, 'log_message_id reserved value')

        log_message_id = str(uuid.uuid4())

        synth_props = {'orig_message': orig_message, 'log_message_id': log_message_id}

        # We first generate all props for the purpose of producing the semi-structured
        # log message via _kv_messsage
        all_props = dict(
            itertools.chain(
                synth_props.items(),
                self._context_dict.items(),
                message_props.items(),
            )
        )

        message_with_structured_props = _kv_message(all_props.items())

        getattr(self._logger, method)(message_with_structured_props, extra=all_props)

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

    def get_context_value(self, key):
        check.str_param(key, 'key')
        return self._context_dict[key]

    # FIXME: Actually make this work
    # def exception(self, e):
    #     check.inst_param(e, 'e', Exception)

    #     # this is pretty lame right. should embellish with more data (stack trace?)
    #     return self._log('error', str(e))

    @contextmanager
    def value(self, key, value):
        '''
        Adds a context value to the Execution for a particular scope, using the
        python contextmanager abstraction. This allows the user to add scoped metadata
        just like the framework does (for things such as solid name).

        Examples:

        .. code-block:: python

            with context.value('some_key', 'some_value):
                context.info('msg with some_key context value')

            context.info('msg without some_key context value')

        '''

        check.str_param(key, 'key')
        check.not_none_param(value, 'value')
        with self.values({key: value}):
            yield

    @contextmanager
    def values(self, ddict):
        check.dict_param(ddict, 'ddict')

        for key, value in ddict.items():
            check.invariant(not key in self._context_dict, 'Should not be in context')
            self._context_dict[key] = value

        yield

        for key in ddict.keys():
            self._context_dict.pop(key)
