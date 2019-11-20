from abc import ABCMeta, abstractmethod

import six


class RunLauncher(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def launch_run(self, run):
        pass
