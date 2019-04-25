import datetime
import itertools
import logging
import uuid

from dagster import check, seven

DAGSTER_META_KEY = 'dagster_meta'
DAGSTER_DEFAULT_LOGGER = 'dagster'


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


class DagsterLogManager:
    '''Centralized dispatch for logging through the execution context.

    Handles the construction of uniform structured log messages and passes through to the underlying
    loggers.

    An instance of the log manager is made available to solids as context.log.

    In an attempt to support the range of Python logging possibilities, the log manager can be
    invoked in two ways:

        1. Using the standard convenience methods built into the Python logging library:
           ``context.log.{debug, info, warning, error, critical}``
        2. Using the underlying integer API directly by calling, e.g., ``context.log.log(5, msg)``.
    '''

    def __init__(self, run_id, logging_tags, loggers):
        self.run_id = check.str_param(run_id, 'run_id')
        self.logging_tags = check.dict_param(logging_tags, 'logging_tags')
        self.loggers = check.list_param(loggers, 'loggers', of_type=logging.Logger)

    def _log(self, level, orig_message, message_props):
        '''Actually invoke the underlying loggers.

        Args:
            level (Union[str, int]): A built=in logging level name, a level name as registered using
                logging.addLevelName, or an integer logging level.
            orig_message (str): The log message generated in user code.
            message_props (dict): Additional properties for the structured log message.
        '''
        # It's conceivable that we might want DagsterLogManager to enforce that it be initialized
        # with at least one logger
        if not self.loggers:
            return

        check.int_param(level, 'level')
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

        for logger in self.loggers:
            logger.log(level, _kv_message(all_props.items()), extra={DAGSTER_META_KEY: all_props})

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
        return self._log(logging.DEBUG, msg, kwargs)

    def info(self, msg, **kwargs):
        '''Log at INFO level

        See ``debug()``.

        Args:
            msg (str): The message to log.

        Kwargs:
            Additional context values for only this log message.
        '''
        return self._log(logging.INFO, msg, kwargs)

    def warning(self, msg, **kwargs):
        '''Log at WARNING level

        See ``debug()``.

        Args:
            msg (str): The message to log.

        Kwargs:
            Additional context values for only this log message.
        '''
        return self._log(logging.WARNING, msg, kwargs)

    def error(self, msg, **kwargs):
        '''Log at ERROR level

        See ``debug()``.

        Args:
            msg (str): The message to log.

        Kwargs:
            Additional context values for only this log message.
        '''
        return self._log(logging.ERROR, msg, kwargs)

    def critical(self, msg, **kwargs):
        '''Log at CRITICAL level

        See ``debug()``.

        Args:
            msg (str): The message to log.

        Kwargs:
            Additional context values for only this log message.
        '''
        return self._log(logging.CRITICAL, msg, kwargs)

    def log(self, level, msg, **kwargs):
        '''Log at the integer level ``level``.

        See ``debug()``.

        Args:
            lvl (int): An integer logging level.
            msg (str): The message to log.
        
        Kwargs:
            Additional context values for only this log message.
        '''
        check.int_param(level, 'level')
        return self._log(level, msg, kwargs)
