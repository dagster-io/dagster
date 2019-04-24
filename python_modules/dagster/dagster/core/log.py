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


def _kv_message(all_items, multiline=False):
    sep = '\n' if multiline else ' '
    format_str = '{key:>20} = {value}' if multiline else '{key}={value}'
    return sep + sep.join(
        [format_str.format(key=key, value=_dump_value(value)) for key, value in all_items]
    )


class DagsterLogManager:
    '''Centralized dispatch for logging through the execution context.
    
    Handles the construction of uniform structured log messages and passes through to the underlying
    loggers.

    An instance of the log manager is made available to solids as context.log.

    In an attempt to support the range of Python logging possibilities, the log manager can be invoked
    in three ways:

        1. Using standard convenience methods like those built in to the Python logging library:
           context.log.{debug, info, warning, error, critical}
        2. With any user-defined log level, like context.log.trace, or context.log.notice. Users are
           expected to register these levels with the Python logging library (using
           logging.addLevelName) when instantiating custom loggers.
        3. Using the underlying integer API directly by calling, e.g., context.log.log(5, msg).
    '''

    def __init__(self, run_id, tags, loggers):
        self.run_id = check.str_param(run_id, 'run_id')
        self.tags = check.dict_param(tags, 'tags')
        self.loggers = check.list_param(loggers, 'loggers', of_type=logging.Logger)

    def _log(self, level, orig_message, message_props):
        if not self.loggers:
            return

        check.str_param(level, 'level')
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
            itertools.chain(synth_props.items(), self.tags.items(), message_props.items())
        )

        msg_with_structured_props = _kv_message(all_props.items())
        msg_with_multiline_structured_props = _kv_message(all_props.items(), multiline=True)

        # So here we use the arbitrary key DAGSTER_META_KEY to store a dictionary of
        # all the meta information that dagster injects into log message.
        # The python logging module, in its infinite wisdom, actually takes all the
        # keys in extra and unconditionally smashes them into the internal dictionary
        # of the logging.LogRecord class. We used a reserved key here to avoid naming
        # collisions with internal variables of the LogRecord class.
        # See __init__.py:363 (makeLogRecord) in the python 3.6 logging module source
        # for the gory details.
        # getattr(self.logger, method)(
        #     message_with_structured_props, extra={DAGSTER_META_KEY: all_props}
        # )

        # HACK: getLevelName really doesn't do what it says on the box. This function was originally
        # intended to give the user-facing name of a given int log level, e.g.,
        # getLevelName(40) -> 'ERROR'. In fact, it also works the other way around (this was 'fixed'
        # in Python 3.4 then immediately reverted in 3.4.2). For levels it doesn't recognize,
        # including all ints that don't have a name registered with logging.addLevelName it does:
        # getLevelName('foo') -> 'Level foo'; getLevelName(3) -> 'Level 3' (!)
        # See: https://docs.python.org/3/library/logging.html#logging.getLevelName
        if isinstance(level, int):
            lvl = level
        else:
            lvl = logging.getLevelName(level.upper())

        if not isinstance(lvl, int):
            self.error(
                'Unexpected log level: User code attempted to log at level \'{level}\', but that '
                'level has not been registered with the Python logging library. Original message: '
                '\'{orig_message}\''.format(level=level, orig_message=orig_message),
                **message_props
            )
            return

        for logger in self.loggers:
            if hasattr(logger, level):
                logger_method = check.is_callable(getattr(logger, level))
                if logger.name == DAGSTER_DEFAULT_LOGGER:
                    logger_method(
                        msg_with_multiline_structured_props, extra={DAGSTER_META_KEY: all_props}
                    )
                else:
                    logger_method(msg_with_structured_props, extra={DAGSTER_META_KEY: all_props})

            else:
                if logger.name == DAGSTER_DEFAULT_LOGGER:
                    logger.log(
                        lvl,
                        msg_with_multiline_structured_props,
                        extra={DAGSTER_META_KEY: all_props},
                    )
                else:
                    logger.log(lvl, msg_with_structured_props, extra={DAGSTER_META_KEY: all_props})

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

    def log(lvl, self, msg, **kwargs):
        pass

    def __getattr__(self, name):
        def handler(msg, **kwargs):
            return self._log(name, msg, kwargs)

        return handler
