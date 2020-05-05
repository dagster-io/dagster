from abc import ABCMeta, abstractmethod

import six


class ExecutablePipeline(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def get_definition(self):
        pass

    @abstractmethod
    def build_sub_pipeline(self, solid_subset):
        pass


class InMemoryExecutablePipeline(ExecutablePipeline, object):
    def __init__(self, pipeline_def):
        self._pipeline_def = pipeline_def

    def get_definition(self):
        return self._pipeline_def

    def build_sub_pipeline(self, solid_subset):
        return InMemoryExecutablePipeline(self._pipeline_def.build_sub_pipeline(solid_subset))
