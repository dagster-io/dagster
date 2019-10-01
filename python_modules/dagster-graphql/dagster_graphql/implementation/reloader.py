import abc

import six


class Reloader(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def is_reload_supported(self):
        '''Return true if the reload() method will restart the dagit process.

        Returns:
            bool: Yes or no
        '''

    @abc.abstractmethod
    def reload(self):
        '''Terminate and re-launch the dagit process.
        '''
