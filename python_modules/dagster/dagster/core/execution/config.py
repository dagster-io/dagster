import multiprocessing
import time
import logging
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import namedtuple

import six

from dagster import check
from dagster.core.utils import make_new_run_id
from dagster.utils import merge_dicts

EXECUTION_TIME_KEY = 'execution_epoch_time'


class RunConfig(
    namedtuple(
        '_RunConfig',
        'run_id tags event_callback log_sink reexecution_config step_keys_to_execute mode',
    )
):
    '''
    Configuration that controls the details of how Dagster will execute a pipeline.

    Args:
        run_id (Optional[str]): The ID to use for this run. If not provided a new UUID will
            be created using `uuid4`.
        tags (Optional[dict[str, str]]): Key value pairs that will be added to logs.
        event_callback (Optional[callable]): A callback to invoke with each :py:class:`EventRecord`
            produced during execution.
        log_sink (Optional[Logger]):
            An optionally provided logger used for handling logs outside of the single process executor.
        rexecution_config (Optional[RexecutionConfig]): Information about a previous run to allow
            for subset rexecution.
        step_keys_to_execute (Optional[list[str]]): The subset of steps from a pipeline to execute
            this run.
        mode (Optional[str]): The name of the mode in which to execute the pipeline.
    '''

    def __new__(
        cls,
        run_id=None,
        tags=None,
        event_callback=None,
        log_sink=None,
        reexecution_config=None,
        step_keys_to_execute=None,
        mode=None,
    ):
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        tags = check.opt_dict_param(tags, 'tags', key_type=str)

        if EXECUTION_TIME_KEY in tags:
            tags[EXECUTION_TIME_KEY] = float(tags[EXECUTION_TIME_KEY])
        else:
            tags[EXECUTION_TIME_KEY] = time.time()

        return super(RunConfig, cls).__new__(
            cls,
            run_id=check.str_param(run_id, 'run_id') if run_id else make_new_run_id(),
            tags=tags,
            event_callback=check.opt_callable_param(event_callback, 'event_callback'),
            log_sink=check.opt_inst_param(log_sink, 'log_sink', logging.Logger),
            reexecution_config=check.opt_inst_param(
                reexecution_config, 'reexecution_config', ReexecutionConfig
            ),
            step_keys_to_execute=step_keys_to_execute,
            mode=check.opt_str_param(mode, 'mode'),
        )

    def with_tags(self, **new_tags):
        new_tags = merge_dicts(self.tags, new_tags)
        return RunConfig(**merge_dicts(self._asdict(), {'tags': new_tags}))

    def with_log_sink(self, sink):
        return RunConfig(**merge_dicts(self._asdict(), {'log_sink': sink}))


class ExecutorConfig(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    _raise_on_error = True

    @property
    def raise_on_error(self):
        '''(bool): Whether errors encountered during execution should be reraised, or encapsulated
        in DagsterEvents.'''
        return self._raise_on_error

    @abstractproperty
    def requires_persistent_storage(self):
        '''(bool): Whether this executor config requires persistent storage to be configured.'''

    @abstractmethod
    def get_engine(self):
        '''(IEngine): Return the configured engine.'''


class InProcessExecutorConfig(ExecutorConfig):
    def __init__(self, raise_on_error=True):
        self._raise_on_error = check.opt_bool_param(raise_on_error, 'raise_on_error', default=True)

    @property
    def requires_persistent_storage(self):
        return False

    def get_engine(self):
        from dagster.core.engine.engine_inprocess import InProcessEngine

        return InProcessEngine


class MultiprocessExecutorConfig(ExecutorConfig):
    def __init__(self, handle, max_concurrent=None):
        from dagster import ExecutionTargetHandle

        # TODO: These gnomic process boundary/execution target handle exceptions should link to
        # a fuller explanation in the docs.
        # https://github.com/dagster-io/dagster/issues/1649
        self.handle = check.inst_param(
            handle,
            'handle',
            ExecutionTargetHandle,
            additional_message='Multiprocessing can only be configured when a pipeline is executed '
            'from an ExecutionTargetHandle: do not pass a pure in-memory pipeline definition.',
        )

        max_concurrent = max_concurrent if max_concurrent else multiprocessing.cpu_count()
        self.max_concurrent = check.int_param(max_concurrent, 'max_concurrent')
        self._raise_on_error = False

    @property
    def requires_persistent_storage(self):
        return True

    def get_engine(self):
        from dagster.core.engine.engine_multiprocess import MultiprocessEngine

        return MultiprocessEngine


class ReexecutionConfig:
    def __init__(self, previous_run_id, step_output_handles):
        self.previous_run_id = previous_run_id
        self.step_output_handles = step_output_handles
