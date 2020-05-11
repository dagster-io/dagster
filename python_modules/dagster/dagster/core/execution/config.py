import multiprocessing
from abc import ABCMeta, abstractmethod

import six

from dagster import check
from dagster.core.execution.retries import Retries


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

        self._handle = check.inst_param(handle, 'handle', ExecutionTargetHandle)
        self.retries = check.inst_param(retries, 'retries', Retries)
        max_concurrent = max_concurrent if max_concurrent else multiprocessing.cpu_count()
        self.max_concurrent = check.int_param(max_concurrent, 'max_concurrent')

    def load_pipeline(self, pipeline_run):
        from dagster.core.storage.pipeline_run import PipelineRun

        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

        return self._handle.build_pipeline_definition().subset_for_execution(
            pipeline_run.selector.solid_subset
        )

    def get_engine(self):
        from dagster.core.engine.engine_multiprocess import MultiprocessEngine

        return MultiprocessEngine
