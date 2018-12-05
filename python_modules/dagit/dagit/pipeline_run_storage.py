from collections import OrderedDict
from enum import Enum
import logging
from rx import Observable
from dagster import check
from dagster.utils.logging import StructuredLoggerMessage
from dagster.core.events import (
    EventRecord,
    PipelineEventRecord,
    EventType,
)


class PipelineRunStatus(Enum):
    NOT_STARTED = 'NOT_STARTED'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'


class PipelineRunStorage(object):
    def __init__(self):
        self._runs = OrderedDict()

    def add_run(self, run_id, pipeline_name, config, execution_plan):
        check.invariant(run_id not in self._runs)
        run = PipelineRun(run_id, pipeline_name, config, execution_plan)
        self._runs[run_id] = run
        return run

    def all_runs(self):
        return self._runs.values()

    def all_runs_for_pipeline(self, pipeline_name):
        return [r for r in self.all_runs() if r.pipeline_name == pipeline_name]

    def get_run_by_id(self, id_):
        return self._runs.get(id_)

    def __getitem__(self, id_):
        return self.get_run_by_id(id_)


class PipelineRun(object):
    def __init__(self, run_id, pipeline_name, config, execution_plan):
        self._logs = []
        self._run_id = run_id
        self._status = PipelineRunStatus.NOT_STARTED
        self._subscribers = []
        self.pipeline_name = pipeline_name
        self.config = config
        self.execution_plan = execution_plan

    def logs_after(self, cursor):
        cursor = int(cursor) + 1
        return self._logs[cursor:]

    def all_logs(self):
        return self._logs

    def handle_new_event(self, new_event):
        check.inst_param(new_event, 'new_event', EventRecord)

        if new_event.event_type == EventType.PIPELINE_START:
            self._status = PipelineRunStatus.STARTED
        elif new_event.event_type == EventType.PIPELINE_SUCCESS:
            self._status = PipelineRunStatus.SUCCESS
        elif new_event.event_type == EventType.PIPELINE_FAILURE:
            self._status = PipelineRunStatus.FAILURE

        self._logs.append(new_event)
        for subscriber in self._subscribers:
            subscriber.handle_new_event(new_event)

    @property
    def run_id(self):
        return self._run_id

    @property
    def status(self):
        return self._status

    def subscribe(self, subscriber):
        self._subscribers.append(subscriber)

    def observable_after_cursor(self, cursor=None):
        return Observable.create( # pylint: disable=E1101
            PipelineRunObservableSubscribe(self, cursor),
        )


class PipelineRunObservableSubscribe(object):
    def __init__(self, pipeline_run, start_cursor=None):
        self.pipeline_run = pipeline_run
        self.observer = None
        self.start_cursor = start_cursor or 0

    def __call__(self, observer):
        self.observer = observer
        for event in self.pipeline_run.logs_after(self.start_cursor):
            self.observer.on_next(event)
        self.pipeline_run.subscribe(self)

    def handle_new_event(self, event):
        check.inst_param(event, 'event', EventRecord)
        self.observer.on_next(event)
