from abc import ABCMeta, abstractmethod
from collections import defaultdict

import gevent.lock
import pyrsistent
import six

from dagster import check
from dagster.core.errors import DagsterError
from dagster.core.events.log import EventRecord
from dagster.core.execution.stats import build_stats_from_events


class EventLogInvalidForRun(DagsterError):
    def __init__(self, *args, **kwargs):
        self.run_id = check.str_param(kwargs.pop('run_id'), 'run_id')
        super(EventLogInvalidForRun, self).__init__(*args, **kwargs)


class EventLogSequence(pyrsistent.CheckedPVector):
    __type__ = EventRecord


class EventLogStorage(six.with_metaclass(ABCMeta)):
    '''Abstract base class for storing structured event logs from pipeline runs.'''

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


class InMemoryEventLogStorage(EventLogStorage):
    def __init__(self):
        self._logs = defaultdict(EventLogSequence)
        self._lock = defaultdict(gevent.lock.Semaphore)
        self._handlers = defaultdict(set)

    def get_logs_for_run(self, run_id, cursor=-1):
        check.str_param(run_id, 'run_id')
        check.int_param(cursor, 'cursor')
        check.invariant(
            cursor >= -1,
            'Don\'t know what to do with negative cursor {cursor}'.format(cursor=cursor),
        )

        cursor = cursor + 1
        with self._lock[run_id]:
            return self._logs[run_id][cursor:]

    def store_event(self, event):
        check.inst_param(event, 'event', EventRecord)
        run_id = event.run_id
        with self._lock[run_id]:
            self._logs[run_id] = self._logs[run_id].append(event)
            for handler in self._handlers[run_id]:
                handler(event)

    def delete_events(self, run_id):
        with self._lock[run_id]:
            del self._logs[run_id]
        del self._lock[run_id]

    def wipe(self):
        self._logs = defaultdict(EventLogSequence)
        self._lock = defaultdict(gevent.lock.Semaphore)

    def watch(self, run_id, start_cursor, callback):
        with self._lock[run_id]:
            self._handlers[run_id].add(callback)

    def end_watch(self, run_id, handler):
        with self._lock[run_id]:
            if handler in self._handlers[run_id]:
                self._handlers[run_id].remove(handler)
