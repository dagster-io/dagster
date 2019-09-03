import weakref
from collections import namedtuple
from enum import Enum

from rx import Observable

from dagster import check
from dagster.core.events import DagsterEventType


class PipelineRunStatus(Enum):
    NOT_STARTED = 'NOT_STARTED'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'


class PipelineRunData(
    namedtuple(
        '_PipelineRunData',
        (
            'pipeline_name run_id environment_dict mode selector reexecution_config '
            'step_keys_to_execute status'
        ),
    )
):
    @staticmethod
    def create_empty_run(pipeline_name, run_id):
        from dagster.core.execution.api import ExecutionSelector

        return PipelineRunData(
            pipeline_name=pipeline_name,
            run_id=run_id,
            environment_dict=None,
            mode=None,
            selector=ExecutionSelector(pipeline_name),
            reexecution_config=None,
            step_keys_to_execute=None,
            status=PipelineRunStatus.NOT_STARTED,
        )

    def __new__(
        cls,
        pipeline_name,
        run_id,
        environment_dict,
        mode,
        selector,
        reexecution_config,
        step_keys_to_execute,
        status,
    ):
        from dagster.core.execution.api import ExecutionSelector
        from dagster.core.execution.config import ReexecutionConfig

        return super(PipelineRunData, cls).__new__(
            cls,
            pipeline_name=check.str_param(pipeline_name, 'pipeline_name'),
            run_id=check.str_param(run_id, 'run_id'),
            environment_dict=check.opt_dict_param(
                environment_dict, 'environment_dict', key_type=str
            ),
            mode=check.opt_str_param(mode, 'mode'),
            selector=check.inst_param(selector, 'selector', ExecutionSelector),
            reexecution_config=check.opt_inst_param(
                reexecution_config, 'reexecution_config', ReexecutionConfig
            ),
            step_keys_to_execute=None
            if step_keys_to_execute is None
            else check.list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str),
            status=status,
        )

    def run_with_status(self, status):
        return PipelineRunData(
            pipeline_name=self.pipeline_name,
            run_id=self.run_id,
            environment_dict=self.environment_dict,
            mode=self.mode,
            selector=self.selector,
            reexecution_config=self.reexecution_config,
            step_keys_to_execute=self.step_keys_to_execute,
            status=status,
        )


class PipelineRun(object):
    def __init__(self, pipeline_run_data, run_storage=None):
        from .runs import RunStorage

        self._pipeline_run_data = pipeline_run_data

        run_storage = check.opt_inst_param(run_storage, 'run_storage', RunStorage)
        if run_storage:
            self._run_storage = weakref.proxy(run_storage)
        else:
            self._run_storage = None

        self.__subscribers = []

    @property
    def mode(self):
        return self._pipeline_run_data.mode

    @property
    def run_id(self):
        return self._pipeline_run_data.run_id

    @property
    def status(self):
        return self._pipeline_run_data.status

    @property
    def is_persistent(self):
        return False

    @property
    def pipeline_name(self):
        return self._pipeline_run_data.pipeline_name

    @property
    def environment_dict(self):
        return self._pipeline_run_data.environment_dict

    def logs_after(self, cursor):
        return self._run_storage.event_log_storage.get_logs_for_run(self.run_id, cursor=cursor)

    def all_logs(self):
        return self._run_storage.event_log_storage.get_logs_for_run(self.run_id)

    def logs_ready(self):
        return self._run_storage.event_log_storage.logs_ready(self.run_id)

    def watch_event_logs(self, cursor, cb):
        return self._run_storage.event_log_storage.watch(self.run_id, cursor, cb)

    @property
    def selector(self):
        return self._pipeline_run_data.selector

    @property
    def reexecution_config(self):
        return self._pipeline_run_data.reexecution_config

    @property
    def step_keys_to_execute(self):
        return self._pipeline_run_data.step_keys_to_execute

    def handle_new_event(self, new_event):
        from dagster.core.events.log import EventRecord

        check.inst_param(new_event, 'new_event', EventRecord)

        if new_event.is_dagster_event:
            event = new_event.dagster_event
            if event.event_type == DagsterEventType.PIPELINE_START:
                self._pipeline_run_data = self._pipeline_run_data.run_with_status(
                    PipelineRunStatus.STARTED
                )
            elif event.event_type == DagsterEventType.PIPELINE_SUCCESS:
                self._pipeline_run_data = self._pipeline_run_data.run_with_status(
                    PipelineRunStatus.SUCCESS
                )
            elif event.event_type == DagsterEventType.PIPELINE_FAILURE:
                self._pipeline_run_data = self._pipeline_run_data.run_with_status(
                    PipelineRunStatus.FAILURE
                )

        for subscriber in self.__subscribers:
            subscriber.handle_new_event(new_event)

        return self._pipeline_run_data.status

    def subscribe(self, subscriber):
        self.__subscribers.append(subscriber)

    def observable_after_cursor(self, observable_cls=None, cursor=None):
        check.type_param(observable_cls, 'observable_cls')
        return Observable.create(observable_cls(self, cursor))  # pylint: disable=E1101

    @staticmethod
    def from_json(json_data, run_storage):
        from dagster.core.execution.api import ExecutionSelector
        from .runs import RunStorage

        check.dict_param(json_data, 'json_data')
        check.inst_param(run_storage, 'run_storage', RunStorage)

        selector = ExecutionSelector(
            name=json_data['pipeline_name'], solid_subset=json_data.get('pipeline_solid_subset')
        )
        run = PipelineRun(
            run_storage=run_storage,
            pipeline_run_data=PipelineRunData(
                pipeline_name=json_data['pipeline_name'],
                run_id=json_data['run_id'],
                selector=selector,
                environment_dict=json_data['environment_dict'],
                mode=json_data['mode'],
                # the properties below are not modeled in persistence right now
                reexecution_config=None,
                step_keys_to_execute=None,
                status=PipelineRunStatus.NOT_STARTED,
            ),
        )

        if not run.logs_ready():
            run.watch_event_logs(0, run.handle_new_event)
            return run

        init_logs = run.all_logs()
        for log in init_logs:
            run.handle_new_event(log)

        if run.status != PipelineRunStatus.SUCCESS:
            run.watch_event_logs(len(init_logs), run.handle_new_event)

        return run
