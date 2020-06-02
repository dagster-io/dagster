from abc import ABCMeta, abstractmethod

import six

from dagster import check


class ExecutablePipeline(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def get_definition(self):
        pass

    @abstractmethod
    def subset_for_execution(self, solid_subset):
        pass


class InMemoryExecutablePipeline(ExecutablePipeline, object):
    def __init__(self, pipeline_def):
        self._pipeline_def = pipeline_def

    def get_definition(self):
        return self._pipeline_def

    def subset_for_execution(self, solid_subset):
        check.list_param(solid_subset, 'solid_subset', of_type=str)

        if self._pipeline_def.is_subset_pipeline:
            return InMemoryExecutablePipeline(
                self._pipeline_def.parent_pipeline_def.get_pipeline_subset_def(solid_subset)
            )

        return InMemoryExecutablePipeline(self._pipeline_def.get_pipeline_subset_def(solid_subset))
