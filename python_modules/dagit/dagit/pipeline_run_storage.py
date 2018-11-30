from enum import Enum
import logging
from rx import Observable
from dagster import check
from dagster.utils.logging import StructuredLoggerMessage
from dagster.core.events import (
    EventRecord,
    PipelineEventRecord,
)


class PipelineRunState(Enum):
    NOT_STARTED = 'NOT_STARTED'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'


import multiprocessing as mp


class PipelineRunStorage(object):
    def __init__(self):
        self._runs = {}
        self.add_run('foo', None)

    def _process_message(self, message):
        print(message, message.record_dagster_meta)

    def add_run(self, run_id, execution_params):
        check.invariant(run_id not in self._runs)

        self._runs[run_id] = PipelineRun(run_id, execution_params)
        # Temp, should subscribe to logging here
        self._runs[run_id].handle_new_event(
            PipelineEventRecord(
                StructuredLoggerMessage(
                    name="name",
                    message="msg",
                    level=50,
                    meta={'run_id': run_id},
                    record=logging.LogRecord(
                        name='n',
                        level=50,
                        pathname='p',
                        lineno=0,
                        msg='msg',
                        args=None,
                        exc_info=None
                    ),
                )
            )
        )
        self._runs[run_id].handle_new_event(
            PipelineEventRecord(
                StructuredLoggerMessage(
                    name="name2",
                    message="msg2",
                    level=50,
                    meta={'run_id': run_id},
                    record=logging.LogRecord(
                        name='n',
                        level=50,
                        pathname='p',
                        lineno=0,
                        msg='msg',
                        args=None,
                        exc_info=None
                    ),
                )
            )
        )

    def all_runs(self):
        return self._runs.keys()

    def get_run_by_id(self, id):
        return self._runs.get(id)

    def __getitem__(self, id):
        return self.get_run_by_id(id)


class PipelineRun(object):
    def __init__(self, run_id, execution_params):
        self._logs = []
        self._run_id = run_id
        self._status = PipelineRunState.NOT_STARTED
        self._subscribers = []
        self.execution_params = execution_params

    def logs_from(self, cursor):
        return self._logs[cursor:]

    def handle_new_event(self, new_event):
        check.inst_param(new_event, 'new_event', EventRecord)
        self._logs.append(new_event)
        for subscriber in self._subscribers:
            subscriber.handle_new_event(new_event)

    def subscribe(self, subscriber):
        self._subscribers.append(subscriber)

    def observable_after_cursor(self, cursor=None):
        return Observable.create( # pylint: disable=E1101
            PipelineRunObservableSubscribe(self, cursor),
        )


#
# TBD
# class CursorList(object):
#     def __init__(self, initial=None):
#         self._list = initial or []
#         self._start_cursor = 0
#         self._end_cursor = len(self._list)


class PipelineRunObservableSubscribe(object):
    def __init__(self, pipeline_run, start_cursor=None):
        self.pipeline_run = pipeline_run
        self.observer = None
        self.start_cursor = start_cursor or 0

    def __call__(self, observer):
        self.observer = observer
        for event in self.pipeline_run.logs_from(self.start_cursor):
            self.observer.on_next(event)
        self.pipeline_run.subscribe(self)

    def handle_new_event(self, event):
        check.inst_param(event, 'event', EventRecord)
        self.observer.on_next(event)
