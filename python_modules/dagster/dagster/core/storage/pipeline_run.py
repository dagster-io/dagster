import weakref
from enum import Enum

from rx import Observable

from dagster import check
from dagster.core.events import DagsterEventType


class PipelineRunStatus(Enum):
    NOT_STARTED = 'NOT_STARTED'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'


class PipelineRun(object):
    __slots__ = [
        '_run_storage',
        '_pipeline_name',
        '_run_id',
        '_env_config',
        '_mode',
        '_selector',
        '_reexecution_config',
        '_step_keys_to_execute',
        '__subscribers',
        '_status',
    ]

    def __init__(
        self,
        run_storage=None,
        pipeline_name=None,
        run_id=None,
        env_config=None,
        mode=None,
        selector=None,
        reexecution_config=None,
        step_keys_to_execute=None,
    ):
        from dagster.core.execution.api import ExecutionSelector
        from dagster.core.execution.config import ReexecutionConfig
        from .runs import RunStorage

        self._pipeline_name = check.str_param(pipeline_name, 'pipeline_name')
        self._run_id = check.str_param(run_id, 'run_id')
        self._env_config = check.opt_dict_param(env_config, 'environment_config', key_type=str)
        self._mode = check.opt_str_param(mode, 'mode')
        self._selector = check.opt_inst_param(
            selector,
            'selector',
            ExecutionSelector,
            default=ExecutionSelector(name=self.pipeline_name),
        )
        self._reexecution_config = check.opt_inst_param(
            reexecution_config, 'reexecution_config', ReexecutionConfig
        )
        if step_keys_to_execute is not None:
            self._step_keys_to_execute = check.list_param(
                step_keys_to_execute, 'step_keys_to_execute', of_type=str
            )
        else:
            self._step_keys_to_execute = None

        run_storage = check.opt_inst_param(run_storage, 'run_storage', RunStorage)
        if run_storage:
            self._run_storage = weakref.proxy(run_storage)
        else:
            self._run_storage = None

        self.__subscribers = []

        self._status = PipelineRunStatus.NOT_STARTED

    @property
    def mode(self):
        return self._mode

    @property
    def run_id(self):
        return self._run_id

    @property
    def status(self):
        return self._status

    @property
    def is_persistent(self):
        return False

    @property
    def pipeline_name(self):
        return self._pipeline_name

    @property
    def config(self):
        return self._env_config

    def logs_after(self, cursor):
        return self._run_storage.event_log_storage.get_logs_for_run(self.run_id, cursor=cursor)

    def all_logs(self):
        return self._run_storage.event_log_storage.get_logs_for_run(self.run_id)

    @property
    def selector(self):
        return self._selector

    @property
    def reexecution_config(self):
        return self._reexecution_config

    @property
    def step_keys_to_execute(self):
        return self._step_keys_to_execute

    def handle_new_event(self, new_event):
        from dagster.core.events.log import EventRecord

        check.inst_param(new_event, 'new_event', EventRecord)

        if new_event.is_dagster_event:
            event = new_event.dagster_event
            if event.event_type == DagsterEventType.PIPELINE_START:
                self._status = PipelineRunStatus.STARTED
            elif event.event_type == DagsterEventType.PIPELINE_SUCCESS:
                self._status = PipelineRunStatus.SUCCESS
            elif event.event_type == DagsterEventType.PIPELINE_FAILURE:
                self._status = PipelineRunStatus.FAILURE

        for subscriber in self.__subscribers:
            subscriber.handle_new_event(new_event)

    def subscribe(self, subscriber):
        self.__subscribers.append(subscriber)

    def observable_after_cursor(self, observable_cls=None, cursor=None):
        check.type_param(observable_cls, 'observable_cls')
        return Observable.create(observable_cls(self, cursor))  # pylint: disable=E1101
