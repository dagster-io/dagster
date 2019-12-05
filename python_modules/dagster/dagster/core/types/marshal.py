import pickle
from abc import ABCMeta, abstractmethod

import six

from dagster import check
from dagster.utils import PICKLE_PROTOCOL


class SerializationStrategy(six.with_metaclass(ABCMeta)):
    def __init__(self, name, write_mode='wb', read_mode='rb'):
        self._name = name
        self._write_mode = write_mode
        self._read_mode = read_mode

    @property
    def name(self):
        return self._name

    @property
    def read_mode(self):
        return self._read_mode

    @property
    def write_mode(self):
        return self._write_mode


class BufferBasedSerializationStrategy(SerializationStrategy):  # pylint: disable=no-init
    '''This is the base class for serialization / deserialization of dagster objects. The primary
    use case is serialize to / from files, but any file-like objects (e.g. byte buffers) are
    supported.
    '''

    def __init__(self, name, **kwargs):
        SerializationStrategy.__init__(self, name, **kwargs)

    @abstractmethod
    def serialize_to_buffer(self, value, write_buffer_handle):
        '''Core buffer serialization method.'''

    @abstractmethod
    def deserialize_from_buffer(self, read_buffer_handle):
        '''Core buffer deserialization method'''


class FileBasedSerializationStrategy(SerializationStrategy):
    '''
    This is a shim used for serde protocols that require file paths. (E.G Keras save/load_model)
    '''

    def __init__(self, name='file', **kwargs):
        SerializationStrategy.__init__(self, name, **kwargs)

    @abstractmethod
    def serialize_to_file(self, value, write_file_path):
        pass

    @abstractmethod
    def deserialize_from_file(self, read_file_path):
        pass


class PickleSerializationStrategy(FileBasedSerializationStrategy):  # pylint: disable=no-init
    def __init__(self, name='pickle', **kwargs):
        super(PickleSerializationStrategy, self).__init__(name, **kwargs)

    def serialize_to_file(self, value, write_path):
        check.str_param(write_path, 'write_path')

        with open(write_path, self.write_mode) as write_obj:
            pickle.dump(value, write_obj, PICKLE_PROTOCOL)

    def deserialize_from_file(self, read_path):
        check.str_param(read_path, 'read_path')

        with open(read_path, self.read_mode) as read_obj:
            return pickle.load(read_obj)
