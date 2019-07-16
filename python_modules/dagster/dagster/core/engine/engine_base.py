import abc
import six


class IEngine(six.with_metaclass(abc.ABCMeta)):  # pylint: disable=no-init
    @staticmethod
    @abc.abstractmethod
    def execute(pipeline_context, execution_plan, step_keys_to_execute=None):
        '''Core execution method.'''
