from abc import ABCMeta, abstractmethod, abstractproperty

import six


class RepresentedPipeline(six.with_metaclass(ABCMeta)):
    @abstractproperty
    def config_schema_snapshot(self):
        pass

    @abstractmethod
    def get_mode_def_snap(self, mode_name):
        pass
