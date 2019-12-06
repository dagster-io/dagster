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

    @abstractmethod
    def serialize_to_file(self, value, write_path):
        '''Core Serialization Method'''

    @abstractmethod
    def deserialize_from_file(self, read_path):
        '''Core Deserialization Method'''


class PickleSerializationStrategy(SerializationStrategy):  # pylint: disable=no-init
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
