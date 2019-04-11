from abc import ABCMeta, abstractmethod
import pickle

import six

from dagster import check


class SerializationStrategy(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def serialize_value(self, context, value, write_file_obj):
        pass

    @abstractmethod
    def deserialize_value(self, context, read_file_obj):
        pass


class PickleSerializationStrategy(SerializationStrategy):  # pylint: disable=no-init
    def serialize_value(self, _context, value, write_file_obj):
        pickle.dump(value, write_file_obj)

    def deserialize_value(self, _context, read_file_obj):
        return pickle.load(read_file_obj)


def serialize_to_file(context, serialization_strategy, value, write_path):
    check.inst_param(serialization_strategy, 'serialization_strategy', SerializationStrategy)
    check.str_param(write_path, 'write_path')

    with open(write_path, 'wb') as write_obj:
        return serialization_strategy.serialize_value(context, value, write_obj)


def deserialize_from_file(context, serialization_strategy, read_path):
    check.inst_param(serialization_strategy, 'serialization_strategy', SerializationStrategy)
    check.str_param(read_path, 'read_path')

    with open(read_path, 'rb') as read_obj:
        return serialization_strategy.deserialize_value(context, read_obj)
