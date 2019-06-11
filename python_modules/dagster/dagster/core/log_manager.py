import datetime
import itertools
import logging
import uuid

from collections import OrderedDict, namedtuple

from dagster import check, seven
from dagster.utils import frozendict

DAGSTER_META_KEY = 'dagster_meta'


PYTHON_LOGGING_LEVELS_MAPPING = frozendict(
    OrderedDict({'CRITICAL': 50, 'ERROR': 40, 'WARNING': 30, 'INFO': 20, 'DEBUG': 10})
)

PYTHON_LOGGING_LEVELS_ALIASES = frozendict(OrderedDict({'FATAL': 'CRITICAL', 'WARN': 'WARNING'}))

PYTHON_LOGGING_LEVELS_NAMES = frozenset(
    [
        level_name.lower()
        for level_name in sorted(
            list(PYTHON_LOGGING_LEVELS_MAPPING.keys()) + list(PYTHON_LOGGING_LEVELS_ALIASES.keys())
        )
    ]
)


def _dump_value(value):
    # dump namedtuples as objects instead of arrays
    if isinstance(value, tuple) and hasattr(value, '_asdict'):
        return seven.json.dumps(value._asdict())

    return seven.json.dumps(value)


def _kv_message(all_items):
    sep = '\n'
    format_str = '{key:>20} = {value}'
    return sep + sep.join(
        [format_str.format(key=key, value=_dump_value(value)) for key, value in all_items]
    )


def coerce_valid_log_level(log_level):
    '''Convert a log level into an integer for consumption by the low-level Python logging API.'''
    if isinstance(log_level, int):
        return log_level
    check.str_param(log_level, 'log_level')
    check.invariant(
        log_level.lower() in PYTHON_LOGGING_LEVELS_NAMES,
        'Bad value for log level {level}: permissible values are {levels}.'.format(
            level=log_level,
            levels=', '.join(['\'{level_name}\'' for level_name in PYTHON_LOGGING_LEVELS_NAMES]),
        ),
    )
    log_level = PYTHON_LOGGING_LEVELS_ALIASES.get(log_level.upper(), log_level.upper())
    return PYTHON_LOGGING_LEVELS_MAPPING[log_level]


class DagsterLogManager(namedtuple('_DagsterLogManager', 'run_id logging_tags loggers')):
    '''Centralized dispatch for logging through the execution context.

    Handles the construction of uniform structured log messages and passes through to the underlying
    loggers.

    An instance of the log manager is made available to solids as context.log.

    The log manager supports standard convenience methods like those built into the Python logging
    library (i.e., ``DagsterLogManager.{debug, info, warning, error, critical}``, expects
    corresponding methods to be defined on the loggers passed to its constructor, and will delegate
    to those methods on each logger.

    The underlying integer API can also be called directly using, e.g.,
    ``DagsterLogManager.log(5, msg)``, and the log manager will delegate to the `log` method defined
    on each of the loggers it manages.

    User-defined custom log levels are not supported, and calls to, e.g.,
    ``DagsterLogManager.trace()`` or ``DagsterLogManager.notice`` will result in hard exceptions at
    runtime.

    Args:
        run_id (str): The run_id.
        tags (dict): Tags for the run
        loggers (List[logging.Logger]): Loggers to invoke.
    '''

    def __new__(cls, run_id, logging_tags, loggers):
        return super(DagsterLogManager, cls).__new__(
            cls,
            run_id=check.str_param(run_id, 'run_id'),
            logging_tags=check.dict_param(logging_tags, 'logging_tags'),
            loggers=check.list_param(loggers, 'loggers', of_type=logging.Logger),
        )

    def _prepare_message(self, orig_message, message_props):
        check.str_param(orig_message, 'orig_message')
        check.dict_param(message_props, 'message_props')

        # These are todos to further align with the Python logging API
        check.invariant(
            'extra' not in message_props, 'do not allow until explicit support is handled'
        )
        check.invariant(
            'exc_info' not in message_props, 'do not allow until explicit support is handled'
        )

        # Reserved keys in the message_props -- these are system generated.
        check.invariant('orig_message' not in message_props, 'orig_message reserved value')
        check.invariant('message' not in message_props, 'message reserved value')
        check.invariant('log_message_id' not in message_props, 'log_message_id reserved value')
        check.invariant('log_timestamp' not in message_props, 'log_timestamp reserved value')

        log_message_id = str(uuid.uuid4())

        log_timestamp = datetime.datetime.utcnow().isoformat()

        synth_props = {
            'orig_message': orig_message,
            'log_message_id': log_message_id,
            'log_timestamp': log_timestamp,
            'run_id': self.run_id,
        }

        # We first generate all props for the purpose of producing the semi-structured
        # log message via _kv_messsage
        all_props = dict(
            itertools.chain(synth_props.items(), self.logging_tags.items(), message_props.items())
        )

        # So here we use the arbitrary key DAGSTER_META_KEY to store a dictionary of
        # all the meta information that dagster injects into log message.
        # The python logging module, in its infinite wisdom, actually takes all the
        # keys in extra and unconditionally smashes them into the internal dictionary
        # of the logging.LogRecord class. We used a reserved key here to avoid naming
        # collisions with internal variables of the LogRecord class.
        # See __init__.py:363 (makeLogRecord) in the python 3.6 logging module source
        # for the gory details.
        return (_kv_message(all_props.items()), {DAGSTER_META_KEY: all_props})

    def _log(self, level, orig_message, message_props):
        '''Actually invoke the underlying loggers for a given log level.

        Args:
            level (Union[str, int]): An integer represeting a Python logging level or one of the
                standard Python string representations of a loggging level.
            orig_message (str): The log message generated in user code.
            message_props (dict): Additional properties for the structured log message.
        '''
        if not self.loggers:
            return

        level = coerce_valid_log_level(level)

        message, extra = self._prepare_message(orig_message, message_props)

        for logger_ in self.loggers:
            logger_.log(level, message, extra=extra)

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
            msg (str): The message to log.

        Kwargs:
            Additional context values for only this log message.
        '''

        check.str_param(msg, 'msg')
        return self._log(logging.DEBUG, msg, kwargs)

    def info(self, msg, **kwargs):
        '''Log at INFO level

        See ``debug()``.

        Args:
            msg (str): The message to log.

        Kwargs:
            Additional context values for only this log message.
        '''

        check.str_param(msg, 'msg')
        return self._log(logging.INFO, msg, kwargs)

    def warning(self, msg, **kwargs):
        '''Log at WARNING level

        See ``debug()``.

        Args:
            msg (str): The message to log.

        Kwargs:
            Additional context values for only this log message.
        '''

        check.str_param(msg, 'msg')
        return self._log(logging.WARNING, msg, kwargs)

    # Define the alias .warn()
    warn = warning

    def error(self, msg, **kwargs):
        '''Log at ERROR level

        See ``debug()``.

        Args:
            msg (str): The message to log.

        Kwargs:
            Additional context values for only this log message.
        '''

        check.str_param(msg, 'msg')
        return self._log(logging.ERROR, msg, kwargs)

    def critical(self, msg, **kwargs):
        '''Log at CRITICAL level

        See ``debug()``.

        Args:
            msg (str): The message to log.

        Kwargs:
            Additional context values for only this log message.
        '''

        check.str_param(msg, 'msg')
        return self._log(logging.CRITICAL, msg, kwargs)

    # Define the alias .fatal()
    fatal = critical
