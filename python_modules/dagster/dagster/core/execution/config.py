import multiprocessing
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import namedtuple

import six

from dagster import check
from dagster.core.execution.retries import Retries
from dagster.core.utils import make_new_run_id
from dagster.utils import merge_dicts


class IRunConfig(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    '''
    Interface for a container for RunConfig-like (e.g. RunConfig and PipelineRun) properties.
    Implementation should be left to the respective `namedtuple` superclass.
    '''

    @abstractproperty
    def run_id(self):
        pass

    @abstractproperty
    def tags(self):
        pass

    @abstractproperty
    def step_keys_to_execute(self):
        pass

    @abstractproperty
    def mode(self):
        pass

    @abstractproperty
    def previous_run_id(self):
        pass


class RunConfig(
    namedtuple('_RunConfig', 'run_id tags step_keys_to_execute mode previous_run_id'), IRunConfig,
):
    '''Configuration for pipeline execution.

    Args:
        run_id (Optional[str]): The ID to use for this run. If not provided a new UUID will
            be created (using :py:func:`python:uuid4.uuid4`).
        tags (Optional[dict[str, str]]): Key value pairs that will be added to logs.
        step_keys_to_execute (Optional[list[str]]): The subset of steps from a pipeline to execute
            this run.
        mode (Optional[str]): The name of the mode in which to execute the pipeline.
        previous_run_id (Optional[str]): A previous run id to perform re-execution of.
    '''

    def __new__(
        cls, run_id=None, tags=None, step_keys_to_execute=None, mode=None, previous_run_id=None,
    ):

        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        tags = check.opt_dict_param(tags, 'tags', key_type=str)

        return super(RunConfig, cls).__new__(
            cls,
            run_id=check.str_param(run_id, 'run_id') if run_id else make_new_run_id(),
            tags=tags,
            step_keys_to_execute=step_keys_to_execute,
            mode=check.opt_str_param(mode, 'mode'),
            previous_run_id=check.opt_str_param(previous_run_id, 'previous_run_id'),
        )

    def with_tags(self, **new_tags):
        '''Extend an existing RunConfig with additional logging tags.

        Args:
            **new_tags: Values should be strings. The logging tags to add.

        Returns:
            RunConfig: The extended RunConfig.
        '''
        new_tags = merge_dicts(self.tags, new_tags)
        return RunConfig(**merge_dicts(self._asdict(), {'tags': new_tags}))

    def with_mode(self, mode):
        '''Extend an existing RunConfig with a different mode.

        Args:
            mode (str): The new mode to use.

        Returns:
            RunConfig: The extended RunConfig.
        '''
        return RunConfig(**merge_dicts(self._asdict(), {'mode': mode}))

    def with_step_keys_to_execute(self, step_keys_to_execute):
        '''Extend an existing run config with different step keys to execute.

        Args:
            step_keys_to_execute (List[str]): The step keys to execute.

        Returns:
            RunConfig: The extended RunConfig.
        '''
        return RunConfig(
            **merge_dicts(self._asdict(), {'step_keys_to_execute': step_keys_to_execute})
        )


class ExecutorConfig(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def get_engine(self):
        '''Get the configured engine.

        Returns:
            Engine: The configured engine.'''


class InProcessExecutorConfig(ExecutorConfig):
    def __init__(self, retries, marker_to_close):
        self.retries = check.inst_param(retries, 'retries', Retries)
        self.marker_to_close = check.opt_str_param(marker_to_close, 'marker_to_close')

    def get_engine(self):
        from dagster.core.engine.engine_inprocess import InProcessEngine

        return InProcessEngine


class MultiprocessExecutorConfig(ExecutorConfig):
    def __init__(self, handle, retries, max_concurrent=None):
        from dagster import ExecutionTargetHandle

        self._handle = check.inst_param(handle, 'handle', ExecutionTargetHandle,)
        self.retries = check.inst_param(retries, 'retries', Retries)
        max_concurrent = max_concurrent if max_concurrent else multiprocessing.cpu_count()
        self.max_concurrent = check.int_param(max_concurrent, 'max_concurrent')

    def load_pipeline(self, pipeline_run):
        from dagster.core.storage.pipeline_run import PipelineRun

        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

        return self._handle.get_pipeline_for_run(pipeline_run)

    def get_engine(self):
        from dagster.core.engine.engine_multiprocess import MultiprocessEngine

        return MultiprocessEngine
