from abc import ABCMeta, abstractmethod, abstractproperty

import pyrsistent
import six

from dagster import check
from dagster.core.errors import DagsterError
from dagster.core.events.log import EventRecord
from dagster.core.execution.stats import build_stats_from_events


class DagsterEventLogInvalidForRun(DagsterError):
    def __init__(self, *args, **kwargs):
        self.run_id = check.str_param(kwargs.pop('run_id', None), 'run_id')
        super(DagsterEventLogInvalidForRun, self).__init__(*args, **kwargs)


class EventLogSequence(pyrsistent.CheckedPVector):
    __type__ = EventRecord


class EventLogStorage(six.with_metaclass(ABCMeta)):
    '''Abstract base class for storing structured event logs from pipeline runs.
    
    Note that event log storages using SQL databases as backing stores should implement
    :py:class:`~dagster.core.storage.event_log.SqlEventLogStorage`.

    Users should not directly instantiate concrete subclasses of this class; they are instantiated
    by internal machinery when ``dagit`` and ``dagster-graphql`` load, based on the values in the
    ``dagster.yaml`` file in ``$DAGSTER_HOME``. Configuration of concrete subclasses of this class
    should be done by setting values in that file.    
    '''

    @abstractmethod
    def get_logs_for_run(self, run_id, cursor=-1):
        '''Get all of the logs corresponding to a run.

        Args:
            run_id (str): The id of the run for which to fetch logs.
            cursor (Optional[int]): Zero-indexed logs will be returned starting from cursor + 1,
                i.e., if cursor is -1, all logs will be returned. (default: -1)
        '''

    def get_stats_for_run(self, run_id):
        '''Get a summary of events that have ocurred in a run.'''

        return build_stats_from_events(run_id, self.get_logs_for_run(run_id))

    @abstractmethod
    def store_event(self, event):
        '''Store an event corresponding to a pipeline run.

        Args:
            run_id (str): The id of the run that generated the event.
            event (EventRecord): The event to store.
        '''

    @abstractmethod
    def delete_events(self, run_id):
        '''Remove events for a given run id'''

    @abstractmethod
    def wipe(self):
        '''Clear the log storage.'''

    @abstractmethod
    def watch(self, run_id, start_cursor, callback):
        '''Call this method to start watching.'''

    @abstractmethod
    def end_watch(self, run_id, handler):
        '''Call this method to stop watching.'''

    @abstractproperty
    def is_persistent(self):
        '''bool: Whether the storage is persistent.'''

    def dispose(self):
        '''Explicit lifecycle management.'''
