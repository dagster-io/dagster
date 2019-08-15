import logging
from abc import ABCMeta, abstractmethod

import six


class _EventSinkLogHandler(logging.Handler):
    def __init__(self, sink):
        self.sink = sink
        super(_EventSinkLogHandler, self).__init__()

    def emit(self, record):
        try:
            self.sink.handle_record(record)

        # preserving existing behavior here - but i think the right thing to do
        # depends on what the EventSink is being used for, likely need an is_critical
        # flag or something
        except Exception as e:  # pylint: disable=W0703
            logging.critical('Error during logging!')
            logging.exception(str(e))


class EventSink(six.with_metaclass(ABCMeta)):
    '''
    EventSinks are used to to capture the events that are produced during a dagster run.
    '''

    @abstractmethod
    def on_log_record(self, record):
        pass

    @abstractmethod
    def on_pipeline_init(self):
        pass

    @abstractmethod
    def on_pipeline_teardown(self):
        pass

    def get_logger(self):
        logger = logging.Logger('__event_sink')
        logger.addHandler(_EventSinkLogHandler(self))
        logger.setLevel(10)
        return logger

    def handle_record(self, record):
        self.on_log_record(record)
