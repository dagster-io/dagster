import itertools
import copy
from collections import (
    OrderedDict,
    namedtuple,
)
from contextlib import contextmanager
import uuid

from dagster import check
from dagster.utils.logging import CompositeLogger

Metric = namedtuple('Metric', 'context_dict metric_name value')


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


    resources is an arbitrary user-defined object that can be passed in
    by a user and then access during pipeline execution. This exists so that
    a user does not have to subclass ExecutionContext
    '''

    def __init__(self, loggers=None, resources=None):
        self._logger = CompositeLogger(loggers=loggers)
        self._context_dict = OrderedDict()
        self._metrics = []
        self.resources = resources

    def _maybe_quote(self, val):
        str_val = str(val)
        if ' ' in str_val:
            return '"{val}"'.format(val=str_val)
        return str_val

    def _kv_message(self, extra=None):
        extra = check.opt_dict_param(extra, 'extra')
        return ' '.join(
            [
                '{key}={value}'.format(key=key, value=self._maybe_quote(value))
                for key, value in itertools.chain(self._context_dict.items(), extra.items())
            ]
        )

    def _log(self, method, msg, **kwargs):
        check.str_param(method, 'method')
        check.str_param(msg, 'msg')

        check.invariant('extra' not in kwargs, 'do not allow until explicit support is handled')
        check.invariant('exc_info' not in kwargs, 'do not allow until explicit support is handled')

        check.invariant('log_message' not in kwargs, 'log_message_id reserved value')
        check.invariant('log_message_id' not in kwargs, 'log_message_id reserved value')

        full_message = 'message="{message}" {kv_message}'.format(
            message=msg, kv_message=self._kv_message(kwargs)
        )

        log_props = copy.copy(self._context_dict)
        log_props['log_message'] = msg

        log_props['log_message'] = msg
        log_props['log_message_id'] = str(uuid.uuid4())

        extra = {}
        extra.update(log_props)
        extra.update(kwargs)

        getattr(self._logger, method)(full_message, extra=extra)

    def debug(self, msg, **kwargs):
        return self._log('debug', msg, **kwargs)

    def info(self, msg, **kwargs):
        return self._log('info', msg, **kwargs)

    def warning(self, msg, **kwargs):
        return self._log('warning', msg, **kwargs)

    def error(self, msg, **kwargs):
        return self._log('error', msg, **kwargs)

    def critical(self, msg, **kwargs):
        return self._log('critical', msg, **kwargs)

    # FIXME: Actually make this work
    # def exception(self, e):
    #     check.inst_param(e, 'e', Exception)

    #     # this is pretty lame right. should embellish with more data (stack trace?)
    #     return self._log('error', str(e))

    @contextmanager
    def value(self, key, value):
        check.str_param(key, 'key')
        check.not_none_param(value, 'value')

        check.invariant(not key in self._context_dict, 'Should not be in context')

        self._context_dict[key] = value

        yield

        self._context_dict.pop(key)

    def metric(self, metric_name, value):
        check.str_param(metric_name, 'metric_name')
        check.not_none_param(value, 'value')

        keys = list(self._context_dict.keys())
        keys.append(metric_name)
        if isinstance(value, float):
            format_string = 'metric:{metric_name}={value:.3f} {kv_message}'
        else:
            format_string = 'metric:{metric_name}={value} {kv_message}'

        self._logger.info(
            format_string.format(
                metric_name=metric_name, value=value, kv_message=self._kv_message()
            ),
            extra=self._context_dict
        )

        self._metrics.append(
            Metric(
                context_dict=copy.copy(self._context_dict), metric_name=metric_name, value=value
            )
        )

    def _dict_covers(self, needle_dict, haystack_dict):
        for key, value in needle_dict.items():
            if not key in haystack_dict:
                return False
            if value != haystack_dict[key]:
                return False
        return True

    def metrics_covering_context(self, needle_dict):
        for metric in self._metrics:
            if self._dict_covers(needle_dict, metric.context_dict):
                yield metric

    def metrics_matching_context(self, needle_dict):
        for metric in self._metrics:
            if needle_dict == metric.context_dict:
                yield metric
