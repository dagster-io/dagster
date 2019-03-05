from abc import ABCMeta, abstractmethod
import pickle

import six

from dagster import check


@six.add_metaclass(ABCMeta)
class SerializationStrategy:
    @abstractmethod
    def serialize_value(self, step_context, value, write_file_obj):
        pass

    @abstractmethod
    def deserialize_value(self, step_context, read_file_obj):
        pass


class PickleSerializationStrategy(SerializationStrategy):
    def serialize_value(self, _step_context, value, write_file_obj):
        pickle.dump(value, write_file_obj)

    def deserialize_value(self, _step_context, read_file_obj):
        return pickle.load(read_file_obj)


@six.add_metaclass(ABCMeta)
class PersistenceStrategy:
    @abstractmethod
    def write_value(self, step_context, serialization_strategy, key, value):
        pass

    @abstractmethod
    def read_value(self, step_context, serialization_strategy, key):
        pass


class FilePersistencePolicy(PersistenceStrategy):
    def write_value(self, step_context, serialization_strategy, key, value):
        check.inst_param(serialization_strategy, 'serialization_strategy', SerializationStrategy)
        check.str_param(key, 'key')

        return serialize_to_file(step_context, serialization_strategy, value, key)

    def read_value(self, step_context, serialization_strategy, key):
        check.inst_param(serialization_strategy, 'serialization_strategy', SerializationStrategy)
        check.str_param(key, 'key')
        return deserialize_from_file(step_context, serialization_strategy, key)


def serialize_to_file(step_context, serialization_strategy, value, write_path):
    check.inst_param(serialization_strategy, 'serialization_strategy', SerializationStrategy)
    check.str_param(write_path, 'write_path')

    with open(write_path, 'wb') as write_obj:
        return serialization_strategy.serialize_value(step_context, value, write_obj)


def deserialize_from_file(step_context, serialization_strategy, read_path):
    check.inst_param(serialization_strategy, 'serialization_strategy', SerializationStrategy)
    check.str_param(read_path, 'read_path')

    with open(read_path, 'rb') as read_obj:
        return serialization_strategy.deserialize_value(step_context, read_obj)
